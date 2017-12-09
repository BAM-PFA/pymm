#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices

import sys
import subprocess
import os
import os.path
from ffmpy import FFprobe, FFmpeg
import argparse
import configparser
from datetime import date

from pymmFunctions import *
pymmDirectory = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0,localContextDirectory+'/config')
# from config import config
configPath = os.path.join(pymmDirectory,'config/config.ini') 
globalConfig = configparser.SafeConfigParser()
globalConfig.read(configPath)

today = date.today()

# COMMAND LINE ARGUMENTS
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

if inputFilepath:
	filename = os.path.basename(inputFilepath)

requiredPaths = ['inputFilepath','mediaID','operator']

if interactiveMode == False:
	# Quit if there are required variables missing
	missingPaths = 0
	for flag in requiredPaths:
		if getattr(args,flag) == None:
			print("YOU FORGOT TO SET "+flag+". It is required. Try again, but set "+flag+" with the flag --"+flag)
			missingPaths += 1
	if missingPaths > 0:
		exit()
else:
	# ask operator/mediaID/input file
	operator = input("Please enter your name: ")
	inputFilepath = input("Please drag the file you want to ingest into this window___")
	mediaID = input("Please enter a valid mediaID for the input file (only use 'A-Z' 'a-z' '0-9' '_' or '-') : ")

# NOT TOTALLY CLEAR WHAT THE POINT OF THIS IS IN THE ORIGINAL
# SEEMS LIKE IT'S RARELY USED, IE IF THE FILE NO LONGER EXISTS?
def cleanup():
	status = 'abort'
	log(mediaID,status,"Something went wrong and the process was aborted.")
	exit()

# SET UP AIP DIRECTORY PATHS FOR INGEST...
# packageDirDict = {
# 	"packageOutputDir":globalConfig['paths']['outdir_ingestfile']+'/'+mediaID+'/',
# 	"packageMetadataDir":packageOutputDir+'metadata/',
# 	"packageFileMetadataDir":packageMetadataDir+'fileMeta/',
# 	"packageMetadataObjects":packageFileMetadataDir+'objects/',
# 	"packageLogDir":packageMetadataDir+'logs/',
# }
packageOutputDir = globalConfig['paths']['outdir_ingestfile']+'/'+mediaID+'/'
packageObjectDir = packageOutputDir+'objects/'
packageMetadataDir = packageOutputDir+'metadata/'
packageFileMetadataDir = packageMetadataDir+'fileMeta/'
packageMetadataObjects = packageFileMetadataDir+'objects/'
packageLogDir = packageMetadataDir+'logs/'
packageDirs = [packageOutputDir,packageObjectDir,packageMetadataDir,packageFileMetadataDir,packageMetadataObjects,packageLogDir]

# ... SEE IF THE TOP DIR EXISTS ...
if os.path.isdir(packageOutputDir):
	print("It looks like "+mediaID+" was already ingested.\
If you want to replace the existing package please delete the package at \
"+packageOutputDir+"\n\
first and then try again.")
	exit()

# ... AND OTHERWISE MAKE THEM ALL
for directory in packageDirs:
	os.mkdir(directory)

# set up a logfile for this ingest instance
ingestLogPath = packageLogDir+mediaID+'_'+str(today)+'.txt'
with open(ingestLogPath,'x') as log:
	print('Laying a log at '+ingestLogPath)
is_video(inputFilepath)

if not is_video(inputFilepath):
	status = 'warning'
	message = "WARNING: "+filename+" is not recognized as a video file."
	print(message)
	log(mediaID,status,message)
	if interactiveMode:
		stayOrGo = input("If you want to quit press 'q' and enter, otherwise press any other key:")
		if stayOrGo == 'q':
			exit()
		else:
			pass
	else:
		pass

if interactiveMode:
	# ask operator/mediaID/input file
	operator = input("Please enter your name: ")
	inputFilepath = input("Please drag the file to ingest into the terminal window: ")
	filename = os.path.basename(filePath)
	mediaID = input("Please enter a MEDIA ID for this file (A-Z a-z 0-9 _ and - *ONLY*): ")

	# check regex for mediaID

	# cleanup strategy
	cleanupStrategy = input("Do you want to clean up stuff when you are done? yes/no ")
	if cleanupStrategy == 'yes':
		cleanupStrategy = True
	else:
		cleanupStrategy = False

	# crop decision

	# formula

	# blackframe test

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

