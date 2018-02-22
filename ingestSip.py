#!/usr/bin/env python3
'''
`ingestSip` takes an input a/v file or directory of a/v files,
transcodes a derivative for each file,
produces/extracts some metadata,
creates fixity checks,
and packages the whole lot in an OAIS-like Archival Information Package

It can take a directory of files and concatenate them before performing
the above steps. Currently we'd only do that on reels/tapes that
represent parts of a whole.

@fixme = stuff to do
'''
import sys
import subprocess
import os
import argparse
import uuid
import json
# local modules:
import pymmFunctions
import makeDerivs
import moveNcopy
import makeMetadata
import concatFiles

# read in from the config file
config = pymmFunctions.read_config()
# check that paths required for ingest are declared in config.ini
pymmFunctions.check_missing_ingest_paths(config)

def set_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--inputFilepath',
		help='path of input file'
		)
	parser.add_argument(
		'-u','--operator',
		help='name of the person doing the ingest'
		)
	parser.add_argument(
		'-t','--ingestType',
		choices=['film scan','video transfer'],
		default='video transfer',
		help='type of file(s) being ingested: film scan, video xfer'
		)
	parser.add_argument(
		'-p','--makeProres',
		action='store_true',
		help='override whatever config default you have set '
			'and make a prores HQ mezzanine file'
		)
	parser.add_argument(
		'-c','--concat',
		action='store_true',
		help='try to concatenate files in an input directory'
		)
	parser.add_argument(
		'-d','--database_reporting',
		action='store_true',
		help='report preservation metadata/events to database'
		)
	parser.add_argument(
		'-x','--interactiveMode',
		action='store_true',
		help='enter interactive mode for command line usage'
		)
	parser.add_argument(
		'-z','--cleanup_originals',
		action='store_true',
		default=False,
		help='set this flag to delete source files after ingest'
		)

	return parser.parse_args()

def prep_package(tempID):
	'''
	Create a directory structure for a SIP
	'''
	packageOutputDir = os.path.join(config['paths']['outdir_ingestfile'],tempID)
	packageObjectDir = os.path.join(packageOutputDir,'objects')
	packageMetadataDir = os.path.join(packageOutputDir,'metadata')
	packageMetadataObjects = os.path.join(packageMetadataDir,'objects')
	packageLogDir = os.path.join(packageMetadataDir,'logs')
	packageDirs = [packageOutputDir,packageObjectDir,packageMetadataDir,packageMetadataObjects,packageLogDir]
	
	# ... SEE IF THE TOP DIR EXISTS ...
	if os.path.isdir(packageOutputDir):
		print('''
			It looks like '''+tempID+''' was already ingested.
			If you want to replace the existing package please delete the package at
			'''+packageOutputDir+'''
			and then try again.
			''')
		sys.exit()

	# ... AND IF NOT, MAKE THEM ALL
	for directory in packageDirs:
		os.mkdir(directory)

	return packageDirs

def sniff_input(inputFilepath,ingestUUID,concatChoice):
	'''
	Check whether the input path from command line is a directory
	or single file. If it's a directory, see if the user wanted
	to concatenate the files and do/don't concatenate.

	@fixme separate out the different activities from this function!
	'''

	inputType = pymmFunctions.dir_or_file(inputFilepath)
	# DO A SANITY CHECK ON FILENAMES IN AN INPUT DIRECTORY
	# EXIT IF THERE IS A DISCREPANCY (IF FILENAMES ARE TOO DIFFERENT)... 
	# WE MAY OR MAY NOT WANT TO LOOSEN THIS?
	if inputType == 'dir':
		outliers, outlierList = pymmFunctions.check_dir_filename_distances(inputFilepath)
		if outliers > 0: 
			print("Hey, there are "+str(outliers)+" files that seem like they might not belong in the input directory."
				"\nHere's a list:"
				"\n"+'\n'.join(outlierList)
				)
			sys.exit()

		# TRY CONCAT... 
		if concatChoice == True:
			sys.argv = 	['',
						'-i'+inputFilepath,
						'-d'+ingestUUID
						]
			if concatFiles.main():
				sys.exit()
		else:
			print('still testing out concat. input was directory so I QUIT.')
			sys.exit()
	
	else:
		print("input is a single file")
	return inputType

def check_av_status(inputFilepath,interactiveMode,ingestLogBoilerplate):
	'''
	Check whether or not a file is recognized as an a/v file.
	If it isn't and user declares interactive mode, ask whether to continue, otherwise quit.
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
	else:
		pymmFunctions.ingest_log(
			# message
			ingestLogBoilerplate['filename']+" is an AV file, way to go.",
			# status
			'OK',
			# ingest boilerplate
			**ingestLogBoilerplate
			)

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

def mediaconch_check(inputFilepath,ingestType,ingestLogBoilerplate):
	'''
	Check input file against MediaConch policy.
	Needs to be cleaned up. Also, we don't have any policies set up yet...
	'''
	if ingestType == 'film scan':
		policyStatus = pymmFunctions.check_policy(ingestType,inputFilepath)
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
	sys.argv = 	['',
				'-i'+processingVars['inputFilepath'],
				'-d'+processingVars['packageObjectDir'],
				'-L'+processingVars['packageLogDir']
				]
	moveNcopy.main()

def input_file_metadata(ingestLogBoilerplate,processingVars):
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

def make_derivs(processingVars):
	'''
	Make derivatives based on options declared in config...
	
	Based on discussions w Dave Taylor it makes more sense
	for our workflows to just have him make a mezzanine file 
	if he needs it. And otherwise there's no reason for us to 
	make and store a ProRes mezzanineby default.

	However, the option to create & deliver any number of derivs by default
	still exists in the config file.
	'''
	inputFilepath = processingVars['inputFilepath']
	packageObjectDir = processingVars['packageObjectDir']
	packageLogDir = processingVars['packageLogDir']
	packageMetadataObjects = processingVars['packageMetadataObjects']
	makeProres = processingVars['makeProres']
	ingestType = processingVars['ingestType']

	# WE'LL ALWAYS OUTPUT A RESOURCESPACE ACCESS FILE FOR VIDEO INGESTS,
	# SO INIT THE DERIVTYPES LIST WITH `RESOURCESPACE`
	if ingestType in ('film scan','video transfer'):
		derivTypes = ['resourcespace']
	deliveredDerivPaths = {}
	
	if pymmFunctions.boolean_answer(config['deriv delivery options']['proresHQ']):
	# if ingestType == 'film scan':
	# 	derivTypes.append('filmMezzanine')
	# elif ingestType == 'video transfer':
		derivTypes.append('proresHQ')
	elif makeProres == True:
		derivTypes.append('proresHQ')
	else:
		pass

	for derivType in derivTypes:
		sys.argv = 	['',
					'-i'+inputFilepath,
					'-o'+packageObjectDir,
					'-d'+derivType,
					'-r'+packageLogDir
					]
		deliveredDeriv = makeDerivs.main()
		deliveredDerivPaths[derivType] = deliveredDeriv

	for key,value in deliveredDerivPaths.items():
		mdDest = os.path.join(packageMetadataObjects,key)
		if not os.path.isdir(mdDest):
			os.mkdir(mdDest)
		mediainfo = makeMetadata.get_mediainfo_report(value,mdDest)

def move_sip(processingVars):
	packageOutputDir = processingVars['packageOutputDir']
	aip_staging = processingVars['aip_staging']
	tempID = processingVars['tempID']
	sys.argv = 	['',
				'-i'+packageOutputDir,
				'-d'+aip_staging,
				'-L'+os.path.join(aip_staging,tempID)]
	moveNcopy.main()

def do_cleanup(cleanupStrategy,packageVerified,inputFilepath,packageOutputDir,reason):
	if cleanupStrategy == True and packageVerified == True:
		print("LET'S CLEEEEEAN!")
		cleanup_package(inputFilepath,packageOutputDir,reason)
	else:
		print("BUH-BYE")

def main():
	# parse them args
	args = set_args()
	inputFilepath = args.inputFilepath
	operator = args.operator
	report_to_db = args.database_reporting
	ingestType = args.ingestType
	makeProres = args.makeProres
	concatChoice = args.concat
	cleanupStrategy = args.cleanup_originals
	interactiveMode = args.interactiveMode
	# read aip staging dir from config
	aip_staging = config['paths']['aip_staging']
	# make a uuid for the ingest
	ingestUUID = str(uuid.uuid4())
	# make a temp ID based on input path for the ingested object
	# this will get replaced by the ingest UUID during final package move ...?
	tempID = pymmFunctions.get_temp_id(inputFilepath)

	# SNIFF WHETHER THE INPUT IS A FILE OR DIRECTORY
	inputType = sniff_input(inputFilepath,ingestUUID,concatChoice)

	# 1) CREATE DIRECTORY PATHS FOR INGEST...
	packageOutputDir,packageObjectDir,packageMetadataDir,packageMetadataObjects,packageLogDir = prep_package(tempID)

	# 2) CHECK THAT REQUIRED VARS ARE DECLARED
	requiredVars = ['inputFilepath','operator']
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
		# ask operator/input file
		operator = input("Please enter your name: ")
		inputFilepath = input("Please drag the file you want to ingest into this window___").rstrip()
		inputFilepath = pymmFunctions.sanitize_dragged_linux_paths(inputFilepath)

	if inputFilepath and inputType == 'file':
		filename = os.path.basename(inputFilepath)

	# SET UP A DICT FOR PROCESSING VARIABLES TO PASS AROUND
	processingVars =	{'operator':operator,'inputFilepath':inputFilepath,
						'tempID':tempID,'ingestType':ingestType,
						'ingestUUID':ingestUUID,'filename':filename,
						'makeProres':makeProres,
						'packageOutputDir':packageOutputDir,'packageObjectDir':packageObjectDir,
						'packageMetadataDir':packageMetadataDir,'packageMetadataObjects':packageMetadataObjects,
						'packageLogDir':packageLogDir,'aip_staging':aip_staging}

	# 3) SET UP A LOG FILE FOR THIS INGEST
	ingestLogPath = os.path.join(packageLogDir,tempID+'_'+pymmFunctions.timestamp('now')+'_ingestfile-log.txt')
	with open(ingestLogPath,'x') as ingestLog:
		print('Laying a log at '+ingestLogPath)

	ingestLogBoilerplate = 	{
							'ingestLogPath':ingestLogPath,
							'tempID':tempID,
							'filename':filename,
							'operator':operator
							}
	pymmFunctions.ingest_log(
		# message
		'start',
		# status
		'start',
		# ingest boilerplate
		**ingestLogBoilerplate
		)

	# 4) TELL THE SYSTEM LOG THAT WE ARE STARTING
	pymmFunctions.pymm_log(filename,tempID,operator,'','STARTING')

	# 5) IF INTERACTIVE ASK ABOUT CLEANUP
	if interactiveMode:
		reset_cleanup_choice()

	# 6) INSERT DATABASE RECORD FOR THIS INGEST (log 'ingestion start')
	# @fixme

	# 7) CHECK THAT THE FILE IS ACTUALLY AN AV FILE (SHOULD THIS GO FIRST?)
	check_av_status(inputFilepath,interactiveMode,ingestLogBoilerplate)

	# 8) CHECK INPUT FILE AGAINST MEDIACONCH POLICIES
	mediaconch_check(inputFilepath,ingestType,ingestLogBoilerplate)
	
	# 9) RSYNC THE INPUT FILE TO THE OUTPUT DIR
	move_input_file(processingVars)

	# 10) MAKE METADATA FOR INPUT FILE
	input_file_metadata(ingestLogBoilerplate,processingVars)

	# 11) MAKE DERIVATTIVES
	make_derivs(processingVars)

	# 12) CHECK DERIVS AGAINST MEDIACONCH POLICIES
	
	# 13) MOVE SIP TO AIP STAGING
	# a) make a hashdeep manifest
	# b) move it
	move_sip(processingVars)
	packageVerified = False
	# c) audit the hashdeep manifest
	# packageVerified = result of audit

	# FINISH LOGGING

if __name__ == '__main__':
	main()
