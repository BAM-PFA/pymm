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
# check this out for mysql.connector install: https://gist.github.com/stefanfoulis/902296/f466a8dba3a75c172ac88627298f18eaaf0aa4c3
# brew install mysql-connector-c
# pip3 install mysql-connector
# pip3 error  ``Unable to find Protobuf include directory.`` --> `brew install protobuf`
# and if that still doesn't work try pip3 install mysql-connector==2.1.6

class DB:
	connection = None
	cursor = None

	def __init__(self,user):
		self.user = user

	def connect(self):
		# create a connection using root ... 
		if self.user == 'root':
			pw = getpass.getpass(prompt="enter password for mysql root:")
			self.connection = mysql.connector.connect(host='localhost',user='root',password=pw)
			return self.connection
		# ... or a designated user if running locally
		else:
			optionFile = os.path.expanduser('~/mylogin.cnf')
			try:
				self.connection = mysql.connector.connect(option_files=optionFile)
				return self.connection
			except:
				print("YOU DON'T SEEM TO HAVE SET UP THE LOGIN PATH FILE FOR USER "+self.user+".TRY AGAIN.\n"
					"MAYBE TRY RUNNING createPymmDB.py -m user ON THE DB HOST MACHINE,\n"
					"OR CHECK OUT THE pymmconfig.ini FILE ON THE USER COMPUTER (WHICH SHOULD BE THIS COMPUTER...).")

	def query(self, sql,*args):
		cursor = None
		try:
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

	def close_cursor(self):
		self.connection.cursor().close()

	def close_connection(self):
		self.connection.close()

if __name__ == '__main__':
	print(user)
