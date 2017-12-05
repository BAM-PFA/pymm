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

today = date.today()

################################################################
# read the config.ini file, or make one if it doesn't exist
# THIS LOGIC SHOULD REALLY BE IN PYMMFUNCTIONS
# OR EVEN IN CONFIG.PY AND CALLED AT THE START OF EACH MICROSERVICE SCRIPT
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(scriptDirectory,'..','config/config.ini')
globalConfig = configparser.ConfigParser()
if os.path.isfile(configPath):
	globalConfig.read(confPath)
else:
	print("the configuration file doesn't exist yet... hang on ...")
	with open(configPath,'w+') as configPath:
		globalConfig.read(configPath)

requiredPaths = ['outdir_ingestfile','aip_storage','resourcespace_deliver']
for path in requiredPaths:
	if globalConfig['paths'][path] == '': # config settings
		print("You did not set "+path+". Please edit the config file or\n\
			use '--output-path' to set the ingestfile output path\n\
			use '--aip-path' to set the AIP output path\n\
			use '--resourcespace_deliver' to set the resourcespace output path")
		exit()
################################################################

# set interactivemode state if command line flag is set
interactiveMode = argparse.ArgumentParser().add_argument('--interactive',action='store_true')
# set ingest variables
inputFilepath = argparse.ArgumentParser().add_argument('--inputFilepath')
filename = os.path.basename(inputFilepath)
mediaID = argparse.ArgumentParser().add_argument('--mediaID')
operator = argparse.ArgumentParser().add_argument('--operator')

# Quit if there are required variables missing
for flag in inputFilepath, mediaID, operator:
	if flag = '':
		print("YOU FORGOT TO SET "+flag+". It is required. Try again, but set "+flag+" with the flag --"+flag)
		exit()

# NOT TOTALLY CLEAR WHAT THE POINT OF THIS IS IN THE ORIGINAL
# SEEMS LIKE IT'S RARELY USED, IE IF THE FILE NO LONGER EXISTS?
def cleanup():
	status = 'abort'
	log(mediaID,status,"Something went wrong and the process was aborted.")
	exit()

# SET UP AIP DIRECTORY PATHS...
packageDirDict = {
	"packageOutputDir":"globalConfig['paths']['outdir_ingestfile']+mediaID+'/'",
	"packageMetadataDir":"packageOutputDir+'metadata/'",
	"packageFileMetadataDir":"packageMetadataDir+'fileMeta/'",
	"packageMetadataObjects":"packageFileMetadataDir+'objects/'",
	"packageLogDir":"packageMetadataDir+'logs/'",
}

# ... SEE IF THE TOP DIR EXISTS ...
if os.path.isdir(packageDirDict['packageOutputDir']):
	print("It looks like "+mediaID+" was already ingested. If you want to replace \
		the existing package please delete the package at \r\
		"+packageDirDict['packageOutputDir']+"\r\
		first and then try again.")
	exit()

# ... AND OTHERWISE MAKE THEM ALL
for key in packageDirDict:
	os.mkdir(key)

# set up a logfile for this ingest instance
ingestLogPath = packageDirDict['packageLogDir']+mediaID+'_'+today+'.txt'

if not is_video(mediaID):
	status = 'warning'
	message = "WARNING: "+mediaID+" is not recognized as a video file."
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
	filePath = input("Please drag the file to ingest into the terminal window: ")
	fileName = os.path.basename(filePath)
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

