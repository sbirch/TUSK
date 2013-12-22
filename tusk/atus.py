from tusk import __path__
import dataset
import readline
import sqlparse
import sqlparse.sql as sql
import sqlparse.tokens as token
import traceback
import variables
import sys
import re
import os
import sqlalchemy
import sqlite3
import inspect

class ATUS:
	def __init__(self, db):
		self.db = db

		# TODO: this is an enormous SQLite-specific hack
		def _hook(dbapi_con, con_record):
			assert isinstance(dbapi_con, sqlite3.Connection)
			for obj in dir(variables):
				if obj.startswith('sql_'):
					f = getattr(variables, obj)
					# n.b. sql_ functions can only have normal style arguments,
					# no funny business.
					dbapi_con.create_function(obj[4:],
						len(inspect.getargspec(f).args), f)
				elif obj.startswith('SQL_'):
					f = getattr(variables, obj)
					dbapi_con.create_aggregate(obj[4:],
						len(inspect.getargspec(f.step).args)-1, f)
		sqlalchemy.event.listen(self.db.engine, 'connect', _hook)

	def _variable_rewriter(self, mv):
		table = ''
		if mv.count('.') == 1:
			table, mv = mv.split('.', 1)
			table = self._infer(table) + '.'
		mv = variables.rewrite(mv)
		return table + mv
	def _infer(self, table_ref):
		try:
			return variables.Tables[table_ref]
		except KeyError:
			return table_ref
	def rewrite(self, q, verbose=False):
		return rewrite(q, self._infer, self._variable_rewriter, verbose=verbose)
	def __getattr__(self, attr):
		return getattr(self.db, attr)
	def __getitem__(self, key):
		if not self.db.engine.has_table(key) and self.db.engine.has_table(self._infer(key)):
			key = self._infer(key)
		return self.db[key]
	def query_tuples(self, q):
		self.db.executable.execute(query, **kw)
	def query(self, q, explain=False, verbose=False):
		return self.db.query(('EXPLAIN ' if explain else '') + self.rewrite(q, verbose=verbose))
	def get(self, q, explain=False, verbose=False):
		results = list(self.query(q, explain=explain, verbose=verbose))
		assert len(results) == 1
		if len(results[0].keys()) == 1:
			return results[0][results[0].keys()[0]]
		return results[0]

def find(L, f):
	for i,l in enumerate(L):
		if f(l):
			return i
	return None

def rewrite(sql, table_translator, variable_rewriter, verbose=False):
	'''
	Rewrite a SQL statement with the given table translator and
	variable rewriter. Handles SELECT statements with arbitrary
	WHERE clauses.

	TODO(smb):
		error messaging
		SQL placeholders
	'''
	if verbose:
		print 'Rewriting:', re.sub('\s+', ' ', sql)
	# TODO(smb) only handles the first statement
	parsed = sqlparse.parse(sql)[0]
	if verbose:
		print 'Tokens:', list([x for x in parsed.flatten() if not x.is_whitespace()])
	new_tree = _rewrite_parse_tree(parsed, table_translator, variable_rewriter, verbose=verbose)
	new_query = new_tree.to_unicode()
	if verbose:
		print 'Rewritten:', re.sub('\s+', ' ', new_query)
	return new_query

def is_base_identifier(t):
	return isinstance(t, sql.Identifier) or t.ttype in [token.Keyword, token.Name]

def _rewrite_parse_tree(parsed, table_translator, variable_rewriter,
		context=None, d=0, verbose=False):
	dp = '  ' * d

	if isinstance(parsed, sql.Statement) and parsed.get_type() == 'SELECT':
		#print dp, 'SELECT case', repr(parsed)
		#print dp, 'Tokens:', parsed.tokens

		assert parsed.tokens[0].ttype == token.DML

		# find the position of the FROM keyword
		from_position = find(parsed.tokens,
			lambda x: x.ttype == token.Keyword and x.value.lower() == 'from')
		distinct_present = 0 if find(parsed.tokens,
			lambda x: x.ttype == token.Keyword and x.value.lower() == 'distinct') == None else 1

		# get the selected column tokens and rewrite them
		terms = [x for x in parsed.tokens[1 + distinct_present:from_position] if not x.is_whitespace()]
		if verbose:
			print dp, 'SELECT result columns:', terms
		assert len(terms) == 1
		terms = terms[0]
		parsed.tokens[parsed.tokens.index(terms)] = _rewrite_parse_tree(
			terms,
			table_translator,
			variable_rewriter,
			context='result-cols', d=d+1, verbose=verbose)

		end_join_source = find(parsed.tokens,
			lambda x: isinstance(x, sql.Where) or (x.ttype == token.Keyword and x.value.lower() in ['order', 'group', 'limit']))

		# replace the table name
		join_source = parsed.tokens[from_position+1:end_join_source]
		#print dp, 'Table ID:', join_source
		for table_id in join_source:
			if table_id.is_whitespace():
				continue

			if isinstance(table_id, sql.Function):
				respondent_link = table_id.value.startswith('respondent_link')
				case_link = table_id.value.startswith('case_link')
				if respondent_link or case_link:
					# TODO(smb) this is a very simple (fragile) parser
					arguments = table_id.value[table_id.value.index('(')+1:-1]
					arguments = [x.strip() for x in arguments.split(',')]
					tables = [table_translator(x) for x in arguments]

					table_conditions = [tables[0]]
					for i,table in enumerate(tables[1:]):
						cond = '%s on %s.TUCASEID=%s.TUCASEID' % (
								table, table, tables[i]
						)
						# TODO(smb) this hardcoded list of tables with line numbers
						# is a hack and doesn't account for any of the modules
						if respondent_link and arguments[i+1] in ['cps', 'roster', 'who', 'respondent']:
							cond += ' and %s.TULINENO=1' % table
						table_conditions.append(cond)

					statement = ' inner join '.join(table_conditions)

					parsed.tokens[parsed.tokens.index(table_id)] = sql.Parenthesis([
							sql.Token(sqlparse.tokens.Group.Parenthesis, '('),
							# TODO(smb): this is a total violation of the parse tree
							# but it serializes right
							sql.Identifier(statement),
							sql.Token(sqlparse.tokens.Group.Parenthesis, ')')
					])
					continue

			parsed.tokens[parsed.tokens.index(table_id)] = _rewrite_parse_tree(
				table_id,
				table_translator,
				variable_rewriter,
				context='table', d=d+1, verbose=verbose)
		
		#print dp, 'end_join_source:', end_join_source, repr(parsed.tokens[end_join_source if end_join_source is not None else -1])
		
		if end_join_source is not None:
			for i,tok in enumerate(parsed.tokens[end_join_source:]):
				if tok.is_whitespace():
					continue
				idx = i + end_join_source
				#print dp, i, idx, repr(parsed.tokens[idx])
				parsed.tokens[idx] = _rewrite_parse_tree(
					tok,
					table_translator,
					variable_rewriter,
					d=d+1, verbose=verbose)

		return parsed
	elif is_base_identifier(parsed):
		if verbose:
			print dp, 'base_identifier case context=%s %r/"%s"' % (context, parsed, parsed)
		if context == 'result-cols':
			rewritten = variable_rewriter(parsed.value)
			if parsed.value != rewritten:
				if verbose:
					print dp, 'Rewriting result-cols %s => %s' % (parsed.value, variable_rewriter(parsed.value))
				
				result_name = parsed.value.split('.')[-1]
				return sql.Identifier('%s AS %s' % (variable_rewriter(parsed.value), result_name))
			else:
				if verbose:
					print dp, 'Leaving %r be' % parsed
				return parsed
		elif context == 'table':
			if parsed.ttype == token.Keyword:
				return parsed
			if verbose:
				print dp, 'Rewriting %s => %s' % (parsed.value, table_translator(parsed.value))
			return sql.Identifier(table_translator(parsed.value))
		else:
			rewritten = variable_rewriter(parsed.value)
			if parsed.value != rewritten:
				if verbose:
					print dp, 'Rewriting %s => (%s)' % (parsed.value, variable_rewriter(parsed.value))

				if rewritten[0] == '(' and rewritten[-1] == ')':
					rewritten = rewritten[1:-1]
					return sql.Parenthesis([
							sql.Token(sqlparse.tokens.Group.Parenthesis, '('),
							sql.Identifier(rewritten),
							sql.Token(sqlparse.tokens.Group.Parenthesis, ')')
					])
				else:
					return sql.Identifier(rewritten)
			else:
				if verbose:
					print dp, 'Leaving %r be' % parsed
				return parsed
	elif isinstance(parsed, sql.TokenList):
		if verbose:
			print dp, 'token-list case', repr(parsed.tokens)
		for i,tok in enumerate(parsed.tokens):
			if is_base_identifier(tok) or isinstance(tok, sql.TokenList):
				parsed.tokens[i] = _rewrite_parse_tree(
					tok, table_translator, variable_rewriter,
					context=context if isinstance(parsed, sql.IdentifierList) else None,
					d=d+1, verbose=verbose)
			else:
				if verbose:
					print dp, 'Leaving %r in place' % tok

		return parsed
	else:
		if verbose:
			print dp, 'Returning %r as-is' % parsed
		return parsed

db = ATUS(dataset.connect('sqlite:///%s' % os.path.join(__path__[0], 'db/atus.db')))
displayed_rows = None

if __name__ == '__main__':
	while True:
		query = raw_input('> ')
		if query.strip().lower() in ['.quit', 'quit']:
			break
		if query.strip().lower().split()[0] in ['.set']:
			set_command = query.lower().split()
			try:
				display_index = set_command.index('displayed_rows')
				displayed_rows = int(set_command[display_index + 1])
				print 'displayed_rows = ', str(displayed_rows)
				continue
			except:
				print 'You did not provide a valid variable to set'
			continue
		if query.startswith('.lookup'):
			var = query.split(' ', 1)[1]
			print var
			print '='*len(var)

			if var in variables.Variables:
				print 'Aliases to expression:', variables.Variables[var][1]
				print 'Taking inputs:', ', '.join(variables.Variables[var][0])
				inputs = variables.Variables[var][0]
			else:
				inputs = [var]

			requirements = set()
			for var in inputs:
				listed_in = []
				for alias in variables.Tables:
					if var in db[variables.Tables[alias]].columns:
						listed_in.append(alias)
				print '%s in:' % var, ', '.join(['%s (%s)' % (t, variables.Tables[t]) for t in listed_in])
				requirements |= set(listed_in)

			print 'All tables for inputs:', ', '.join(requirements)

			continue
		if query.startswith('.rewrite'):
			q = query.split(' ', 1)[1]
			print db.rewrite(q)
			continue
		try:
			k = 0
			for row in db.query(query):
				if False:
					print row
				else:
					print ','.join([str(row[x]) for x in row])
				k += 1
				if displayed_rows is not None and k >= displayed_rows:
					break
		except:
			print traceback.print_exc()