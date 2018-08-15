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
	parser.add_argument(
		'-m','--mode',
		choices=['database','user','check'],
		help=(
			'database mode creates a PREMIS database from scratch; '
			'user mode adds a user to an existing db'
			)
		)
	return parser.parse_args()
#
#
##################

config = pymmFunctions.read_config()
pymm_db = config['database settings']['pymm_db']

print(
	"THIS SCRIPT CREATES A PYMM DATABASE, OR ADDS USERS TO ONE.\n"
	"\nRUN THIS ON THE PYMM DATABASE HOST MACHINE!!"
	)

def connect_to_mysql(user='root'):
	try:
		connect = db.DB(user)
		connection = connect.connect()
		return connect
	except:
		print("you got some mysql connection issues, "
			"maybe the user doesn't exist?")
		sys.exit()

def check_db_exists(pymm_db=pymm_db):
	if pymm_db == '':
		print("There is no Pymm database set "
			"in the config file yet. Now exiting.")
		sys.exit()
	showDBs = "SHOW DATABASES"
	connect = connect_to_mysql('root')
	# connect = db.DB('root')
	# connect.connect()
	databases = connect.query(showDBs,)
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
	# mysql.connector only allows parameterization for INSERT and SELECT
	# use str.format() method instead
	createDbSQL = "CREATE DATABASE IF NOT EXISTS {}".format(pymm_db)
	# set 'use database' setting to True
	pymmconfig.set_value("database settings",'use_db','y')
	useDB = "USE {}".format(pymm_db)
	try:
		connect = db.DB('root')
		connect.connect()
		cursor = connect.query(createDbSQL)
		cursor = connect.close_cursor()
	except:
		print("Error: uh, error.. :(")
		sys.exit()
	
	cursor = connect.query(useDB)
	print(cursor)

	createObjectTable =	('''CREATE TABLE IF NOT EXISTS object(\
							objectIdentifierValueID BIGINT(20) NOT NULL AUTO_INCREMENT,\
							objectIdentifierValue VARCHAR(1000) NOT NULL UNIQUE,\
							objectCategory VARCHAR(30) NOT NULL,\
							objectCategoryDetail VARCHAR(50) NOT NULL,\
							objectDB_Insertion datetime NOT NULL DEFAULT NOW(),\
							object_LastTouched datetime NOT NULL,\
							PRIMARY KEY (objectIdentifierValueID)\
							);\
						''')
	createEventTable = 	('''CREATE TABLE IF NOT EXISTS event (\
							eventIdentifierValue BIGINT(20) NOT NULL AUTO_INCREMENT,\
							objectIdentifierValueID BIGINT(20),\
							objectIdentifierValue VARCHAR(1000),\
							eventType VARCHAR(100) NOT NULL,\
							eventDateTime datetime NOT NULL DEFAULT NOW(),\
							eventOutcome VARCHAR(30) NOT NULL,\
							eventOutcomeDetail VARCHAR(1000),\
							eventDetailCallingFunc VARCHAR(1000),\
							eventDetailCOMPUTER VARCHAR(50) NOT NULL,\
							linkingAgentIdentifierValue VARCHAR(30) NOT NULL,\
							PRIMARY KEY (eventIdentifierValue),\
							FOREIGN KEY (objectIdentifierValueID) REFERENCES object(objectIdentifierValueID)\
							);\
						''')
	# messageDigestSOURCE is optionally read from an objects_manifest
	createFixityTable =	('''CREATE TABLE IF NOT EXISTS fixity (\
							fixityIdentifierValue BIGINT NOT NULL AUTO_INCREMENT,\
							eventIdentifierValue BIGINT(20) NOT NULL,\
							objectIdentifierValueID BIGINT(20),\
							objectIdentifierValue VARCHAR(1000),\
							eventDateTime DATETIME NOT NULL DEFAULT NOW(),\
							eventDetailCallingFunc VARCHAR(30) NOT NULL,\
							messageDigestAlgorithm VARCHAR (20) NOT NULL,\
							messageDigestFilepath VARCHAR (8000) NOT NULL,\
							messageDigestHashValue VARCHAR (32) NOT NULL,\
							messageDigestSOURCE VARCHAR (1000),\
							PRIMARY KEY (fixityIdentifierValue),\
							FOREIGN KEY (eventIdentifierValue) REFERENCES event(eventIdentifierValue),\
							FOREIGN KEY (objectIdentifierValueID) REFERENCES object(objectIdentifierValueID)\
							);\
						''')

	createChecksumIndex = "CREATE INDEX checksums ON fixity (messageDigestHashValue);"
	createLTOschemaTable = 	('''CREATE TABLE IF NOT EXISTS ltoSchema (\
								ltoSchemaValueID BIGINT NOT NULL AUTO_INCREMENT,\
								ltoID VARCHAR(10) NOT NULL,\
								fileName VARCHAR(200),\
								filePath VARCHAR(400),\
								fileSize VARCHAR(100),\
								modifyTime VARCHAR(40),\
								FULLTEXT (filePath),\
								PRIMARY KEY (ltoSchemaValueID)\
								);\
						''')
	createLTOidIndex = "CREATE INDEX ltoID_Index ON ltoSchema (ltoID);"
	createLTOcolumnIndex = 	('''CREATE UNIQUE INDEX lto_column_index \
								ON ltoSchema(ltoID,fileName,filePath,fileSize,modifyTime);\
								''')
	createObjectCharsTable = 	('''CREATE TABLE IF NOT EXISTS objectCharacteristics (\
									objectCharacteristicValueID BIGINT NOT NULL AUTO_INCREMENT,\
									objectIdentifierValueID BIGINT(20) NOT NULL,\
									objectIdentifierValue VARCHAR(1000),\
									mediaInfo LONGTEXT,\
									ingestLog LONGTEXT,\
									pbcoreOutput LONGTEXT,\
									pbcoreXML MEDIUMBLOB,\
									PRIMARY KEY (objectCharacteristicValueID),\
									FOREIGN KEY (objectIdentifierValueID) REFERENCES object(objectIdentifierValueID)\
									);\
								''')
	# THIS IS STRAIGHT FROM CUNY.... NOT SURE IF/HOW WE WILL USE IT.
	createFingerprintsTable = 	('''CREATE TABLE IF NOT EXISTS fingerprints (\
									hashNumber BIGINT NOT NULL AUTO_INCREMENT,\
									objectIdentifierValue VARCHAR(1000) NOT NULL,\
									startframe VARCHAR(100),\
									endframe VARCHAR(100),\
									hash1 VARCHAR(255),\
									hash2 VARCHAR(255),\
									hash3 VARCHAR(255),\
									hash4 VARCHAR(255),\
									hash5 VARCHAR(255),\
									PRIMARY KEY (hashNumber),\
									FOREIGN KEY (objectIdentifierValue) REFERENCES object(objectIdentifierValue)\
									);\
						''')
	createHashIndex = "CREATE INDEX hashindex ON fingerprints (hash1(244));"

	sqlToDo = [createObjectTable,createEventTable,createFixityTable,createChecksumIndex,
			createLTOschemaTable,createLTOidIndex,createLTOcolumnIndex,
			createObjectCharsTable,createFingerprintsTable,createHashIndex]

	# preexistingDB = check_db_exists()
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
	grantPrivsSQL = "GRANT ALL PRIVILEGES ON {}.* TO %s@%s;".format(pymm_db)
	# print(createUserSQL)
	# print(grantPrivsSQL)
	try:
		connect = db.DB('root')
		connect.connect()
		connect.query(createUserSQL,newUser,userIP,userPass)
		connect.query(grantPrivsSQL,newUser,userIP)
		connect.close_cursor()
		connect.close_connection()
		# print("\n\nIMPORTANT!!\nTO FINISH USER SETUP, TYPE THIS TERMINAL COMMAND ON THE ~USER'S~ COMPUTER:\n"
		# 	"mysql_config_editor set --login-path="+newUser+"_db_access --host="+userIP+" --user="+newUser+" --password=\n"
		# 	"\nAND THEN TYPE IN THE USER PASSWORD ("+userPass+")\n"
		# 	"AND ~THEN~ GO INTO THE USER'S LOCAL PYMMCONFIG AND ENTER THESE VALUES:\n"
		# 	"pymm_db_name = "+newUser+"_db_access\n"
		# 	"pymm_db = "+pymm_db+"\n")
		pymmconfig.set_value("database users",newUser,userPass)
	except:
		print("stupid error")
		sys.exit()

def main():
	if mode == 'database':
		create_db()
	elif mode == 'user':
		create_user()
	elif mode == 'check':
		check_db_exists()
	else:
		print("PLEASE PICK A MODE TO RUN THIS SCRIPT IN: '-m database' TO CREATE A DATABASE,\nOR -m user TO ADD USER(S).")
		sys.exit()

if __name__ == '__main__':
	args = set_args()
	mode = args.mode
	main()
