#!/usr/bin/env python3
# pymm databse stuff: create & add users to a PREMIS-based mysql db
# the schema mirrors the `mm` database exactly.

import os
import sys
import argparse
import getpass
# local modules:
import pymmFunctions
import dbAccess as db
from pymmconfig import pymmconfig

##################
#   INIT ARGS
#
def set_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-m','--mode',choices=['db','user','check'],default='check',help='db mode creates a PREMIS database from scratch; user mode adds a user to an existing db')
	return parser.parse_args()
#
#
##################

config = pymmFunctions.read_config()
pymm_db = config['database settings']['pymm_db']

print("THIS SCRIPT CREATES A PYMM DATABASE, OR ADDS USERS TO ONE.\n\nRUN THIS ON THE PYMM DATABASE HOST MACHINE!!")

def check_db_exists(pymm_db=pymm_db):
	if pymm_db == '':
		print("There is no Pymm database set in the config file yet. Now exiting.")
		sys.exit()
	query = "SHOW DATABASES;"
	connect = db.DB()
	connect.connect()
	databases = connect.query(query,)
	dbExists = [item[0] for item in databases if pymm_db in item]
	if dbExists:
		print(pymm_db+" EXISTS!")
		return True
		connect.close_cursor()
		connect.close_connection()
	else:
		print(pymm_db+" DOES NOT EXIST!")
		return False
		connect.close_cursor()
		connect.close_connection()

def create_db(pymm_db=pymm_db):
	# check config file for existing db, ask for one if it doesn't exist
	if pymm_db == '':
		pymm_db = input("Please enter a name for the database: ")
	# mysql.connector won't allow %s substitution for db name... ? use str.format() method instead
	createDbSQL = "CREATE DATABASE IF NOT EXISTS {};".format(pymm_db)
	useDB = "USE {};".format(pymm_db)
	try:
		connect = db.DB()
		connect.connect()
		cursor = connect.query(createDbSQL)
		print(cursor)
		cursor = connect.close_cursor()
	except connect.Error as e:
		print(e)
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
		try:
			cursor = connect.query(sql)
			cursor = connect.close_cursor()
		except:
			print("mysql error... check your settings and try again.")
			sys.exit()
	pymmconfig.set_value("database settings",'pymm_db',pymm_db)
	connect.close_connection()

def create_user(pymm_db=pymm_db):
	print("This step will make a new user for the pymm database.\n")
	newUser = input("Please enter a name for the user: ")
	if pymm_db == '':
		targetDB = input("Please enter the name you created for the pymm databse:")
	else:
		targetDB = pymm_db
	if targetDB != pymm_db:
		print("\n\nFYI!!!\nTHE DATABSE YOU ENTERED ("+targetDB+")\n"
			"IS NOT THE SAME AS THE DATABSE IN YOUR CONFIG FILE ("+pymm_db+")")
	userPass = input("Enter a password for the user: ")
	userIP = input("Please enter the ip address for the user: ")
	if userIP == pymmFunctions.get_unix_ip():
		userIP = 'localhost'
	createUserSQL = "CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s;"
	# createUserSQL = "CREATE USER \'{}\'@\'{}\' IDENTIFIED BY \'{}\';".format(newUser,userIP,userPass)
	grantPrivsSQL = "GRANT ALL PRIVILEGES ON {}.* TO %s@%s;".format(pymm_db)
	print(createUserSQL)
	print(grantPrivsSQL)
	try:
		connect = db.DB()
		connect.connect()
		connect.query(createUserSQL,(newUser,userIP,userPass))
		connect.query(grantPrivsSQL,(newUser,userIP))
		connect.close_cursor()
		connect.close_connection()
		print("\n\nIMPORTANT!!\nTO FINISH USER SETUP, TYPE THIS TERMINAL COMMAND ON THE USER'S COMPUTER:\n"
			"mysql_config_editor set --login-path="+newUser+"_db_access --host="+userIP+" --user="+newUser+" --password=\n"
			"\nAND THEN TYPE IN THE USER PASSWORD ("+userPass+")\n"
			"AND ~THEN~ GO INTO THE USER'S LOCAL PYMMCONFIG AND ENTER THESE VALUES:\n"
			"pymm_db_name = "+newUser+"_db_access\n"
			"pymm_db = "+pymm_db+"\n")
	except:
		print("stupid error")
		sys.exit()

def main():
	if mode == 'db':
		create_db()
	elif mode == 'user':
		create_user()
	elif mode == 'check':
		check_db_exists()
	else:
		print("PLEASE PICK A MODE TO RUN THIS SCRIPT IN: '--db' TO CREATE A DATABASE,\nOR --user TO ADD USER(S).")
		sys.exit()

if __name__ == '__main__':
	args = set_args()
	mode = args.mode
	print(mode)
	main()
