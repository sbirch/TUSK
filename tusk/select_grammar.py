import pyparsing
from pyparsing import Optional, White, Word, Regex, alphas, CaselessLiteral, CaselessKeyword, oneOf, delimitedList, Forward, ZeroOrMore, NotAny, Keyword, Literal

# transformString doesn't play nice with suppressed anything, including
# whitespace. So it seems like the only effective way to use it is with
# explicit whitespace.
pyparsing.ParserElement.setDefaultWhitespaceChars('')

W = White()
OW = Optional(White())

CKeyword = CaselessKeyword
comma_list = lambda x: x + ZeroOrMore(OW + ',' + OW + x)

unary_op = oneOf('- + ~', caseless=True)
unary_op |= CKeyword('NOT')

# TODO this does not encode precedence
binary_op = oneOf("|| * / % + - << >> & | < <= > >= = == != <>", caseless=True)
binary_op |= reduce(lambda x,y: x|y, [CKeyword(x) for x in 'IS,IS NOT,IN,LIKE,GLOB,MATCH,REGEXP,AND,OR'.split(',')])

# these direct from the SQLite docs
KEYWORDS = 'ABORT ACTION ADD AFTER ALL ALTER ANALYZE AND AS ASC ATTACH AUTOINCREMENT BEFORE BEGIN BETWEEN BY CASCADE CASE CAST CHECK COLLATE COLUMN COMMIT CONFLICT CONSTRAINT CREATE CROSS CURRENT_DATE CURRENT_TIME CURRENT_TIMESTAMP DATABASE DEFAULT DEFERRABLE DEFERRED DELETE DESC DETACH DISTINCT DROP EACH ELSE END ESCAPE EXCEPT EXCLUSIVE EXISTS EXPLAIN FAIL FOR FOREIGN FROM FULL GLOB GROUP HAVING IF IGNORE IMMEDIATE IN INDEX INDEXED INITIALLY INNER INSERT INSTEAD INTERSECT INTO IS ISNULL JOIN KEY LEFT LIKE LIMIT MATCH NATURAL NO NOT NOTNULL NULL OF OFFSET ON OR ORDER OUTER PLAN PRAGMA PRIMARY QUERY RAISE REFERENCES REGEXP REINDEX RELEASE RENAME REPLACE RESTRICT RIGHT ROLLBACK ROW SAVEPOINT SELECT SET TABLE TEMP TEMPORARY THEN TO TRANSACTION TRIGGER UNION UNIQUE UPDATE USING VACUUM VALUES VIEW VIRTUAL WHEN WHERE'

# TODO probably not right charset & does not account for escaping identifiers
# https://www.sqlite.org/lang_keywords.html
identifier = NotAny(
	reduce(lambda x,y: x|y, [CKeyword(x) for x in KEYWORDS.split(' ')])
	) + Regex('[a-zA-Z_][a-zA-Z0-9_]*')

# for the purposes of attaching parse actions to these
# objects they need to all be separate. table_in_column
# is to distinguish between tables as found in the grammar
# and those specifically found (optionally) in a column spec
# (which gets triggered whether there's actually a table part
# or not.)
table_name = identifier.copy()
table_in_column = table_name.copy()
database_name = identifier.copy()
column_name = identifier.copy()

column = Optional(database_name + '.') + Optional(table_in_column + '.') + column_name

integer_num = Regex('[0-9]+')
exponent = Regex('[eE][\+\-]?[0-9]+')
# floats either have a decimal or an exponent
float_num = Regex('(((\.[0-9]+|[0-9]+\.[0-9]*)([eE][\+\-]?[0-9]+)?)|[0-9]+[eE][\+\-]?[0-9]+)')
# strings are escaped with double single quotes in SQL
string_literal = Regex("'([^']|'')*'")
blob_literal = Regex("[xX]'((?:[a-fA-F0-9]{2})+)'")

literal = float_num | integer_num | string_literal | blob_literal | \
	CKeyword('NULL') | \
	CKeyword('CURRENT_TIME') | \
	CKeyword('CURRENT_DATE') | \
	CKeyword('CURRENT_TIMESTAMP')

expression = Forward()
join_source = Forward()
select = Forward()

unary_term = unary_op + OW + expression

function_term = identifier + '(' + OW + \
	( '*' | (Optional(CKeyword('DISTINCT') + W) + Optional(comma_list(expression))) ) + \
	OW + ')'

parens_term = '(' + OW + expression + OW + ')'

type_name = oneOf('TEXT REAL INTEGER BLOB NUMERIC', caseless=True)
cast = CKeyword('CAST') + OW + '(' + OW + expression + W + CKeyword('AS') + W + type_name + OW + ')'

# TODO: does not include full TCL-style $parameters
parameter = (
	('?' + Optional(Regex('[0-9]+'))) | 
	(Regex('[\$\:\@]') + identifier)
)

# TODO: not in, not between, is not, isnull, like
# Not included: raise, case, not exists, collate
atom = parameter | literal | unary_term | cast | function_term | column | parens_term
expression << atom + ZeroOrMore(OW + binary_op + OW + expression)

table_wildcard = (table_name + '.*').setResultsName('table_wildcard')
# n.b. in the SQLite grammar "AS" is optional
result_column = ('*' ^
	(expression + Optional(Optional(W + CKeyword('AS')) + W + identifier)) ^
	table_wildcard
)
result_column_list = comma_list(result_column)

# TODO probably not right charset
collation_name = Regex('[a-zA-Z0-9_]+')
ordering_term = expression + \
	Optional(W + CKeyword('COLLATE') + W + collation_name) + \
	Optional(W + (CKeyword('ASC') | CKeyword('DESC')))

table_alias = Optional(CKeyword('AS') + W) + identifier
index_spec = (CKeyword('INDEXED BY') + W + identifier) | CKeyword('NOT INDEXED')
join_type = CKeyword('INNER') | CKeyword('CROSS') | (CKeyword('LEFT') + Optional(W+CKeyword('OUTER')))
# unlike everything else this has whitespace built-in
join_op = (OW+','+OW) | (Optional(W + CKeyword('NATURAL')) + Optional(W + join_type) + W + CKeyword('JOIN') + W)
join_constraint = (
	(CKeyword('ON') + W + expression) |
	# TODO: using technically works on column_names, not columns
	# but actions are attached to columns so this allows a superset
	(CKeyword('USING') + OW + '(' + OW + comma_list(column) + OW + ')')
)
join_function = identifier + '(' + OW + comma_list(table_name) + OW + ')'
single_source = (
	# n.b. special sauce: join-source functions
	(join_function + Optional(W + table_alias)) ^
	(Optional(database_name + '.') + table_name + Optional(W + table_alias) + Optional(W + index_spec)) ^
	('(' + OW + select + OW + ')' + Optional(W + table_alias)) ^
	('(' + OW + join_source + OW + ')')
)
join_source << (
	single_source + \
	ZeroOrMore(join_op + single_source + Optional(W + join_constraint))
)

where_clause = CKeyword('WHERE') + W + expression

group_by_clause = CKeyword('GROUP BY') + W + comma_list(expression) + \
	Optional(W + CKeyword('HAVING') + W + expression)
order_by_clause = CKeyword('ORDER BY') + W + comma_list(ordering_term)
limit_clause = CKeyword('LIMIT') + W + expression + \
	Optional(( (W + CKeyword('OFFSET') + W) | (OW + ',' + OW)) + expression)


# N.B. this doesn't account for compound operators (union, intersect...)
select << (\
	CKeyword('SELECT') + W + Optional((CKeyword('DISTINCT') | CKeyword('ALL')) + W) + \
	result_column_list.setResultsName("result_columns") + \
	Optional(W + CKeyword('FROM') + W + join_source.setResultsName("join_source")) + \
	Optional(W + where_clause).setResultsName("where") + \
	Optional(W + group_by_clause).setResultsName("group_by") + \
	Optional(W + order_by_clause).setResultsName("order_by") + \
	Optional(W + limit_clause).setResultsName("limit")
)
	

SQL_select = pyparsing.StringStart() + OW + select + Optional(';') + pyparsing.StringEnd()

if __name__ == '__main__':
	'''
	def dbgStart(s, loc, grammar):
		print 'Starting', s
	def dbgSuccess(s, start, end, grammar, match): #
		print 'Success', s
	def dbgExcept(s, loc, grammar, e):
		print 'Except', s
	SQL_select.setDebugActions(dbgStart, dbgSuccess, dbgExcept)
	'''

	def translate_col_name(loc, toks):
		print 'column:', toks, loc
		return '.'.join(['XX']*len([x for x in toks if x != '.']))
	column.setParseAction(translate_col_name)
	def translate_table_name(loc, toks):
		print 'table:', toks, loc
		return 'XX'
	table_name.setParseAction(translate_table_name)
	def translate_join_function(loc, toks):
		#print 'join func:', toks, loc
		toks[0] = 'XX'
		return toks
	join_function.setParseAction(translate_join_function)

	tests = '''
	# result columns
	select A
	   select 1
	select *;
	# TODO
	*select A.* from T
	select A R
	select A A
	select A as C
	select all A
	select DISTINCT A
	select A,B from T
	select A=B

	# where
	select A where T.A=T.B or T.B <> T.A
	select A where A LIKE B
	select A where A=100
	select A where A=1e4
	select A where A=1.4e-4
	select A where A is CURRENT_DATE
	select A where A is 'how''s A going'
	select A where A is x'72aef9'
	select A where -1=A
	select A where -1=-A
	select A where not A is ~A
	select A where cast (A as integer) is ((1))
	select A where funfun(DISTINCT A, B) || 0 == 4
	select A where funfun(*)=A
	select A where ? = ?45 and @x = :x+$A

	# group by
	select A group by B
	select A group by B,A
	select A group by B, A HAVING B

	# order by & limit
	select A,B order by A
	select A order by A, B
	select A order by A,B
	select A,B order by A limit 5
	select A,B from T order by A limit B
	select A from T limit B+1,5
	select A from T limit B+1 ,  5
	select A from T limit B+1 OFFSET (B/2)

	# joins
	select A,B from T,T,T where A=B and B=A
	select A FROM T,T, T
	select A FROM T inner join T
	select A from T left join T
	select A from T natural left outer join T
	select A FROM T natural inner join T
	select A from T natural cross join T
	select A from T cross join T, T left join T
	select A from T cross join T, T left outer join T
	select A from T,T USING (A,B)
	select A from T,T USING ( A , B )
	select A from T,T ON T.A = T.B+T.B
	select A from T AS T cross join T AS T ON (T.A=T.B+T.B)
	select A from T AS T not INDEXED cross join T AS T ON (T.A=T.B+T.B)
	select A from T AS T INDEXED by some_index cross join T AS T ON (T.A=T.B+T.B)
	select A from (select B from T)
	select A from ( select B from T ) as T
	select A from (T cross join T on (T.A=T.B))

	# some real queries
	  select age, weighted_avg(family_time, respondents.weight) as avg_famtime from respondent_link(respondents, summary) group by age
	select count(*) as c, 5, RC1+5 from respondents, activities where age=(21+1) and WC1=2010;
	'''.strip().split('\n')
	tests = [x.lstrip() for x in tests if x.strip() != '']
	tests = [x for x in tests if len(x) > 0 and x[0] != '#']
	tests = [x[1:] for x in tests if x[0] == '*']

	import pprint
	for t in tests:
		try:
			pr = SQL_select.parseString(t)
			print pr.dump()
			print t
			print '=>'
			print SQL_select.transformString(t)
			print
		except pyparsing.ParseException as e:
			import traceback
			traceback.print_exc()
			print t
			print ' '*(e.col-1) + '^'
			print