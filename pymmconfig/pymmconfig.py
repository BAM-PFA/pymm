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

def make_config(configPath):
	if not os.path.isfile(configPath):
		print('theres no system config file yet... hang on...')
		open(configPath,'x')
		with open(configPath,'w+') as config:
			config.write('''[paths]\noutdir_ingestfile:\naip_storage:\nresourcespace_deliver:\npymm_scriptdir:\
				\n\n[database settings]\nuse_db:\npymm_db:\npymm_db_access:\npymm_db_address:\
				\n\n[logging]\npymm_log_dir:\
				\n\n[mediaconch format policies]\nfilm_scan_master:\nvideo_capture_master:\nmagnetic_video_mezzanine:\nfilm_scan_mezzanine:\nlow_res_proxy:
				''')

def set_value(section, optionToSet,newValue=None):
	if newValue == None:
		print("So you want to set "+optionToSet)
		# the replace() call is a kind of stupid hack fix to get around paths with spaces getting an unnecessary escape slash
		# when you drag a folder into the terminal on Mac.... 
		# @fixme
		newValue = input("Please enter a value for "+optionToSet+": ").rstrip().replace("\ "," ")  
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
	more = input("Type 'q' to quit or hit enter to select another option to set: ")
	ask_more(more)

def ask_more(more):
	if more == 'q':
		with open(configPath, 'r+') as conf:
			print('THIS IS WHAT THE CONFIG FILE LOOKS LIKE NOW.')
			for line in conf.readlines():
				print(line.rstrip())
			print("NOW EXITING. BYE!!")
		sys.exit()
	else:
		select_option()

configPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'config.ini')
# configPath = 'config.ini'
make_config(configPath)
config = configparser.SafeConfigParser()
config.read(configPath)

def main():
	with open(configPath, 'r+') as conf:
		print('THIS IS WHAT THE CONFIG FILE LOOKS LIKE NOW.')
		for line in conf.readlines():
			print(line.rstrip())
		print("IF YOU WANT TO CHANGE ANYTHING, LET'S GO!!")

		select_option()

if __name__ == '__main__':
	main()
