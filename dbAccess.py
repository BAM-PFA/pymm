#!/usr/bin/env python3
import os
import sys
import argparse
import getpass
try:
	import mysql.connector
except ImportError:
	print("Try installing mysqlclient again.")
	sys.exit()

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
			cursor = self.connection.cursor()
			cursor.execute(sql)
			return cursor
		except:
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

