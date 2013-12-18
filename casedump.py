import atus, variables, sys
from variables import interpret

caseid = int(sys.argv[1])

print 'Case ID:', caseid

demographics = atus.db.get('select age, sex from roster where caseid=%s and lineno=1' % caseid)
demographics.update(atus.db.get('select region, race from cps where caseid=%s and lineno=1' % caseid))
demographics.update(atus.db.get('select labor_status from respondents where caseid=%s' % caseid))

print '{age}yo "{race}" {sex} from the {region} who is "{labor_status}"'.format(**demographics)

#TEAGE, TERRP, TESEX, TUCASEID, TULINENO
print 'Household:'
family = atus.db.query('select age,relation,sex,lineno from roster where caseid=%s order by lineno' % caseid)
for member in family:
	print '\t{lineno}: {age}yo {sex} {relation}'.format(**member)

print 'Records:'
for table in atus.db.tables:
	results = list(atus.db.query('select * from %s where caseid=%s' % (table, caseid)))
	if results:
		print '\t', table, 'has', len(results), 'records'