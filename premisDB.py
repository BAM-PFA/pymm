#!/usr/bin/env python3
import os
import sys
try:
	import MySQLdb
except ImportError:
	print("Try installing MySQLdb again. Maybe do 'pip3 install mysqlclient'")
import pymmFunctions

config = pymmFunctions.read_config()
pymm_db = config['database settings']['pymm_db']

if pymm_db == '':
	print("ya need to set the db name at least, my man")
	sys.exit()

database = MySQLdb.connect(host='localhost',user='',password='')
cursor = database.cursor()

cursor.execute("SHOW DATABASES;")
databases = cursor.fetchall()
dbExists = [item[0] for item in databases if pymm_db in item]
if not dbExists:
	createDbSQL =  ("CREATE DATABASE IF NOT EXISTS "+pymm_db+";")
	createTablesSQL =  ("CREATE TABLE event ("
						"eventIdentifierValue BIGINT(20) NOT NULL AUTO_INCREMENT, "
						"objectIdentifierValue VARCHAR(1000), "
						"PRIMARY KEY (eventIdentifierValue)" 
						"" # ETC
						");"
						)
	print(createTablesSQL)
	useDB = ("USE "+pymm_db)
	cursor.execute(createDbSQL)
	cursor.execute(useDB)
	cursor.execute(createTablesSQL)
