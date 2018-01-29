#!/usr/bin/env python3
import os
import sys
import argparse
import getpass
# try:
# 	import mysql.connector
# except ImportError:
# 	print("Try installing mysqlclient again.")
# 	sys.exit()
import pymmFunctions
import dbAccess as db
# import pymmconfig

# check this out for mysql.connector install: https://gist.github.com/stefanfoulis/902296/f466a8dba3a75c172ac88627298f18eaaf0aa4c3
# brew install mysql-connector-c
# pip3 install mysql-connector
# pip3 error  ``Unable to find Protobuf include directory.`` --> `brew install protobuf`
# and if that still doesn't work try pip install mysql-connector==2.1.6

##################
#   INIT ARGS
#
parser = argparse.ArgumentParser()
parser.add_argument('-m','--mode',choices=['db','user'],help='db mode creates a PREMIS database from scratch; user mode adds a user to an existing db')
args = parser.parse_args()
createMode = args.mode
#
#
##################

config = pymmFunctions.read_config()
pymm_db = config['database settings']['pymm_db']

print("this script will set up a mysql database for use in pymm\n\nRUN THIS ON THE SERVER HOST MACHINE")

def check_db_exists(pymm_db):
	query = "SHOW DATABASES;"
	connect = db.DB()
	connect.connect()
	dostuff = connect.query(query)
	databases = dostuff.fetchall()
	dbExists = [item[0] for item in databases if pymm_db in item]
	if dbExists:
		return True
		connect.close_cursor()
		connect.close_connection()
	else:
		return False
		connect.close_cursor()
		connect.close_connection()

def create_db(pymm_db=pymm_db):
	createDbSQL = ("CREATE DATABASE IF NOT EXISTS "+pymm_db+";")
	useDB = ("USE "+pymm_db+";")
	try:
		connect = db.DB()
		connect.connect()
		cursor = connect.query(createDbSQL)
		print(cursor)
		cursor = connect.close_cursor()
	except:
		print("Check your mysql settings and try again.")
		sys.exit()
	
	cursor = connect.query(useDB)
	cursor = connect.close_cursor()

	createObjectTable =	('''CREATE TABLE object(\
							objectIdentifierValueID bigint NOT NULL AUTO_INCREMENT,\
							objectIdentifierValue varchar(1000) NOT NULL UNIQUE,\
							objectDB_Insertion datetime NOT NULL DEFAULT NOW(),\
							object_LastTouched datetime NOT NULL,\
							PRIMARY KEY (objectIdentifierValueID)\
							);\
						''')
	createEventTable = 	('''CREATE TABLE event (\
							eventIdentifierValue BIGINT(20) NOT NULL AUTO_INCREMENT,\
							objectIdentifierValue VARCHAR(1000),\
							eventType varchar(100) NOT NULL,\
							eventDateTime datetime NOT NULL DEFAULT NOW(),\
							eventDetail varchar(30) NOT NULL,\
							eventOutcome varchar(30),\
							eventDetailOPT varchar(1000),\
							eventDetailCOMPNAME varchar(50) NOT NULL,\
							linkingAgentIdentifierValue varchar(30) NOT NULL,\
							PRIMARY KEY (eventIdentifierValue),\
							FOREIGN KEY (objectIdentifierValue) REFERENCES object(objectIdentifierValue)\
							);\
						''')
	createFixityTable =	('''CREATE TABLE fixity (\
							fixityIdentifierValue bigint NOT NULL AUTO_INCREMENT,\
							eventIdentifierValue bigint NOT NULL,\
							objectIdentifierValue varchar(1000),\
							eventDateTime datetime NOT NULL DEFAULT NOW(),\
							eventDetail varchar(30) NOT NULL,\
							messageDigestAlgorithm varchar (20) NOT NULL,\
							messageDigestSOURCE varchar (1000),\
							messageDigestPATH varchar (8000) NOT NULL,\
							messageDigestFILENAME varchar (8000) NOT NULL,\
							messageDigestHASH varchar (32) NOT NULL,\
							PRIMARY KEY (fixityIdentifierValue),\
							FOREIGN KEY (eventIdentifierValue) REFERENCES event(eventIdentifierValue),\
							FOREIGN KEY (objectIdentifierValue) REFERENCES object(objectIdentifierValue)\
							);\
						''')							
	createChecksumIndex = "CREATE INDEX checksums ON fixity (messageDigestHASH);"
	createLTOschemaTable = 	('''CREATE TABLE ltoSchema (\
								ltoSchemaValueID bigint NOT NULL AUTO_INCREMENT,\
								ltoID varchar(10) NOT NULL,\
								fileName varchar(200),\
								filePath varchar(400),\
								fileSize varchar(100),\
								modifyTime varchar(40),\
								FULLTEXT (filePath),\
								PRIMARY KEY (ltoSchemaValueID)\
								);\
						''')
	createLTOidIndex = "CREATE INDEX ltoID_Index ON ltoSchema (ltoID);"
	createLTOcolumnIndex = 	('''CREATE UNIQUE INDEX lto_column_index \
								ON ltoSchema(ltoID,fileName,filePath,fileSize,modifyTime);\
								''')
	createObjectCharsTable = 	('''CREATE TABLE objectCharacteristics (\
									objectCharacteristicValueID bigint NOT NULL AUTO_INCREMENT,\
									objectIdentifierValue varchar(1000) NOT NULL UNIQUE,\
									mediaInfo MEDIUMTEXT,\
									captureLog TEXT,\
									videoFingerprint MEDIUMTEXT,\
									videoFingerprintSorted MEDIUMTEXT,\
									PRIMARY KEY (objectCharacteristicValueID),\
									FOREIGN KEY (objectIdentifierValue) REFERENCES object(objectIdentifierValue)\
									);\
								''')
	createFingerprintsTable = 	('''CREATE TABLE fingerprints (\
									hashNumber bigint NOT NULL AUTO_INCREMENT,\
									objectIdentifierValue varchar(1000) NOT NULL,\
									startframe varchar(100),\
									endframe varchar(100),\
									hash1 varchar(255),\
									hash2 varchar(255),\
									hash3 varchar(255),\
									hash4 varchar(255),\
									hash5 varchar(255),\
									PRIMARY KEY (hashNumber),\
									FOREIGN KEY (objectIdentifierValue) REFERENCES object(objectIdentifierValue)\
									);\
						''')
	createHashIndex = "CREATE INDEX hashindex ON fingerprints (hash1(244));"

	sqlToDo = [createObjectTable,createEventTable,createFixityTable,createChecksumIndex,
			createLTOschemaTable,createLTOidIndex,createLTOcolumnIndex,
			createObjectCharsTable,createFingerprintsTable,createHashIndex]


	for sql in sqlToDo:
		print("executing "+sql.rstrip())
		try:
			cursor = connect.query(sql)
			cursor = connect.close_cursor()
		except:
			print("mysql error... check your settings and try again.")
			sys.exit()
	connect.close_connection()

# def create_user():

# def main():
	# cursor = connect()



