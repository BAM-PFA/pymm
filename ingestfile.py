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
	# parser.add_argument('-a','--aip_path',help='destination for Archival Information Package') # uh, read this from config?
	parser.add_argument('-r','--resourcespace_deliver',help='path for resourcespace proxy delivery') # uh, read this from config?
	parser.add_argument('-d','--database_reporting',help='report preservation metadata/events to database',action='store_true')
	parser.add_argument('-z','--cleanup_originals',action='store_true',default=False,help='set this flag to delete source files after ingest')

	return parser.parse_args()
#
# END INTIALIZE COMMAND LINE ARGUMENTS
#
########################################################

def prep_package(mediaID):#,aip_override):
	'''
	Create a directory structure for a SIP (or are we calling it an AIP still?)
	'''
	packageOutputDir = os.path.join(pymmConfig['paths']['outdir_ingestfile'],mediaID)
	packageObjectDir = os.path.join(packageOutputDir,'objects')
	packageMetadataDir = os.path.join(packageOutputDir,'metadata')
	packageMetadataObjects = os.path.join(packageMetadataDir,'objects')
	packageLogDir = os.path.join(packageMetadataDir,'logs')
	packageDirs = [packageOutputDir,packageObjectDir,packageMetadataDir,packageMetadataObjects,packageLogDir]
	# see if there is an AIP delivery dir set to override the config destination.... 
	# if aip_override == None:
	# 	aip_path = pymmConfig['paths']['aip_staging']
	# else:
	# 	aip_path = aip_override
	# packageDirs.append(aip_path)
	
	# ... THEN SEE IF THE TOP DIR EXISTS ...
	if os.path.isdir(packageOutputDir):
		print('''
			It looks like '''+mediaID+''' was already ingested.
			If you want to replace the existing package please delete the package at
			'''+packageOutputDir+'''
			and then try again.
			''')
		sys.exit()

	# ... AND IF NOT, MAKE THEM ALL
	for directory in packageDirs:
		os.mkdir(directory)

	return packageDirs

def check_av_status(inputFilepath,interactiveMode,ingestLogBoilerplate):
	'''
	Check whether or not a file is recognized as an a/v file.
	If using interactive mode, ask whether to continue, otherwise quit.
	'''
	if not pymmFunctions.is_av(inputFilepath):
		_is_av = False
		message = "WARNING: "+ingestLogBoilerplate['filename']+" is not recognized as an a/v file."
		print(message)
		pymmFunctions.ingest_log(
			# message
			message,
			#status
			'warning',
			# ingest boilerplate
			**ingestLogBoilerplate
			)

	if interactiveMode:
		stayOrGo = input("If you want to quit press 'q' and hit enter, otherwise press any other key:")
		if stayOrGo == 'q':
			# CLEANUP AND LOG THIS @fixme
			sys.exit()
		else:
			if _is_av == False:
				pymmFunctions.ingest_log(
					# message
					message,
					# status
					'warning',
					# ingest boilerplate
					**ingestLogBoilerplate
					)
			pass
	else:
		message = ingestLogBoilerplate['filename']+" is an AV file, way to go."
		status = 'OK'
		pymmFunctions.ingest_log(
			# message
			ingestLogBoilerplate['filename']+" is an AV file, way to go.",
			# status
			'OK',
			# ingest boilerplate
			**ingestLogBoilerplate
			)
		pass

def reset_cleanup_choice():
	'''
	If using interactive mode ask whether or not to remove files when done.
	'''
	cleanupStrategy = input("Do you want to clean up stuff when you are done? yes/no : ")
	if pymmFunctions.boolean_answer(cleanupStrategy):
		cleanupStrategy = True
	else:
		cleanupStrategy = False
		print("Either you selected no or your answer didn't make sense so we will just leave things where they are when we finish.")
	return cleanupStrategy

def mediaconch_check(inputFilepath,ingest_type,ingestLogBoilerplate):
	'''
	Check input file against MediaConch policy.
	Needs to be cleaned up. Also, we don't have any policies set up yet...
	'''
	if ingest_type == 'film scan':
		policyStatus = pymmFunctions.check_policy(ingest_type,inputFilepath)
		if policyStatus:
			message = filename+" passed the MediaConch policy check."
			status = "ok"
		else:
			message = filename+" did not pass the MediaConch policy check."
			status = "not ok, but not critical?"

		pymmFunctions.ingest_log(
			# message
			message,
			# status
			status,
			# ingest boilerplate
			**ingestLogBoilerplate
			)

def move_input_file(processingVars):
	'''
	Put the input file into the package object dir.
	'''
	sys.argv = ['','-i'+processingVars['inputFilepath'],'-d'+processingVars['packageObjectDir'],'-L'+processingVars['packageLogDir']]
	moveNcopy.main()

def input_metadata(ingestLogBoilerplate,processingVars):
	pymmFunctions.ingest_log(
		# message
		"The input file MD5 hash is: "+makeMetadata.hash_file(processingVars['inputFilepath']),
		# status
		'OK',
		# ingest boilerplate
		**ingestLogBoilerplate
		)

	mediainfo = makeMetadata.get_mediainfo_report(processingVars['inputFilepath'],processingVars['packageMetadataObjects'])
	if mediainfo:
		pymmFunctions.ingest_log(
			# message
			"mediainfo XML report for input file written to metadata directory for package.",
			# status
			'OK',
			# ingest boilerplate
			**ingestLogBoilerplate
			)
	
	frameMD5 = makeMetadata.make_frame_md5(processingVars['inputFilepath'],processingVars['packageMetadataObjects'])
	if frameMD5 != False:
		pymmFunctions.ingest_log(
			# message
			"frameMD5 report for input file written to metadata directory for package",
			# status
			"OK",
			# ingest boilerplate
			**ingestLogBoilerplate
			)

def make_derivs(ingest_type,processingVars):
	'''
	Make derivatives based on ingest type....
	'''
	inputFilepath = processingVars['inputFilepath']
	packageObjectDir = processingVars['packageObjectDir']
	packageLogDir = processingVars['packageLogDir']
	packageMetadataObjects = processingVars['packageMetadataObjects']
	
	# WE'LL ALWAYS OUTPUT A RESOURCESPACE VERSION, SO INIT THE 
	# DERIVTYPE LIST WITH RESOURCESPACE
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



# RSYNC TO AIP STAGE
def move_sip(processingVars):
	packageOutputDir = processingVars['packageOutputDir']
	aip_staging = processingVars['aip_staging']
	mediaID = processingVars['mediaID']
	sys.argv = ['','-i'+packageOutputDir,'-d'+aip_staging,'-L'+os.path.join(aip_staging,mediaID)]
	moveNcopy.main()



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
	# aip_override = args.aip_path
	resourcespace_deliver = args.resourcespace_deliver
	report_to_db = args.database_reporting
	ingest_type = args.ingest_type
	cleanupStrategy = args.cleanup_originals
	aip_staging = pymmConfig['paths']['aip_staging']

	# 1) SET UP DIRECTORY PATHS FOR INGEST...
	packageOutputDir,packageObjectDir,packageMetadataDir,packageMetadataObjects,packageLogDir = prep_package(mediaID)#,aip_override)

	# 2) CHECK THAT REQUIRED VARS ARE DECLARED
	requiredVars = ['inputFilepath','mediaID','operator']
	if interactiveMode == False:
		# Quit if there are required variables missing
		missingVars = 0
		for flag in requiredVars:
			if getattr(args,flag) == None:
				print('''
					CONFIGURATION PROBLEM:
					YOU FORGOT TO SET '''+flag+'''. It is required.
					Try again, but set '''+flag+''' with the flag --'''+flag
					)
				missingVars += 1
		if missingVars > 0:
			sys.exit()
	else:
		# ask operator/mediaID/input file
		operator = input("Please enter your name: ")
		inputFilepath = input("Please drag the file you want to ingest into this window___").rstrip()
		inputFilepath = pymmFunctions.sanitize_dragged_linux_paths(inputFilepath)
		mediaID = input("Please enter a valid mediaID for the input file (only use 'A-Z' 'a-z' '0-9' '_' or '-') : ")

	if inputFilepath:
		filename = os.path.basename(inputFilepath)

	# SET UP A DICT FOR PROCESSING VARIABLES TO PASS AROUND
	processingVars =	{'operator':operator,'inputFilepath':inputFilepath,'mediaID':mediaID,'filename':filename,
						'packageOutputDir':packageOutputDir,'packageObjectDir':packageObjectDir,
						'packageMetadataDir':packageMetadataDir,'packageMetadataObjects':packageMetadataObjects,
						'packageLogDir':packageLogDir,'aip_staging':aip_staging}

	# 3) SET UP A LOG FILE FOR THIS INGEST
	ingestLogPath = os.path.join(packageLogDir,mediaID+'_'+pymmFunctions.timestamp('now')+'_ingestfile-log.txt')
	with open(ingestLogPath,'x') as ingestLog:
		print('Laying a log at '+ingestLogPath)

	ingestLogBoilerplate = {'ingestLogPath':ingestLogPath,'mediaID':mediaID,'filename':filename,'operator':operator}
	pymmFunctions.ingest_log(
		# message
		'start',
		# status
		'start',
		# ingest boilerplate
		**ingestLogBoilerplate
		)

	# 4) TELL THE SYSTEM LOG THAT WE ARE STARTING
	pymmFunctions.pymm_log(filename,mediaID,operator,'','STARTING')

	# 5) IF INTERACTIVE ASK ABOUT CLEANUP
	if interactiveMode:
		reset_cleanup_choice()

	# 6) INSERT DATABASE RECORD FOR THIS INGEST (log 'ingestion start')
	# @fixme

	# 7) CHECK THAT THE FILE IS ACTUALLY AN AV FILE (SHOULD THIS GO FIRST?)
	check_av_status(inputFilepath,interactiveMode,ingestLogBoilerplate)

	# 8) CHECK INPUT FILE AGAINST MEDIACONCH POLICIES
	mediaconch_check(inputFilepath,ingest_type,ingestLogBoilerplate)
	
	# 9) RSYNC THE INPUT FILE TO THE OUTPUT DIR
	move_input_file(processingVars)

	# 10) MAKE METADATA FOR INPUT FILE
	input_metadata(ingestLogBoilerplate,processingVars)

	# 11) MAKE DERIVATTIVES
	make_derivs(ingest_type,processingVars)

	# 12) CHECK DERIVS AGAINST MEDIACONCH POLICIES
	
	# 13) MOVE SIP TO AIP STAGING
	move_sip(processingVars)
	
	# FINISH LOGGING

	# VERIFY PACKAGE CHECKSUM
	packageVerified = False



if __name__ == '__main__':
	main()
