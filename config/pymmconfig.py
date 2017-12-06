#!/usr/bin/env python3

import os
import sys
import configparser

configPath = os.path.dirname(os.path.abspath(__file__))+'/config.ini'
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
		print("Oops, there is no option matching "+optionToSet+". Check your spelling and try again.")
		exit()

	more = input("Type 'q' to quit or any other key to select another option to set: ")
	ask_more(more)

def ask_more(more):
	if more == 'q':
		exit()
	else:
		select_option()

with open(configPath, 'r') as conf:
	print('THIS IS WHAT THE CONFIG FILE LOOKS LIKE NOW.')
	for line in conf.readlines():
		print(line)
	print("IF YOU WANT TO CHANGE ANYTHING, LET'S GO!!")

	select_option()

