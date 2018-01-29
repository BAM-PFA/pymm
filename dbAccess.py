#!/usr/bin/env python3
# defines a class for accessing the pymm PREMIS databse

import os
import sys
import argparse
import getpass
# nonstandard libraries:
try:
	import mysql.connector
except ImportError:
	print("Try installing mysql connector/python again.")
	sys.exit()
# check this out for mysql.connector install: https://gist.github.com/stefanfoulis/902296/f466a8dba3a75c172ac88627298f18eaaf0aa4c3
# brew install mysql-connector-c
# pip3 install mysql-connector
# pip3 error  ``Unable to find Protobuf include directory.`` --> `brew install protobuf`
# and if that still doesn't work try pip install mysql-connector==2.1.6

##################
#   INIT ARGS
#
parser = argparse.ArgumentParser()
parser.add_argument('-d','--database',help='name of the db to connect to/query')
parser.add_argument('-u','--user',help='user name for mysql connection')
#					# options should be `root` or `user_config` for a user's instance
args = parser.parse_args()
database = args.database
if database == None:
	database = 'pymm_db'
user = args.user
if user == None:
	user = 'root'
#
#
##################

class DB:
	connection = None
	cursor = None
	def __init__(self,database=database,user=user):
		self.db = database
		self.user = user
	
	def connect(self):
		if user == 'root':
			pw = getpass.getpass(prompt="enter password for mysql root:")
			self.connection = mysql.connector.connect(host='localhost',user='root',password=pw,connection_timeout=30)
		else:
			optionFile = os.path.expanduser('~/mylogin.cnf')
			self.connection = mysql.connector.connect(option_files=optionFile)

	def query(self, sql):
		cursor = None
		try:
			# self.connect()
			self.connection.get_warnings = True
			cursor = self.connection.cursor()
			cursor.execute(sql)
			# for row in cursor:
			# 	print(row)
			return cursor
		except:
			# @fixme
			# https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-fetchwarnings.html
			# print(cursor.fetch_warnings())
			print('errr')
			return 'ooops'
			# self.connect()
			# cursor = self.connection.cursor()
			# cursor.execute(sql)
		# return cursor

	def close_cursor(self):
		self.connection.cursor().close()

	def close_connection(self):
		self.connection.close()

