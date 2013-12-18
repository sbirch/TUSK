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
LEXICON = json.load(open('activity-lexicon/activity_lexicon.json', 'rb'))

def interpret_code(variable, value):
	if variable not in DICTIONARY and variable in Variables:
		variable = Variables[variable][0]
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

# A SQLite UDF
def sql_decode(original_name, value):
	return interpret_code(original_name, value)

def sql_decode_activity(activity_code):
	activity_code = str(activity_code)
	code_size = len(activity_code)
	return LEXICON.get(activity_code.rjust(code_size+1 if code_size%2 == 1 else code_size, '0'), 'unknown activity code %s' % activity_code)

# A SQLite aggregator
class SQL_collect:
    def __init__(self):
        self.collected = []
    def step(self, value):
        self.collected.append(value)
    def finalize(self):
        return json.dumps(self.collected)

def sql_family_income(hufaminc, hefaminc, year):
	if year > 2009:
		# note that HEFAMINC is interpreted like HUFAMINC because the
		# codes are the same and only listed in full for HUFAMINC
		return interpret_code('HUFAMINC', hefaminc)
	return interpret_code('HUFAMINC', hufaminc)

# A map from alias to (variable, expression)
# If not a tuple, assumed that variable and expression are the same, for
# brevity (this is patched up below.)
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
	'weekly_earnings': ('TRERNWA', '(TRERNWA/100.0)'),
	'weekly_overtime_earnings': ('TEERN', '(TEERN/100.0)'),
	'friend_time': 'TRTFRIEND',
	'family_time': 'TRTFAMILY',
	'caseid': 'TUCASEID',
	'lineno': 'TULINENO',
	'relation_code': 'TERRP',
	'family_income': (None, 'family_income(HUFAMINC, HEFAMINC, HRYEAR4)'),
	'education_code': 'PEEDUCA',
	'activity_location_code': 'TEWHERE',

	# activity codes are special cased
	'activity_code': 'TRCODEP',
	'activity_tier1_code': 'TRTIER1P',
	'activity_tier2_code': 'TRTIER2P',
	'activity': ('TRCODEP', 'decode_activity(TRCODEP)'),
	'activity_tier1': ('TRTIER1P', 'decode_activity(TRTIER1P)'),
	'activity_tier2': ('TRTIER2P', 'decode_activity(TRTIER2P)'),
	'duration': 'TUACTDUR',
	'activity_number': 'TUACTIVITY_N',
	'start_time': 'TUSTARTTIM',
	'stop_time': 'TUSTOPTIME',

	# TODO: this is only the right name in the multi-year files
	'weight': 'TUFNWGTP'

	# occupation
}

# If aliases go to a single string, assume that it's the variable
# name and the expression.
for aliased in Variables:
	if not isinstance(Variables[aliased], tuple):
		Variables[aliased] = (Variables[aliased], Variables[aliased])

# Automatically add decoded versions of _code variables
for aliased, (var, expr) in Variables.items():
	if aliased in ['activity_code', 'activity_tier1_code', 'activity_tier2_code']:
		continue
	elif aliased.endswith('_code'):
		Variables[aliased[:-len('_code')]] = (var, "decode('%s', %s)" % (var, expr))

def rewrite(original_name):
	if original_name in Variables:
		return Variables[original_name][1]
	return original_name

# n.b. this will have to change from a 1-1 mapping to be robust to different
# data sources. Will have to look at what tables are available.
Tables = {
	'activities': 'atusact_0312',
	'summary': 'atussum_0312',
	'respondents': 'atusresp_0312',
	'roster': 'atusrost_0312',
	'cps': 'atuscps_0312'
}