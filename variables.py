import json

def interp_varname(varname):
	first = varname[0]
	second = varname[1]

	#T - RT in ATUS vars
	# TXAGE_EC 

	if first == 't':
		return (varname[1:], 'ATUS-interview', 'summary-file')
	else:
		fl_types = {
			'G': 'CPS-geography',
			'H': 'CPS-household',
			'P': 'CPS-person',
			'T': 'ATUS-interview'
		}
		sl_types = {
			'U': 'unedited',
			'E': 'edited',
			'R': 'recoded',
			'T': 'topcoded'
		}
		return (varname[2:], fl_types[first], sl_types[second])

DICTIONARY = json.load(open('data-dictionary/data_dictionary.json', 'rb'))

def interpret_code(variable, value):
	if variable not in DICTIONARY and variable in Variables:
		variable = Variables[variable]
	try:
		metadata = DICTIONARY[variable]
		if metadata["validEntries"].has_key(str(value)):
			return str(metadata["validEntries"][str(value)])
		elif value == -1:
			return 'blank'
		elif value == -2:
			return 'don\'t know'
		elif value == -3:
			return 'refused'
	except KeyError:
		return str(value)

def interpret(d, k):
	return interpret_code(k, d[k])

# TODO define any functions needed for the binding
# TODO how should we deal with cross-table selects?
# TODO null code -1 values
# TODO see variableNotes
Variables = {
	'age': 'TEAGE',
	'sex_code': 'TESEX',
	'race_code': 'PTDTRACE',
	'labor_status_code': 'TELFS',
	'region_code': 'GEREG',
	'housing_type_code': 'HEHOUSUT',
	'household_id': 'HRHHID',
	'fulldate': 'TUDIARYDATE',
	'month': 'TUMONTH',
	'year': 'TUYEAR',
	'cps_year': 'HRYEAR4',
	'cps_month': 'HRMONTH',
	'weekday_code': 'TUDIARYDAY',
	'household_members': 'HRNUMHOU',
	'weekly_earnings': '(TEERN/100.0)',
	'friend_time': 'TRTFRIEND',
	'family_time': 'TRTFAMILY',
	'case_id': 'TUCASEID',
	'lineno': 'TULINENO',
	# TODO: this is only the right name in the multi-year files
	'person_weight': 'TUFNWGTP'

	# occupation
	# race
	# household income
}

# n.b. this will have to change from a 1-1 mapping to be robust to different
# data sources. Will have to look at what tables are available.
Tables = {
	'activities': 'atusact_0312',
	'summary': 'atussum_0312',
	'respondents': 'atusresp_0312',
	'roster': 'atusrost_0312',
	'cps': 'atuscps_0312'
}