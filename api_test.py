import atus
import variables
from collections import namedtuple
import sys

'''
count API
filters (incl activity)
normalization
Output: person-minutes + bounds, record count, caseids
How to get uncertainty on normalized proportions from uncertain part/whole?
Evaluate confidence bounds by estimating state populations
'''

Count = namedtuple('Count', ['people', 'count', 'cases'])

def count(alpha=0.95, **kwargs):
	'''Count the number of respondents matching a given set of filters; returns
	a Count object.'''

	filters = '1=1'
	if kwargs.has_key('filters'):
		filters = kwargs['filters']
	
	results = atus.db.query('''SELECT roster.caseid, weight FROM respondents
		inner join roster on respondents.caseid=roster.caseid and roster.lineno=1 inner join cps on cps.caseid=roster.caseid and cps.lineno=1
		where %s;''' % filters)

	results = list(results)
	
	return Count(
		sum([x['weight'] for x in results]) / len(results),
		len(results),
		[x['caseid'] for x in results]
	)

if __name__ == '__main__':

	
	import sqlite3
	query = 'SELECT TUFNWGTP AS weight FROM atusresp_0312 inner join atusrost_0312 on atusresp_0312.TUCASEID=atusrost_0312.TUCASEID and atusrost_0312.TULINENO=1 inner join atuscps_0312 on atuscps_0312.TUCASEID=atusrost_0312.TUCASEID and atuscps_0312.TULINENO=1 where (atusrost_0312.TESEX=2 and atusrost_0312.TEAGE=21)'
	#query = 'SELECT TUFNWGTP AS weight FROM atusresp_0312 inner join atusrost_0312 on atusresp_0312.TUCASEID=atusrost_0312.TUCASEID and atusrost_0312.TULINENO=1 inner join atuscps_0312 on atuscps_0312.TUCASEID=atusrost_0312.TUCASEID and atuscps_0312.TULINENO=1 where TEAGE=21 or TESEX=2;'
	conn = sqlite3.connect('db/atus.db')

	print conn
	def move():
		sys.stdout.write('.')
		sys.stdout.flush()
	conn.set_progress_handler(move, 10000)

	for result in conn.execute(query):
		continue

	print
	

	#print count(filters='age>=80 and sex_code=1 and year=2010')
	sys.exit(0)


def weighted_groupby_count():
	'''
	Params: list of (category, weight)
	Returns: list of (category label, weighted count) 
	'''
	pass

def weighted_groupby_avg():
	'''
	Params: list of (category, number, weight)
	Returns: list of (category label, weighted average) 
	'''
	pass

def weighted_groupby_sum():
	'''
	Params: list of (category, number, weight)
	Returns: list of (category label, weighted sum)
	'''
	pass

def activity_count(**kwargs):
	query_string = ''
	select_string = 'SELECT count(*)'
	from_tables = []
	for param in kwargs.keys():
		if param == 'group_by':
			group = variables.Variables[param['group_by']] if param['group_by'] in variables.Variables else param['group_by']
			select_string = select_string + ', ' + group
		

	args
	#return persondays