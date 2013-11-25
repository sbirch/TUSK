#!/bin/env python

import argparse
import csv
import zipfile
import os
import sqlite3
import time


parser = argparse.ArgumentParser(description='Locate input files')
parser.add_argument('-z', '--zipfile-location', dest='path',
	default='~/Dropbox/ATUS-195W/data/test_zip/',
	help='The location of the zipfiles with the ATUS data')
args = parser.parse_args()
arg_dict = vars(args)
path = arg_dict['path']

datafiles = os.listdir(path)

conn = sqlite3.connect('atus.db')
cur = conn.cursor()

def find_dat_files(list_of_files):
	correct_list = []
	for x in range(len(list_of_files)):
		last = list_of_files[x].split('/')[-1:][0]
		if (len(last) > 0 and last[0] != '.' and last[-4:] == '.dat'):
			correct_list.append(list_of_files[x])
	return correct_list




def parse_data(rawData):
	colsLabels = {}
	for i,x in enumerate(rawData[1]):
		try:
			time.strptime(x, '%H:%M:%S')
			info_tuple = (rawData[0][i], 'time')
			colsLabels[i] = info_tuple
		except:
			try:
				float(x)
				info_tuple = (rawData[0][i], 'float')
				colsLabels[i] = info_tuple
			except ValueError:
				try:
					str(x)
					info_tuple = (rawData[0][i], 'string')
					colsLabels[i] = info_tuple
				except:
					print'error'
	return colsLabels

def create_table_string(cols, name):
	createString = 'CREATE TABLE ' + name + ' ('
	for x in range(len(cols.keys())):
		the_name, the_type = cols[x]
		createString = createString + the_name + ' ' + the_type + ', '
	createString = createString[:-2] + ');'
	return createString

def create_table(create_string, table_name):
	cur.execute(create_string)
	index_string = 'CREATE INDEX TUCASEID_INDEX_%s ON %s (`TUCASEID` ASC);' % (table_name, table_name)
	cur.execute(index_string)

def insert_data(data_list, table_name):
	columns = data_list.pop(0)
	insert_string = 'INSERT INTO %s (%s) VALUES (%s);' % (
		table_name,
		','.join(columns),
		','.join(['?']*len(columns))
	)
	cur.executemany(insert_string, data_list)
	conn.commit()


for myfile in datafiles:
	theZipper = zipfile.ZipFile(path+myfile)
	datafiles = find_dat_files(theZipper.namelist())
	for aDataFile in datafiles:
		print aDataFile
		rawData = []
		for line in csv.reader(theZipper.open(aDataFile)):
			rawData.append(line)
		cols = parse_data(rawData)
		table_name = aDataFile.split('.')[0]
		drop_string = 'DROP TABLE IF EXISTS ' + table_name 
		cur.execute(drop_string)
		create_string = create_table_string(cols, table_name)
		create_table(create_string, table_name)
		insert_data(rawData, table_name)


