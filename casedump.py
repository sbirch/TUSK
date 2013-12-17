import atus, variables, sys
from variables import interpret

caseid = int(sys.argv[1])

print 'Case ID:', caseid

demographics = atus.db.get('select age, sex_code from roster where case_id=%s and lineno=1' % caseid)
demographics.update(atus.db.get('select region_code, race_code from cps where case_id=%s and lineno=1' % caseid))
demographics.update(atus.db.get('select labor_status_code from respondents where case_id=%s' % caseid))

print '%dyo %r %s from the %s who is %r' % (
	demographics['age'],
	interpret(demographics, 'race_code'),
	interpret(demographics, 'sex_code'),
	interpret(demographics, 'region_code'),
	interpret(demographics, 'labor_status_code')
)

print 'Records:'
for table in atus.db.tables:
	results = list(atus.db.query('select * from %s where TUCASEID=%s' % (table, caseid)))
	if results:
		print '\t', table, 'has', len(results), 'records'