import dataset
import variables

db = ATUS(dataset.connect('sqlite:///db/atus.db'))

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
	where_string = ''
	from_tables = []
	act_sum = False
	for param in kwargs.keys():
		if param == 'group_by':
			group = variables.Variables[param['group_by']] if param['group_by'] in variables.Variables else param['group_by']
			select_string = select_string + ', ' + group
		if param in variables.summary_variables:
			act_sum = True
		else:
			pass

	args
	#return persondays