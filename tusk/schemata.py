import atus

for table in atus.db.tables:
	print table
	print '\t', ', '.join(sorted(atus.db[table].columns))

	print