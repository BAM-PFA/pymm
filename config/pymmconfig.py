#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices
# (https://github.com/mediamicroservices/mm)
#
# run `pymmconfig` once at setup to initialize config settings
# or run it again to change or add values

import os
import sys
import configparser

configPath = os.path.dirname(os.path.abspath(__file__))+'/config.ini'
if not os.path.isfile(configPath):
	print('theres no system config file yet...')
	open(configPath,'x')
	with open(configPath,'w+') as config:
		config.write("[paths]\routdir_ingestfile:\raip_storage:\rresourcespace_deliver:\rpymm_scriptdir:\
			\r\r[database settings]\rpymm_db:\rpymm_db_user_profile:\rpymm_db_name:\
			\r\r[logging]\rpymm_log_dir:")
config = configparser.SafeConfigParser()
config.read(configPath)

def set_value(section, optionToSet):
	print("So you want to set "+optionToSet)
	newValue = input("Please enter a value for "+optionToSet+": ")
	config.set(section,optionToSet,newValue)
	with open(configPath,'w') as out:
		config.write(out)

def select_option():
	more = ''
	optionToSet = input("Enter the configuration option you want to set: ")
	matchingSections = 0

	for section in config.sections():
		if config.has_option(section,optionToSet):
			matchingSection = section
			matchingSections += 1
			set_value(section,optionToSet)
		else:
			pass
	
	if matchingSections == 0:
		print("\nOops, there is no option matching "+optionToSet+". Check your spelling and try again.\n")
	more = input("Type 'q' to quit or any other key to select another option to set: ")
	ask_more(more)

def ask_more(more):
	if more == 'q':
		sys.exit(0)
	else:
		select_option()

with open(configPath, 'r+') as conf:
	print('THIS IS WHAT THE CONFIG FILE LOOKS LIKE NOW.')
	for line in conf.readlines():
		print(line)
	print("IF YOU WANT TO CHANGE ANYTHING, LET'S GO!!")

	select_option()

