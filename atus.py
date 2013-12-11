import dataset
import traceback
import sqlparse
import sqlparse.sql as sql
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
		return tbl[table_ref]
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

if __name__ == '__main__': # Jana approved
	db = ATUS(dataset.connect('sqlite:///db/atus.db'))

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