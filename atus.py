import dataset
import readline
import sqlparse
import sqlparse.sql as sql
import sqlparse.tokens as token
import traceback
import variables
import sys

class ATUS:
	def __init__(self, db):
		self.db = db
	def _variable_rewriter(self, mv):
		table = ''
		if mv.count('.') == 1:
			table, mv = mv.split('.', 1)
			table = self._infer(table) + '.'
		if mv in variables.Variables:
			mv = variables.Variables[mv]
		return table + mv
	def _infer(self, table_ref):
		try:
			return variables.Tables[table_ref]
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

def find(L, f):
	for i,l in enumerate(L):
		if f(l):
			return i
	return None

def rewrite(sql, table_translator, variable_rewriter):
	'''
	Rewrite a SQL statement with the given table translator and
	variable rewriter. Handles SELECT statements with arbitrary
	WHERE clauses.

	TODO:
		error messaging
		GROUP BY, HAVING, ORDER BY
		table.name
	'''
	print 'Rewriting:', sql
	# TODO only handles the first statement
	parsed = sqlparse.parse(sql)[0]
	#print 'Tokens:', list([x for x in parsed.flatten() if not x.is_whitespace()])
	new_tree = _rewrite_parse_tree(parsed, table_translator, variable_rewriter)
	return new_tree.to_unicode()

def is_base_identifier(t):
	return isinstance(t, sql.Identifier) or t.ttype in [token.Keyword, token.Name]

def _rewrite_parse_tree(parsed, table_translator, variable_rewriter, context=None, d=0):
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
		#print dp, 'Terms:', terms
		assert len(terms) == 1
		terms = terms[0]
		parsed.tokens[parsed.tokens.index(terms)] = _rewrite_parse_tree(
			terms,
			table_translator,
			variable_rewriter,
			context='result-cols', d=d+1)

		end_join_source = find(parsed.tokens,
			lambda x: isinstance(x, sql.Where) or (x.ttype == token.Keyword and x.value.lower() in ['order', 'group', 'limit']))

		# replace the table name
		join_source = parsed.tokens[from_position+1:end_join_source]
		#print dp, 'Table ID:', table_id
		for table_id in join_source:
			if table_id.is_whitespace():
				continue
			parsed.tokens[parsed.tokens.index(table_id)] = _rewrite_parse_tree(
				table_id,
				table_translator,
				variable_rewriter,
				context='table', d=d+1)
		
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
					d=d+1)

		return parsed
	elif is_base_identifier(parsed):
		#print dp, 'base_identifier case context=%s' % context, repr(parsed)
		if context == 'result-cols':
			rewritten = variable_rewriter(parsed.value)
			if parsed.value != rewritten:
				#print dp, 'Rewriting result-cols %s => %s' % (parsed.value, variable_rewriter(parsed.value))
				return sql.Identifier('%s AS %s' % (variable_rewriter(parsed.value), parsed.value))
			else:
				#print dp, 'Leaving %r be' % parsed.value
				return sql.Identifier(parsed.value)
		elif context == 'table':
			if parsed.ttype == token.Keyword:
				return parsed
			#print dp, 'Rewriting %s => %s' % (parsed.value, table_translator(parsed.value))
			return sql.Identifier(table_translator(parsed.value))
		else:
			rewritten = variable_rewriter(parsed.value)
			if parsed.value != rewritten:
				#print dp, 'Rewriting %s => (%s)' % (parsed.value, variable_rewriter(parsed.value))
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
				#print dp, 'Leaving %r be' % parsed.value
			return sql.Identifier(parsed.value)
	elif isinstance(parsed, sql.TokenList):
		#print dp, 'token-list case', repr(parsed)
		for i,tok in enumerate(parsed.tokens):
			if is_base_identifier(tok) or isinstance(tok, sql.TokenList):
				parsed.tokens[i] = _rewrite_parse_tree(
					tok, table_translator, variable_rewriter,
					context=context if isinstance(parsed, sql.IdentifierList) else None,
					d=d+1)
			else:
				#print dp, 'Leaving %r in place' % tok

		return parsed
	else:
		raise Exception('Do not recognize: %r' % parsed)

db = ATUS(dataset.connect('sqlite:///db/atus.db'))

if __name__ == '__main__':

	'''
	print '-'* 40
	print db.rewrite('select age from respondents LEFT JOIN summary as activities ORDER BY age')

	print '-'* 40
	print db.rewrite('select year from respondents, activities where age=22')
	
	print '-'* 40
	print db.rewrite('select TRCODEP from activities where age<18;')
	
	
	print '-'* 40
	print db.rewrite('select count(*) from respondents where year=2010')
	
	print '-'* 40
	print db.rewrite('SELECT DISTINCT age from respondents')
	print '-'* 40
	print db.rewrite('select age, avg(family_time) from respondents, summary where respondents.case_id = summary.case_id and number_children <= 0 GROUP BY age;')
	print '-'* 40
	print db.rewrite('select age, avg(weekly_earnings) from respondents, summary where respondents.case_id = summary.case_id GROUP BY age;')

	
	'''
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