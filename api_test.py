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

Count = namedtuple('Count', ['minutes', 'variance', 'interval', 'cases'])

def count(alpha=0.95, **kwargs):
	'''Count the number of respondents matching a given set of filters; returns
	a Count object.'''

	filters = '1=1'
	if kwargs.has_key('filters'):
		filters = kwargs['filters']
	
	results = atus.db.query('''SELECT count(*) FROM respondents
		inner join roster on respondents.caseid=roster.caseid and roster.lineno=1 inner join cps on cps.caseid=roster.caseid and cps.lineno=1
		where %s''' % filters,
		explain=True)

	for r in results:
		print r
		break

if __name__ == '__main__':
	count(filters='sex_code=2 and age=21')
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