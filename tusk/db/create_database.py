#!/usr/bin/env python

import argparse
import csv
import zipfile
import os
import sqlite3
import time
import itertools
import sys
import json
from collections import defaultdict

DATAFILE_ENDINGS = ('.dat', '.csv')
COLUMN_NAMES = None

def split_and_strip(input_string, delim=","):
	if not input_string: return list()
	return_list = map(str.strip, input_string.split(delim))
	return [x.replace(' ', '_') for x in return_list]

def declare_table(cur, column_types, table_name, index=None):
	cur.execute('DROP TABLE IF EXISTS %s' % table_name)

	# Build the main table
	colspec = ', '.join([name + ' ' + data_type for name,data_type in column_types.items()])
	command = 'CREATE TABLE %s (%s)' % (table_name, colspec)
	cur.execute(command)

	# Build an index on the case ID
	if index:
		# TODO: Work on semi-automating the addition of indexes to the tables
		index_string = 'CREATE INDEX TUCASEID_INDEX_%s ON %s (`TUCASEID` ASC);' % (table_name, table_name)
		cur.execute(index_string)

def sniff_type(strings, column_name):
	if all([x.isdigit() or x == '' or (x[0]=='-' and x[1:].isdigit()) for x in strings]):
		return 'INTEGER'
	try:
		[float(x) for x in strings]
		return 'REAL'
	except ValueError:
		return 'TEXT'

def build_table(cur, conn, table_name, csv_reader):
	columns = []
	if COLUMN_NAMES.get(table_name) is not None:
		columns = split_and_strip(str(COLUMN_NAMES.get(table_name)))
	else:
		columns = csv_reader.next()
	
	# Pull off the first 100 records to sniff the column types
	sniffed_data = []
	sniff = defaultdict(list)
	for line in csv_reader:
		sniffed_data.append(line)
		for i,value in enumerate(line):
			if i >= len(columns):
				if value == '':
					continue
				columns.append(value)
			sniff[columns[i]].append(value)
		if len(sniffed_data) >= 100:
			break

	data_types = {col: sniff_type(sniff[col], col) for col in columns if col != ''}

	declare_table(cur, data_types, table_name)

	insert_command = 'INSERT INTO %s (%s) VALUES (%s);' % (
		table_name,
		','.join(columns),
		','.join(['CAST(? AS %s)' % data_types[col] for col in columns])
	)
	print insert_command

	
	# TODO(smb): double and triple check that we don't lose any records here.
	records = itertools.chain(sniffed_data, csv_reader)

	batch = True
	while batch:
		batch = list(itertools.islice(records, 10000))
		try:
			cur.executemany(insert_command, batch)
		except Exception as e:
			print e
			print 'Insert Failed: Attempting to insert row by row'
			for b in batch:
				try:
					cur.execute(insert_command, b[:len(columns)])
				except Exception as e:
					print e
					print 'Row failed', table_name, b
		sys.stdout.write('.')
		sys.stdout.flush()
		
	conn.commit()
	sys.stdout.write('\n')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Locate input files')
	parser.add_argument('-z', '--zipfile-location', dest='path',
		default='~/Dropbox/ATUS-195W/data/bigboy/',
		help='The location of the zipfiles with the ATUS data')
	parser.add_argument('--database-name', dest='db_name',
		default='database.db',
		help='The name of the generated database')
	parser.add_argument('--column-names', dest='column_names',
		default=None,
		help='A path to a json file mapping db name to column names. If not provided, the'
		' script will try to guess the names. Spaces in column names are replaced with underscores')
	args = parser.parse_args()
	arg_dict = vars(args)

	path = os.path.expanduser(arg_dict['path'])

	conn = sqlite3.connect(arg_dict['db_name'])
	cur = conn.cursor()

	if arg_dict['column_names'] is not None:
		try:
			COLUMN_NAMES = json.loads(open(arg_dict['column_names'], 'rb').read())
		except Exception as e:
			print "Error reading in column names ", e

	for zip_name in os.listdir(path):
		print zip_name
		if not zip_name.endswith('.zip'): continue
		zip_handle = zipfile.ZipFile(os.path.join(path, zip_name))

		datafiles = [fname for fname in zip_handle.namelist() if fname.endswith(DATAFILE_ENDINGS)]
		for datafile in datafiles:
			print 'Processing', datafile
			table_name = datafile.split('.')[0]

			build_table(
				cur,
				conn,
				table_name,
				csv.reader(zip_handle.open(datafile))
			)
