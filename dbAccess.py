#!/usr/bin/env python3
# defines a class for accessing the pymm PREMIS databse

import os
import sys
import getpass
# nonstandard libraries:
try:
	import mysql.connector
except ImportError:
	print("Try installing mysql connector/python again.")
	sys.exit()
# local modules:
import pymmFunctions
# check this out for mysql.connector install: https://gist.github.com/stefanfoulis/902296/f466a8dba3a75c172ac88627298f18eaaf0aa4c3
# brew install mysql-connector-c
# pip3 install mysql-connector
# pip3 error  ``Unable to find Protobuf include directory.`` --> `brew install protobuf`
# and if that still doesn't work try pip3 install mysql-connector==2.1.6

config = pymmFunctions.read_config()
pymmDB = config['database settings']['pymm_db']
# set db name to None in case it doesn't exist yet
if pymmDB in ('',None):
	pymmDB = None

class DB:
	connection = None
	cursor = None

	def __init__(self,user):
		self.user = user

	def connect(self):
		# create a connection using root ... 
		if self.user == 'root':
			pw = getpass.getpass(prompt="enter password for mysql root:")
			self.connection = mysql.connector.connect(
				host='localhost',
				user='root',
				password=pw
				)
			return self.connection
		# ... or a designated user
		# database parameter is going to default to 'pymmDB' value read 
		# from config, or None in case it isn't set in which case the connection will fail?
		else:
			# optionFile = os.path.expanduser('~/.my.cnf')
			optionFile = os.path.expanduser('~/.mylogin.cnf')
			optionGroup = "{}_db_access".format(self.user)
			try:
				self.connection = mysql.connector.connect(
					option_files=optionFile,
					option_groups=optionGroup,
					database=pymmDB
					)
				return self.connection
			except:
				try: 
					pw = config['database users'][self.user]
					self.connection = mysql.connector.connect(
						host='localhost',
						user=self.user,
						password=pw,
						database=pymmDB
						)
					return self.connection
				except:
					print(
						"YOU HAVE SOME CONNECTION PROBLEMS. \n"
						"EITHER THE login-path SETTING IS NOT FUNCTIONING \n"
						"OR YOU NEED TO CHECK YOUR PASSWORD SETTINGS. \n"
						"START BY LOOKING AT config.ini"
						)

	def query(self, sql,*args):
		cursor = None
		# print(args)
		self.connection.autocommit = True
		try:
			self.connection.get_warnings = True
			cursor = self.connection.cursor()
			cursor.execute(sql,args)
			# for item in cursor:
			# 	print(item)
			# try:
			# 	self.connection.commit()
			# except:
			# 	print("can't commit {}".format(sql))
			# 	pass
		except mysql.connector.Error as e:
			# @fixme -- setting `get_warnings` to true I *think* grabs and prints out mysql.connector errors, but not all?
			# https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-fetchwarnings.html
			# print(cursor.fetch_warnings())
			print("Error! {}".format(e))
		
		return cursor

	def close_cursor(self):
		self.connection.cursor().close()

	def close_connection(self):
		self.connection.close()

if __name__ == '__main__':
	print(user)
