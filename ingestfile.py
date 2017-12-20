#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices
# (https://github.com/mediamicroservices/mm)
#
# `ingestfile` takes an input a/v file, transcodes a derivative,
# produces/extracts some metadata, creates fixity checks,
# and packages the whole lot in an OAIS-like Archival Information Package

import sys
import subprocess
import os
import os.path
from ffmpy import FFprobe, FFmpeg
import argparse
import configparser
from datetime import date
import pymmFunctions
from pymmFunctions import *

pymmDirectory = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(pymmDirectory,'config','config.ini') 
globalConfig = configparser.SafeConfigParser()
globalConfig.read(configPath)

today = date.today()
now = time.strftime("%Y-%m-%d_%H:%M:%S")
yes = ('YES','Yes','yes','y','Y')
no = ('NO','No','no','n','N')

########################################################
#
#      SET COMMAND LINE ARGUMENTS
#
parser = argparse.ArgumentParser()
# set interactive mode state if command line flag is set
mode = parser.add_argument('-x','--interactiveMode',help='enter interactive mode for command line usage',action='store_true')
# set ingest variables
parser.add_argument('-i','--inputFilepath',help='path of input file')
parser.add_argument('-m','--mediaID',help='mediaID for input file')
parser.add_argument('-u','--operator',help='name of the person doing the ingest')
parser.add_argument('-o','--output_path',help='output path for ingestfile')
parser.add_argument('-a','--aip_path',help='destination for Archival Information Package')
parser.add_argument('-r','--resourcespace_deliver',help='path for resourcespace proxy delivery')

args = parser.parse_args()
# print(args)
interactiveMode = args.interactiveMode
inputFilepath = args.inputFilepath
mediaID = args.mediaID
operator = args.operator
output_path = args.output_path
aip_path = args.aip_path
resourcespace_deliver = args.resourcespace_deliver

########################################################

requiredPaths = ['inputFilepath','mediaID','operator']

if interactiveMode == False:
	# Quit if there are required variables missing
	missingPaths = 0
	for flag in requiredPaths:
		if getattr(args,flag) == None:
			print('''
				CONFIGURATION PROBLEM:\n
				YOU FORGOT TO SET "+flag+". It is required.\n
				Try again, but set "+flag+" with the flag --"+flag
				''')
			missingPaths += 1
	if missingPaths > 0:
		sys.exit()
else:
	# ask operator/mediaID/input file
	operator = input("Please enter your name: ")
	inputFilepath = input("Please drag the file you want to ingest into this window___").rstrip()
	mediaID = input("Please enter a valid mediaID for the input file (only use 'A-Z' 'a-z' '0-9' '_' or '-') : ")

if inputFilepath:
	filename = os.path.basename(inputFilepath)

# NOT TOTALLY CLEAR WHAT THE POINT OF THIS IS IN THE ORIGINAL
# SEEMS LIKE IT'S RARELY USED, IE ONLY IF THE FILE NO LONGER EXISTS?
def cleanup():
	status = 'abort'
	log(mediaID,status,"Something went wrong and the process was aborted.")
	sys.exit()

# SET UP AIP DIRECTORY PATHS FOR INGEST...
packageOutputDir = globalConfig['paths']['outdir_ingestfile']+'/'+mediaID+'/'
packageObjectDir = packageOutputDir+'objects/'
packageMetadataDir = packageOutputDir+'metadata/'
packageFileMetadataDir = packageMetadataDir+'fileMeta/'
packageMetadataObjects = packageFileMetadataDir+'objects/'
packageLogDir = packageMetadataDir+'logs/'
packageDirs = [packageOutputDir,packageObjectDir,packageMetadataDir,packageFileMetadataDir,packageMetadataObjects,packageLogDir]

# ... SEE IF THE TOP DIR EXISTS ...
if os.path.isdir(packageOutputDir):
	print('''
		"It looks like "+mediaID+" was already ingested.\n
		If you want to replace the existing package please delete the package at
		\n"+packageOutputDir+"\nfirst and then try again."
		''')
	sys.exit(1)

# ... AND OTHERWISE MAKE THEM ALL
for directory in packageDirs:
	os.mkdir(directory)

# set up a logfile for this ingest instance
ingestLogPath = packageLogDir+mediaID+'_'+str(today)+'.txt'
with open(ingestLogPath,'x') as ingestLog:
	print('Laying a log at '+ingestLogPath)
ingest_log(ingestLogPath,mediaID,filename,operator,'start','start')	

# check if the input is a video file (DOUBLE CHECK THAT THIS ACTUALLY MAKES SENSE)
if not is_video(inputFilepath):
	status = 'warning'
	message = "WARNING: "+filename+" is not recognized as a video file."
	print(message)
	ingest_log(ingestLogPath,mediaID,filename,operator,message,status)
	if interactiveMode:
		stayOrGo = input("If you want to quit press 'q' and enter, otherwise press any other key:")
		if stayOrGo == 'q':
			sys.exit(0)
			# CLEANUP AND LOG THIS
		else:
			pass
	else:
		pass

if interactiveMode:
	# cleanup strategy
	cleanupStrategy = input("Do you want to clean up stuff when you are done? yes/no : ")
	if cleanupStrategy in yes:
		cleanupStrategy = True
	elif cleanupStrategy in no:
		cleanupStrategy = False
	else:
		cleanupStrategy = False
		print("Sorry, your answer didn't make sense so we will leave things where they are.")

	# crop decision
	# going to leave this blank for now, we wouldn't have a reason to crop... AFAIK

	# formula

	# blackframe test
	# also leave this blank, we won't trim anything

	# phasecheck test

	# ask queue

# LOG THAT WE ARE STARTING
pymm_log(filename,mediaID,operator,'','STARTING')

# WRITE VARIABLES TO LOG


# RSYNC THE FILE TO WHERE IT BELONGS

# MAKE DERIVS

# MAKE METADATA

# DO CHECKSUMS

# MAKE FINGERPRINT

# FINISH LOGGING

# RSYNC TO AIP STAGE

# CLEANUP

