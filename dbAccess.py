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

# THIS ISN'T WORKING WHEN CALLING CREATEPYMMDB FROM COMMAND LINE.
# THERE IS A CONFLICT WITH THE ARGPARSE OF CREATEPYMMDB.PY
# FOR NOW I WILL JUST SET DEFAULT VALUES OF ROOT AND PYMM_DB

# def set_args():
# 	parser = argparse.ArgumentParser()
# 	parser.add_argument('-d','--database',default='pymm_db',dest='database',help='name of the db to connect to/query')
# 	parser.add_argument('-u','--user',default='root',dest='user',help='user name for mysql connection')
# 	#					# options should be `root` or `user_config` for a user's instance
# 	return parser.parse_args()
	# database = args.database
	# if database == None:
	# 	database = 'pymm_db'
	# user = args.user
	# if user == None:
	# 	user = 'root'

parser = argparse.ArgumentParser()
parser.add_argument('-d','--database',default='pymm_db',dest='database',help='name of the db to connect to/query')
parser.add_argument('-u','--user',default='root',dest='user',help='user name for mysql connection')
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
	# args = set_args()
	# database = args.database
	# user = args.user

	def __init__(self,database=database,user=user):
		self.db = database
		self.user = user
	
	# def set_args():
	# 	parser = argparse.ArgumentParser()
	# 	parser.add_argument('-d','--database',default='pymm_db',dest='database',help='name of the db to connect to/query')
	# 	parser.add_argument('-u','--user',default='root',dest='user',help='user name for mysql connection')
	# 	#					# options should be `root` or `user_config` for a user's instance
	# 	return parser.parse_args()


	def connect(self):
		# create a connection using root ... 
		if user == 'root':
			pw = getpass.getpass(prompt="enter password for mysql root:")
			self.connection = mysql.connector.connect(host='localhost',user='root',password=pw)
			return self.connection
		# ... or a designated user if running locally
		else:
			optionFile = os.path.expanduser('~/mylogin.cnf')
			self.connection = mysql.connector.connect(option_files=optionFile)
			return self.connection

	def query(self, sql,*args):
		
		cursor = None
		try:
			# self.connect()
			self.connection.get_warnings = True
			cursor = self.connection.cursor()
			cursor.execute(sql,*args)
			return cursor
		except mysql.connector.Error as e:
			# @fixme -- setting `get_warnings` to true I *think* grabs and prints out mysql.connector errors, but not all?
			# https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-fetchwarnings.html
			# print(cursor.fetch_warnings())
			print(e)
			return cursor
			# self.connect()
			# cursor = self.connection.cursor()
			# cursor.execute(sql)

	def close_cursor(self):
		self.connection.cursor().close()

	def close_connection(self):
		self.connection.close()

if __name__ == '__main__':
	set_args()
	# a = DB()
	# print(a.user)