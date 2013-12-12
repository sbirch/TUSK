import dataset
import readline
import sqlparse
import sqlparse.sql as sql
import traceback
import variables

class ATUS:
	def __init__(self, db):
		self.db = db
	def _variable_rewriter(self, mv):
		if mv in variables.Variables:
			return variables.Variables[mv]
		return mv
	def _infer(self, table_ref):
		# TODO: this should look at what tables are available first
		tbl = {
			'respondents': 'atusresp_0312',
			'activities': 'atusact_0312',
			'roster': 'atusrost_0312'
		}
		try:
			return tbl[table_ref]
		except KeyError:
			raise Exception('Could not find a table with the name %r'% table_ref)
	def rewrite(self, q):
		return rewrite(q, self._infer, self._variable_rewriter)
	def __getattr__(self, attr):
		return getattr(self.db, attr)
	def __getitem__(self, key):
		return self.db[key]
	def query(self, q):
		return self.db.query(self.rewrite(q))

def rewrite(sql, table_translator, variable_rewriter):
	'''
	Rewrite a SQL statement with the given table translator and
	variable rewriter. Handles SELECT statements with arbitrary
	WHERE clauses.

	TODO:
		doesn't handle AS statements in existing code
		SELECT UNIQUE
		SELECT DISTINCT

		Assumes a WHERE clause

		error messageing

		select count(*)
	select TRCODEP from activities where age<18;
	tokens: [<DML 'select' at 0x1076e2368>, <Whitespace ' ' at 0x1076e2208>, <Name 'TRCODEP' at 0x1076e2418>, <Whitespace ' ' at 0x1076e24c8>, <Keyword 'from' at 0x1076e2050>, <Whitespace ' ' at 0x1076e2100>, <Name 'activi...' at 0x1076e21b0>, <Whitespace ' ' at 0x1076e2310>, <Keyword 'where' at 0x1076e22b8>, <Whitespace ' ' at 0x1076e23c0>, <Name 'age' at 0x1076e2470>, <Comparison '<' at 0x1076e25d0>, <Integer '18' at 0x1076e2578>, <Punctuation ';' at 0x1076e26d8>]
	Traceback (most recent call last):
	  File "atus.py", line 109, in <module>
	    print row
	  File "atus.py", line 33, in query
	    return self.db.query(self.rewrite(q))
	  File "/Library/Python/2.7/site-packages/dataset/persistence/database.py", line 216, in query
	    return ResultIter(self.executable.execute(query, **kw))
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/base.py", line 1614, in execute
	    return connection.execute(statement, *multiparams, **params)
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/base.py", line 662, in execute
	    params)
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/base.py", line 805, in _execute_text
	    statement, parameters
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/base.py", line 874, in _execute_context
	    context)
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/base.py", line 1024, in _handle_dbapi_exception
	    exc_info
	  File "/Library/Python/2.7/site-packages/sqlalchemy/util/compat.py", line 196, in raise_from_cause
	    reraise(type(exception), exception, tb=exc_tb)
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/base.py", line 867, in _execute_context
	    context)
	  File "/Library/Python/2.7/site-packages/sqlalchemy/engine/default.py", line 324, in do_execute
	    cursor.execute(statement, parameters)
	OperationalError: (OperationalError) no such column: age u'select TRCODEP AS TRCODEP from atusact_0312 where age<18;' ()

	

	'''
	# TODO only handles the first statement
	parsed = sqlparse.parse(sql)[0]
	new_tree = _rewrite_parse_tree(parsed, table_translator, variable_rewriter)
	return new_tree.to_unicode()

def _rewrite_parse_tree(parsed, table_translator, variable_rewriter):
	if isinstance(parsed, sql.Statement) and parsed.get_type() == 'SELECT':
		tokens = [x for x in parsed.tokens if not x.is_whitespace()]
		dml, terms, from_keyword, table_id, where_clause = tokens
		
		if isinstance(terms, sql.IdentifierList):
			replaced_columns = []
			for term in terms.tokens:
				if term.ttype in [sqlparse.tokens.Keyword, sqlparse.tokens.Name] or isinstance(term, sql.Identifier):
					replaced_columns.append(sql.Identifier('%s AS %s' % (variable_rewriter(term.value), term.value)))
					replaced_columns.append(sql.Token(sqlparse.tokens.Punctuation, ','))
					replaced_columns.append(sql.Token(sqlparse.tokens.Whitespace, ' '))

			replaced_columns = sql.IdentifierList(replaced_columns[:-2])
		elif isinstance(terms, sql.Identifier) or terms.ttype in [sqlparse.tokens.Keyword, sqlparse.tokens.Name]:
			replaced_columns = sql.Identifier('%s AS %s' % (variable_rewriter(terms.value), terms.value))

		parsed.tokens[parsed.tokens.index(terms)] = replaced_columns
		parsed.tokens[parsed.tokens.index(table_id)] = sql.Identifier(table_translator(table_id.value))
		parsed.tokens[parsed.tokens.index(where_clause)] = _rewrite_parse_tree(where_clause, table_translator, variable_rewriter)

		return parsed
	elif isinstance(parsed, sql.Where):
		comparisons = [x for x in parsed.tokens if not x.is_whitespace() and isinstance(x, sql.Comparison)]

		for i,tok in enumerate(parsed.tokens):
			if isinstance(tok, sql.Comparison):
				parsed.tokens[i] = _rewrite_parse_tree(tok, table_translator, variable_rewriter)
			elif isinstance(tok, sql.Identifier) or tok.ttype in [sqlparse.tokens.Keyword, sqlparse.tokens.Name]:
				rewritten = variable_rewriter(tok.value)
				if tok.value != rewritten:
					parsed.tokens[i] = sql.Parenthesis([
						sql.Token(sqlparse.tokens.Group.Parenthesis, '('),
						sql.Identifier(rewritten),
						sql.Token(sqlparse.tokens.Group.Parenthesis, ')')
					])

		return parsed
	elif isinstance(parsed, sql.Comparison):
		return parsed

	raise NotImplemented()

db = ATUS(dataset.connect('sqlite:///db/atus.db'))

if __name__ == '__main__':
	while True:
		query = raw_input('> ')
		if query.strip().lower() in ['.quit', 'quit']:
			break
		try:
			k = 0
			for row in db.query(query):
				print row
				k += 1
				if k > 5:
					break
		except:
			print traceback.print_exc()