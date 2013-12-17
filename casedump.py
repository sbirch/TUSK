import atus, sys

caseid = int(sys.argv[1])

print 'Case ID:', caseid

for table in atus.db.tables:
	results = list(atus.db.query('select * from %s where TUCASEID=%s' % (table, caseid)))

	if results:
		print table, len(results), 'records'