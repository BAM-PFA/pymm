#!/usr/bin/env python3
import os
import sys
import argparse
import getpass
try:
	import mysql.connector
except ImportError:
	print("Try installing mysqlclient again.")

from pathlib import Path
home = str(Path.home())
import subprocess

# optionfile = os.path.join(home,'.my.cnf')
pw = getpass.getpass(prompt="enter password for mysql root:")

cnx = mysql.connector.connect(host='localhost',user='root',password=pw)


cursor = cnx.cursor()

d = cursor.execute("SHOW DATABASES;")
db = cursor.fetchall()
print(db)