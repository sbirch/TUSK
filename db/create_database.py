#!/bin/env python

import argparse
import csv
import zipfile
import os
import sqlite3
import time
import itertools
import sys
from collections import defaultdict

def declare_table(cur, column_types, table_name):
	cur.execute('DROP TABLE IF EXISTS %s' % table_name)

	# Build the main table
	colspec = ', '.join([name + ' ' + data_type for name,data_type in column_types.items()])
	command = 'CREATE TABLE %s (%s)' % (table_name, colspec)
	cur.execute(command)

	# Build an index on the case ID
	index_string = 'CREATE INDEX TUCASEID_INDEX_%s ON %s (`TUCASEID` ASC);' % (table_name, table_name)
	cur.execute(index_string)

def sniff_type(strings, column_name):
	if all([x.isdigit() or (x[0]=='-' and x[1:].isdigit()) for x in strings]):
		return 'INTEGER'
	try:
		[float(x) for x in strings]
		return 'REAL'
	except ValueError:
		return 'TEXT'

def build_table(cur, conn, table_name, csv_reader):
	columns = csv_reader.next()
	
	# Pull off the first 100 records to sniff the column types
	sniffed_data = []
	sniff = defaultdict(list)
	for line in csv_reader:
		sniffed_data.append(line)
		for i,value in enumerate(line):
			sniff[columns[i]].append(value)
		if len(sniffed_data) >= 100:
			break

	data_types = {col: sniff_type(sniff[col], col) for col in columns}

	declare_table(cur, data_types, table_name)

	insert_command = 'INSERT INTO %s (%s) VALUES (%s);' % (
		table_name,
		','.join(columns),
		','.join(['CAST(? AS %s)' % data_types[col] for col in columns])
	)

	# TODO: double and triple check that we don't lose any records here.
	records = itertools.chain(sniffed_data, csv_reader)

	batch = True
	while batch:
		batch = list(itertools.islice(records, 10000))
		cur.executemany(insert_command, batch)
		sys.stdout.write('.')
		sys.stdout.flush()
	conn.commit()
	sys.stdout.write('\n')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Locate input files')
	parser.add_argument('-z', '--zipfile-location', dest='path',
		default='~/Dropbox/ATUS-195W/data/test_zip/',
		help='The location of the zipfiles with the ATUS data')
	args = parser.parse_args()
	arg_dict = vars(args)

	path = os.path.expanduser(arg_dict['path'])

	conn = sqlite3.connect('atus.db')
	cur = conn.cursor()

	for zip_name in os.listdir(path):
		zip_handle = zipfile.ZipFile(os.path.join(path, zip_name))

		datafiles = [fname for fname in zip_handle.namelist() if fname.endswith('.dat')]
		for datafile in datafiles:
			print 'Processing', datafile
			table_name = datafile.split('.')[0]

			build_table(
				cur,
				conn,
				table_name,
				csv.reader(zip_handle.open(datafile))
			)