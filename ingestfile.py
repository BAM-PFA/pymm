#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices
# (https://github.com/mediamicroservices/mm)
#
# `ingestfile` takes an input a/v file, transcodes a derivative,
# produces/extracts some metadata, creates fixity checks,
# and packages the whole lot in an OAIS-like Archival Information Package
#
# @fixme = stuff to do


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
import makederivs
import makeMetadata

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
mode = parser.add_argument('-x','--interactiveMode',help='enter interactive mode for command line usage',action='store_true')
parser.add_argument('-i','--inputFilepath',help='path of input file')
parser.add_argument('-m','--mediaID',help='mediaID for input file')
parser.add_argument('-u','--operator',help='name of the person doing the ingest')
parser.add_argument('-t','--ingest_type',choices=['film scan','video transfer'],default='video transfer',help='type of file being ingested: film scan, video xfer')
parser.add_argument('-o','--output_path',help='output path for ingestfile')
parser.add_argument('-a','--aip_path',help='destination for Archival Information Package')
parser.add_argument('-r','--resourcespace_deliver',help='path for resourcespace proxy delivery')
parser.add_argument('-d','--database_reporting',help='report preservation metadata/events to database',action='store_true')

args = parser.parse_args()
# print(args)
interactiveMode = args.interactiveMode
inputFilepath = args.inputFilepath
mediaID = args.mediaID
operator = args.operator
output_path = args.output_path
aip_path = args.aip_path
resourcespace_deliver = args.resourcespace_deliver
report_to_db = args.database_reporting
ingest_type = args.ingest_type
cleanupStrategy = True

########################################################

requiredPaths = ['inputFilepath','mediaID','operator']

if interactiveMode == False:
	# Quit if there are required variables missing
	missingPaths = 0
	for flag in requiredPaths:
		if getattr(args,flag) == None:
			print('''
				CONFIGURATION PROBLEM:\n
				YOU FORGOT TO SET '''+flag+'''. It is required.\n
				Try again, but set '''+flag+''' with the flag --'''+flag
				)
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


# SET UP AIP DIRECTORY PATHS FOR INGEST...
# @fixme REDO THESE WITH OS.PATH.JOIN
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
		It looks like '''+mediaID+''' was already ingested.
		If you want to replace the existing package please delete the package at
		'''+packageOutputDir+'''
		and then try again.
		''')
	sys.exit()

# ... AND OTHERWISE MAKE THEM ALL
for directory in packageDirs:
	os.mkdir(directory)

# set up a logfile for this ingest instance
ingestLogPath = packageLogDir+mediaID+'_'+str(today)+'.txt'
with open(ingestLogPath,'x') as ingestLog:
	print('Laying a log at '+ingestLogPath)
ingest_log(ingestLogPath,mediaID,filename,operator,'start','start')	

# INSERT DATABASE RECORD FOR THIS INGEST (log 'ingestion start')

# check if the input is a video file
if not is_video(inputFilepath):
	is_av = False
	status = 'warning'
	message = "WARNING: "+filename+" is not recognized as a video file."
	print(message)
	ingest_log(ingestLogPath,mediaID,filename,operator,message,status)
	if not is_audio(inputFilepath):
		status = 'warning'
		message = "WARNING: "+filename+" is not recognized as an audio file."
		print(message)
		ingest_log(ingestLogPath,mediaID,filename,operator,message,status)

		if interactiveMode:
			stayOrGo = input("If you want to quit press 'q' and hit enter, otherwise press any other key:")
			if stayOrGo == 'q':
				sys.exit()
				# CLEANUP AND LOG THIS @fixme
			else:
				pass
		else:
			print("Check your file and come back later. Now exiting. Bye!")
			sys.exit()

if interactiveMode:
	# cleanup strategy
	cleanupStrategy = input("Do you want to clean up stuff when you are done? yes/no : ")
	if cleanupStrategy in yes:
		cleanupStrategy = True
	elif cleanupStrategy in no:
		cleanupStrategy = False
	else:
		cleanupStrategy = False
		print("Sorry, your answer didn't make sense so we will just leave things where they are.")


# LOG THAT WE ARE STARTING
pymm_log(filename,mediaID,operator,'','STARTING')

# WRITE VARIABLES TO LOG

# CHECK INPUT FILE AGAINST MEDIACONCH POLICIES

# RSYNC THE FILE TO WHERE IT BELONGS

# MAKE DERIVS
derivType = 'resourcespace'
# NOT CLEAR YET OF THE BEST WAY TO CALL THE DERIV CREATION FUNCTIONS
# I.E. SHOULD I CALL THEM HERE OR IN makederivs AND JUST PASS PARAMETERS FROM HERE
ffmpegMiddleOptions = makederivs.set_middle_options(derivType)

# ffmpegCommand = FFmpeg(
# 	inputFilepath
# 	# YADDA YADDA
# 	ffmpegMiddleOptions
# 	)

if ingest_type == 'film scan':
	derivType = 'mezzanine'
	ffmpegMiddleOptions = makederivs.set_middle_options(derivType)

# CHECK DERIVS AGAINST MEDIACONCH POLICIES

# MAKE METADATA
makeMetadata.get_mediainfo_report(inputFilepath,packageMetadataDir)

# DO CHECKSUMS

# FINISH LOGGING

# RSYNC TO AIP STAGE

# VERIFY PACKAGE CHECKSUM

# CLEANUP
if cleanupStrategy == True:
	print("LET'S CLEEEEEAN!")
else:
	print("BUH-BYE")