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
		'-i','--inputPath',
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

def sniff_input(inputPath,ingestUUID,concatChoice):
	'''
	Check whether the input path from command line is a directory
	or single file. If it's a directory, see if the user wanted
	to concatenate the files and do/don't concatenate.
	'''
	inputType = pymmFunctions.dir_or_file(inputPath)
	if inputType == 'dir':
		# filename sanity check
		goodNames = check_for_outliers(inputPath)
		if goodNames and concatChoice == True:
			try_concat(inputPath,ingestUUID)
		else:
			print('input is a directory')
			# sys.exit()
	
	else:
		print("input is a single file")
	return inputType

def check_for_outliers(inputPath):
	'''
	DO A SANITY CHECK ON FILENAMES IN AN INPUT DIRECTORY
	EXIT IF THERE IS A DISCREPANCY (IF FILENAMES ARE TOO DIFFERENT)... 
	WE MAY OR MAY NOT WANT TO LOOSEN THIS?
	'''
	outliers, outlierList = pymmFunctions.check_dir_filename_distances(inputPath)
	if outliers > 0: 
		print("Hey, there are "+str(outliers)+" files that seem like they might not belong in the input directory."
			"\nHere's a list:"
			"\n"+'\n'.join(outlierList)
			)
		return False
	else:
		return True

def try_concat(inputPath,ingestUUID):
	sys.argv = 	['',
						'-i'+inputPath,
						'-d'+ingestUUID
						]
	try:
		concatFiles.main()
		return True
	except:
		return False

def check_av_status(inputPath,interactiveMode,ingestLogBoilerplate):
	'''
	Check whether or not a file is recognized as an a/v file.
	If it isn't and user declares interactive mode, ask whether to continue, otherwise quit.
	'''
	if not pymmFunctions.is_av(inputPath):
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

def mediaconch_check(inputPath,ingestType,ingestLogBoilerplate):
	'''
	Check input file against MediaConch policy.
	Needs to be cleaned up. Also, we don't have any policies set up yet...
	'''
	if ingestType == 'film scan':
		policyStatus = pymmFunctions.check_policy(ingestType,inputPath)
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
				'-i'+processingVars['inputPath'],
				'-d'+processingVars['packageObjectDir'],
				'-L'+processingVars['packageLogDir']
				]
	moveNcopy.main()

def input_file_metadata(ingestLogBoilerplate,processingVars):
	pymmFunctions.ingest_log(
		# message
		"The input file MD5 hash is: "+makeMetadata.hash_file(processingVars['inputPath']),
		# status
		'OK',
		# ingest boilerplate
		**ingestLogBoilerplate
		)

	mediainfo = makeMetadata.get_mediainfo_report(processingVars['inputPath'],processingVars['packageMetadataObjects'])
	if mediainfo:
		pymmFunctions.ingest_log(
			# message
			"mediainfo XML report for input file written to metadata directory for package.",
			# status
			'OK',
			# ingest boilerplate
			**ingestLogBoilerplate
			)
	
	frameMD5 = makeMetadata.make_frame_md5(processingVars['inputPath'],processingVars['packageMetadataObjects'])
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
	'''
	inputPath = processingVars['inputPath']
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
		derivTypes.append('proresHQ')
	elif makeProres == True:
		derivTypes.append('proresHQ')
	else:
		pass

	for derivType in derivTypes:
		sys.argv = 	['',
					'-i'+inputPath,
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
	'''
	Move a prepped SIP to the AIP staging area.
	Rename the directory to the ingest UUID.
	'''
	packageOutputDir = processingVars['packageOutputDir']
	aip_staging = processingVars['aip_staging']
	tempID = processingVars['tempID']
	ingestUUID = processingVars['ingestUUID']
	sys.argv = 	['',
				'-i'+packageOutputDir,
				'-d'+aip_staging,
				'-L'+os.path.join(aip_staging,ingestUUID)]
	moveNcopy.main()
	# rename the staged dir
	stagedSIP = os.path.join(aip_staging,tempID)
	UUIDpath = os.path.join(aip_staging,ingestUUID)
	pymmFunctions.rename_dir(stagedSIP,UUIDpath)

def do_cleanup(cleanupStrategy,packageVerified,inputPath,packageOutputDir,reason):
	if cleanupStrategy == True and packageVerified == True:
		print("LET'S CLEEEEEAN!")
		cleanup_package(inputPath,packageOutputDir,reason)
	else:
		print("BUH-BYE")

def main():
	# parse them args
	args = set_args()
	inputPath = args.inputPath
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
	tempID = pymmFunctions.get_temp_id(inputPath)

	# SNIFF WHETHER THE INPUT IS A FILE OR DIRECTORY
	inputType = sniff_input(inputPath,ingestUUID,concatChoice)
	if inputType == 'dir':
		source_list = pymmFunctions.list_files(inputPath)

	# CREATE DIRECTORY PATHS FOR INGEST...
	packageOutputDir,packageObjectDir,packageMetadataDir,\
	packageMetadataObjects,packageLogDir = prep_package(tempID)

	# CHECK THAT REQUIRED VARS ARE DECLARED & INIT OTHER VARS
	requiredVars = ['inputPath','operator']
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
		inputPath = input("Please drag the file you want to ingest into this window___").rstrip()
		inputPath = pymmFunctions.sanitize_dragged_linux_paths(inputPath)

	# Set up a canonical name that will be passed to each log entry.
	# For files it's the basename, for dirs it's the dir name.
	if inputPath:
		canonicalName = os.path.basename(inputPath)
		if inputType == 'file':
			filename = input_name = canonicalName
		elif inputType == 'dir':
			filename = ''
			input_name = canonicalName

	# SET UP A DICT FOR PROCESSING VARIABLES TO PASS AROUND
	processingVars =	{'operator':operator,'inputPath':inputPath,
						'tempID':tempID,'ingestType':ingestType,
						'ingestUUID':ingestUUID,'filename':filename,
						'input_name':input_name,'makeProres':makeProres,
						'packageOutputDir':packageOutputDir,'packageObjectDir':packageObjectDir,
						'packageMetadataDir':packageMetadataDir,'packageMetadataObjects':packageMetadataObjects,
						'packageLogDir':packageLogDir,'aip_staging':aip_staging}

	# SET UP A LOG FILE FOR THIS INGEST
	ingestLogPath = os.path.join(packageLogDir,tempID+'_'+pymmFunctions.timestamp('now')+'_ingestfile-log.txt')
	with open(ingestLogPath,'x') as ingestLog:
		print('Laying a log at '+ingestLogPath)
	ingestLogBoilerplate = 	{
							'ingestLogPath':ingestLogPath,
							'tempID':tempID,
							'input_name':input_name,
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

	# TELL THE SYSTEM LOG THAT WE ARE STARTING
	pymmFunctions.pymm_log(input_name,tempID,operator,'','STARTING')

	# IF INTERACTIVE ASK ABOUT CLEANUP
	if interactiveMode:
		reset_cleanup_choice()

	# INSERT DATABASE RECORD FOR THIS INGEST (log 'ingestion start')
	# @fixme

##           ##
## DO STUFF! ##
##           ##
	if inputType == 'file':
		# CHECK THAT INPUT FILE IS ACTUALLY A/V
		check_av_status(inputPath,interactiveMode,ingestLogBoilerplate)
		mediaconch_check(inputPath,ingestType,ingestLogBoilerplate)
		move_input_file(processingVars)
		input_file_metadata(ingestLogBoilerplate,processingVars)
		make_derivs(processingVars)
	elif inputType == 'dir':
		for _file in source_list:
			# set processing variables per file 
			ingestLogBoilerplate['filename'] = os.path.basename(_file)
			processingVars['filename'] = os.path.basename(_file)
			processingVars['inputPath'] = _file
			# CHECK THAT INPUT FILE IS ACTUALLY A/V
			check_av_status(_file,interactiveMode,ingestLogBoilerplate)
			mediaconch_check(_file,ingestType,ingestLogBoilerplate)
			move_input_file(processingVars)
			input_file_metadata(ingestLogBoilerplate,processingVars)
			make_derivs(processingVars)
		# reset the processing variables to the original state 
		processingVars['filename'] = ''
		processingVars['inputPath'] = inputPath

	# MOVE SIP TO AIP STAGING
	# a) make a hashdeep manifest @fixme
	# b) move it 
	move_sip(processingVars)
	packageVerified = False
	# c) audit the hashdeep manifest @fixme
	# packageVerified = result of audit @fixme

	# FINISH LOGGING
	do_cleanup(cleanupStrategy,packageVerified,inputPath,packageOutputDir,'done')

if __name__ == '__main__':
	main()
