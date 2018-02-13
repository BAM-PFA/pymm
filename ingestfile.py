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
import argparse
# nonstandard libraries:
# from ffmpy import FFprobe, FFmpeg
# local modules:
import pymmFunctions
# from pymmFunctions import *
import makeDerivs
import moveNcopy
import makeMetadata

pymmConfig = pymmFunctions.read_config()
pymmFunctions.check_missing_ingest_paths(pymmConfig)

########################################################
#
#  INITIALIZE COMMAND LINE ARGUMENTS
#
def set_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-x','--interactiveMode',help='enter interactive mode for command line usage',action='store_true')
	parser.add_argument('-i','--inputFilepath',help='path of input file')
	parser.add_argument('-m','--mediaID',help='mediaID for input file')
	parser.add_argument('-u','--operator',help='name of the person doing the ingest')
	parser.add_argument('-t','--ingest_type',choices=['film scan','video transfer'],default='video transfer',help='type of file(s) being ingested: film scan, video xfer')
	parser.add_argument('-o','--output_path',help='output path for ingestfile') # uh, read this from config?
	parser.add_argument('-a','--aip_path',help='destination for Archival Information Package') # uh, read this from config?
	parser.add_argument('-r','--resourcespace_deliver',help='path for resourcespace proxy delivery') # uh, read this from config?
	parser.add_argument('-d','--database_reporting',help='report preservation metadata/events to database',action='store_true')
	parser.add_argument('-z','--cleanup_originals',action='store_true',default=False,help='set this flag to delete source files after ingest')

	return parser.parse_args()
#
# END INTIALIZE COMMAND LINE ARGUMENTS
#
########################################################

# SET UP DIRECTORY PATHS FOR INGEST...
def prep_package(mediaID):
	packageOutputDir = os.path.join(pymmConfig['paths']['outdir_ingestfile'],mediaID)
	packageObjectDir = os.path.join(packageOutputDir,'objects')
	packageMetadataDir = os.path.join(packageOutputDir,'metadata')
	packageMetadataObjects = os.path.join(packageMetadataDir,'objects')
	packageLogDir = os.path.join(packageMetadataDir,'logs')
	packageDirs = [packageOutputDir,packageObjectDir,packageMetadataDir,packageMetadataObjects,packageLogDir]
	if aip_path == None:
		aip_path = pymmConfig['paths']['aip_staging']

	# ... THEN SEE IF THE TOP DIR EXISTS ...
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

	return packageDirs

# INSERT DATABASE RECORD FOR THIS INGEST (log 'ingestion start')
# @fixme

def check_av_status(inputFilepath,*args):
	if not pymmFunctions.is_av(inputFilepath):
		_is_av = False
		status = 'warning'
		message = "WARNING: "+filename+" is not recognized as an a/v file."
		print(message)
		pymmFunctions.ingest_log(ingestLogPath,mediaID,filename,operator,message,status)

	if interactiveMode:
		stayOrGo = input("If you want to quit press 'q' and hit enter, otherwise press any other key:")
		if stayOrGo == 'q':
			sys.exit()
			# CLEANUP AND LOG THIS @fixme
		else:
			if _is_av == False:
				pymmFunctions.ingest_log(ingestLogPath,mediaID,filename)
			pass
	else:
		print("Check your file and come back later. Now exiting. Bye!")
		sys.exit()
def reset_cleanup_choice(interactiveMode):
	if interactiveMode:
		# cleanup strategy
		cleanupStrategy = input("Do you want to clean up stuff when you are done? yes/no : ")
		if pymmFunctions.boolean_answer(cleanupStrategy):
			cleanupStrategy = True
		else:
			cleanupStrategy = False
			print("Either you selected no or your answer didn't make sense so we will just leave things where they are when we finish.")
		return cleanupStrategy
	else:
		pass


# WRITE VARIABLES TO INGEST LOG

# CHECK INPUT FILE AGAINST MEDIACONCH POLICIES
def mediaconch_check(inputFilepath,*args):
	if ingest_type == 'film scan':
		policyStatus = pymmFunctions.check_policy(ingest_type,inputFilepath)
		if policyStatus:
			message = filename+" passed the MediaConch policy check."
			status = "ok"
		else:
			message = filename+" did not pass the MediaConch policy check."
			status = "not ok, but not critical?"

		pymmFunctions.ingest_log(ingestLogPath,mediaID,filename,operator,message,status)

# RSYNC THE INPUT FILE TO THE OUTPUT DIR
def move_input(inputFilepath,packageObjectDir,packageLogDir):
	# BUT FIRST GET A HASH OF THE ORIGINAL FILE (can i do this in php for our upload process?)
	sys.argv = ['','-i'+inputFilepath,'-d'+packageObjectDir,'-L'+packageLogDir]
	moveNcopy.main()

# MAKE METADATA FOR INPUT FILE
# log it first
def input_metadata(inputFilepath,*args):
	pymmFunctions.ingest_log(ingestLogPath,mediaID,filename,operator,"The input file MD5 hash is: "+makeMetadata.hash_file(inputFilepath),'OK')

	mediainfo = makeMetadata.get_mediainfo_report(inputFilepath,packageMetadataObjects)
	if mediainfo:
		pymmFunctions.ingest_log(ingestLogPath,mediaID,filename,operator,"mediainfo XML report for input file written to metadata directory for package.",'OK')
	frameMD5 = makeMetadata.make_frame_md5(inputFilepath,packageMetadataObjects)
	if frameMD5 != False:
		pymmFunctions.ingest_log(ingestLogPath,mediaID,filename,operator,"frameMD5 report for input file written to metadata directory for package","OK")

# MAKE DERIVS
# WE'LL ALWAYS OUTPUT A RESOURCESPACE VERSION, SO INIT THE 
# DERIVTYPE LIST WITH RESOURCESPACE
def make_derivs(ingest_type):
	derivTypes = ['resourcespace']
	deliveredDerivPaths = {}
	if ingest_type == 'film scan':
		derivTypes.append('filmMezzanine')
	elif ingest_type == 'video transfer':
		derivTypes.append('proresHQ')
	else:
		pass

	for derivType in derivTypes:
		sys.argv = ['','-i'+inputFilepath,'-o'+packageObjectDir,'-d'+derivType,'-r'+packageLogDir]
		deliveredDeriv = makeDerivs.main()
		deliveredDerivPaths[derivType] = deliveredDeriv

	for key,value in deliveredDerivPaths.items():
		# print([key,value])
		mdDest = os.path.join(packageMetadataObjects,key)
		if not os.path.isdir(mdDest):
			os.mkdir(mdDest)
		mediainfo = makeMetadata.get_mediainfo_report(value,mdDest)

# CHECK DERIVS AGAINST MEDIACONCH POLICIES

# FINISH LOGGING

# RSYNC TO AIP STAGE
def move_sip(packageOutputDir,aip_path,mediaID):
	sys.argv = ['','-i'+packageOutputDir,'-d'+aip_path,'-L'+os.path.join(aip_path,mediaID)]
	moveNcopy.main()

# VERIFY PACKAGE CHECKSUM
packageVerified = False

# CLEANUP
def do_cleanup(cleanupStrategy,packageVerified,inputFilepath,packageOutputDir,reason):
	if cleanupStrategy == True and packageVerified == True:
		print("LET'S CLEEEEEAN!")
		cleanup_package(inputFilepath,packageOutputDir,reason)
	else:
		print("BUH-BYE")


def main():
	args = set_args()
	interactiveMode = args.interactiveMode
	inputFilepath = args.inputFilepath
	mediaID = args.mediaID
	operator = args.operator
	output_path = args.output_path
	aip_path = args.aip_path
	resourcespace_deliver = args.resourcespace_deliver
	report_to_db = args.database_reporting
	ingest_type = args.ingest_type
	cleanupStrategy = args.cleanup_originals

	packageOutputDir,packageObjectDir,packageMetadataDir,packageMetadataObjects,packageLogDir = prep_package(mediaID)

	requiredPaths = ['inputFilepath','mediaID','operator']

	if interactiveMode == False:
		# Quit if there are required variables missing
		missingPaths = 0
		for flag in requiredPaths:
			if getattr(args,flag) == None:
				print('''
					CONFIGURATION PROBLEM:
					YOU FORGOT TO SET '''+flag+'''. It is required.
					Try again, but set '''+flag+''' with the flag --'''+flag
					)
				missingPaths += 1
		if missingPaths > 0:
			sys.exit()
	else:
		# ask operator/mediaID/input file
		operator = input("Please enter your name: ")
		inputFilepath = input("Please drag the file you want to ingest into this window___").rstrip()
		inputFilepath = pymmFunctions.sanitize_dragged_linux_paths(inputFilepath)
		mediaID = input("Please enter a valid mediaID for the input file (only use 'A-Z' 'a-z' '0-9' '_' or '-') : ")

	if inputFilepath:
		filename = os.path.basename(inputFilepath)

	# set up a logfile for this ingest instance
	ingestLogPath = packageLogDir+mediaID+'_'+pymmFunctions.timestamp('now')+'_ingestfile-log.txt'
	with open(ingestLogPath,'x') as ingestLog:
		print('Laying a log at '+ingestLogPath)
	ingestLogBoilerplate = [ingestLogPath,mediaID,filename,operator]
	pymmFunctions.ingest_log(ingestLogPath,mediaID,filename,operator,'start','start')


	# LOG THAT WE ARE STARTING
	pymmFunctions.pymm_log(filename,mediaID,operator,'','STARTING')

	# IF INTERACTIVE ASK ABOUT CLEANUP
	reset_cleanup_choice(interactiveMode)


if __name__ == '__main__':
	main()
