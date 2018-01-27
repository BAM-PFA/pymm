#!/usr/bin/env python3
import os
import sys
import argparse
import getpass
try:
	import mysql.connector
except ImportError:
	print("Try installing mysqlclient again.")
import pymmFunctions
import pymmconfig

# check this out for mysql.connector install: https://gist.github.com/stefanfoulis/902296/f466a8dba3a75c172ac88627298f18eaaf0aa4c3
# brew install mysql-connector-c
# pip install mysql-python

##################
#   INIT ARGS
#
parser = argparse.ArgumentParser()
parser.add_argument('-m','--mode','--inputFilepath',choices=['db','user'],help='db mode creates a PREMIS database from scratch; user mode adds a user to an existing db')
args = parser.parse_args()
createMode = args.mode
#
#
##################

config = pymmFunctions.read_config()
pymm_db = config['database settings']['pymm_db']

print("this script will set up a mysql database for use in pymm\r\rRUN THIS ON THE SERVER HOST MACHINE")

# if not dbExists:
# def check_local_option_file():
# 	optionFilePath = "~/.my.cnf"
# 	if not os.path.isfile(optionFilePath):
# 		try:
# 			with open(optionFilePath,'x') as opt:
# 				print('made an option file to read')
# 				return True
# 		except:
# 			print('couldnt make an option file try again?')
# 			sys.exit()
# 	else:
# 		return True



def connect():
	pw = getpass.getpass(prompt="enter password for mysql root:")
	connection = mysql.connector.connect(host='localhost',user='root',password=pw)
	cursor = connection.cursor()
	return cursor

def check_db_exists(pymm_db):
	cursor = connect()
	cursor.execute("SHOW DATABASES;")
	databases = cursor.fetchall()
	dbExists = [item[0] for item in databases if pymm_db in item]
	if dbExists:
		return True
	else:
		return False

def create_db(pymm_db):
	createDbSQL = ("CREATE DATABASE IF NOT EXISTS "+pymm_db+";")
	useDB = ("USE "+pymm_db+";")
	try:
		cursor.execute(createDbSQL)
	except:
		print("Check your mysql settings and try again.")
		sys.exit()
	
	cursor.execute(useDB)

	createObjectTable =  ('''CREATE TABLE object(\
							objectIdentifierValueID bigint NOT NULL AUTO_INCREMENT,\
							objectIdentifierValue varchar(1000) NOT NULL UNIQUE,\
							objectDB_Insertion datetime NOT NULL DEFAULT NOW(),\
							object_LastTouched datetime NOT NULL,\
							PRIMARY KEY (objectIdentifierValueID)\
							);\
							''')
	createEventTable = ('''CREATE TABLE event (\
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
	createFixityTable = ('''CREATE TABLE fixity (\
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
	createLTOschemaTable = ('''CREATE TABLE ltoSchema (\
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
	createLTOcolumnIndex = "CREATE UNIQUE INDEX lto_column_index ON ltoSchema(ltoID,fileName,filePath,fileSize,modifyTime);"
	createObjectCharsTable = ('''CREATE TABLE objectCharacteristics (\
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
	createFingerprintsTable = ('''CREATE TABLE fingerprints (\
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
			cursor.execute(sql)
		except:
			print("mysql error... check your settings and try again.")
			sys.exit()

# def create_user():

def main():
	# cursor = connect()



