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

from bampfa_pbcore import pbcore

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
		'-j','--metadataJSON',
		help='full path to a JSON file containing descriptive metadata'
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
			It looks like {} was already ingested.
			If you want to replace the existing package please delete the package at
			{}
			and then try again.
			'''.format(tempID,packageOutputDir))
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
		goodNames = pymmFunctions.check_for_outliers(inputPath)
		if goodNames:
			if concatChoice == True:
				try_concat(inputPath,ingestUUID)
		else:
			return False
	
	else:
		print("input is a single file")
	return inputType

def try_concat(inputPath,ingestUUID):
	sys.argv = [
		'',
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
		message = "WARNING: {} is not recognized as an a/v file.".format(
			ingestLogBoilerplate['filename']
			)
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

def mediaconch_check(inputPath,ingestType,ingestLogBoilerplate):
	'''
	Check input file against MediaConch policy.
	Needs to be cleaned up. Move logic to pymmFunctions and keep logging here.
	Also, we don't have any policies set up yet...
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
	sys.argv = [
		'',
		'-i'+processingVars['inputPath'],
		'-d'+processingVars['packageObjectDir'],
		'-L'+processingVars['packageLogDir']
		]
	moveNcopy.main()

def input_file_metadata(ingestLogBoilerplate,processingVars):
	pymmFunctions.ingest_log(
		# message
		"The input file MD5 hash is: {}".format(
			makeMetadata.hash_file(processingVars['inputPath'])
			),
		# status
		'OK',
		# ingest boilerplate
		**ingestLogBoilerplate
		)

	mediainfo = makeMetadata.get_mediainfo_report(
		processingVars['inputPath'],
		processingVars['packageMetadataObjects']
		)
	if mediainfo:
		pymmFunctions.ingest_log(
			# message
			"mediainfo XML report for input file written to metadata directory for package.",
			# status
			'OK',
			# ingest boilerplate
			**ingestLogBoilerplate
			)
	
	frameMD5 = makeMetadata.make_frame_md5(
		processingVars['inputPath'],
		processingVars['packageMetadataObjects']
		)
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

	# we'll always output a resourcespace access file for video ingests,
	# so init the derivtypes list with `resourcespace`
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
		pymmFunctions.cleanup_package(inputPath,packageOutputDir,reason)
	else:
		print("BUH-BYE")

def main():
	#########################
	#### SET INGEST ARGS ####
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
	#### END SET INGEST ARGS #### 
	#############################

	#############################
	#### TEST / SET ENV VARS ####
	# sniff whether the input is a file or directory
	inputType = sniff_input(inputPath,ingestUUID,concatChoice)
	if not inputType:
		sys.exit(1)
	if inputType == 'dir':
		source_list = pymmFunctions.list_files(inputPath)
		subs = 0
		for _object in source_list:
			if os.path.isdir(_object):
				subs += 1
				print("\nYou have subdirectory(ies) in your input:"
					"\n({})\n".format(_object))
		if subs > 0:
			print("This is not currently supported. Exiting!")
			sys.exit()

	# create directory paths for ingest...
	packageOutputDir,packageObjectDir,packageMetadataDir,\
	packageMetadataObjects,packageLogDir = prep_package(tempID)

	# check that required vars are declared & init other vars
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

	# set up a dict for processing variables to pass around
	processingVars = {
		'operator':operator,
		'inputPath':inputPath,
		'tempID':tempID,
		'ingestType':ingestType,
		'ingestUUID':ingestUUID,
		'filename':filename,
		'input_name':input_name,
		'makeProres':makeProres,
		'packageOutputDir':packageOutputDir,
		'packageObjectDir':packageObjectDir,
		'packageMetadataDir':packageMetadataDir,
		'packageMetadataObjects':packageMetadataObjects,
		'packageLogDir':packageLogDir,
		'aip_staging':aip_staging
		}
	#### END TEST / SET ENV VARS ####
	#################################

	###########################
	#### LOGGING / CLEANUP ####
	# set up a log file for this ingest
	ingestLogPath = os.path.join(
		packageLogDir,
		'{}_{}_ingestfile-log.txt'.format(
			tempID,pymmFunctions.timestamp('now')
			)
		)
	with open(ingestLogPath,'x') as ingestLog:
		print('Laying a log at '+ingestLogPath)
	ingestLogBoilerplate = {
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

	# tell the system log that we are starting
	pymmFunctions.pymm_log(input_name,tempID,operator,'','STARTING')

	# if interactive ask about cleanup
	if interactiveMode:
		reset_cleanup_choice()

	# insert database record for this ingest (log 'ingestion start') 
	# --> http://id.loc.gov/vocabulary/preservation/eventType/ins.html
	# @fixme
	# @logme # @dbme

	#### END LOGGING / CLEANUP ####
	###############################

	###############
	## DO STUFF! ##
	###############
	if inputType == 'file':
		# check that input file is actually a/v
		check_av_status(inputPath,interactiveMode,ingestLogBoilerplate) # @dbme
		mediaconch_check(inputPath,ingestType,ingestLogBoilerplate) # @dbme
		move_input_file(processingVars) # @logme # @dbme
		input_file_metadata(ingestLogBoilerplate,processingVars) # @logme # @dbme
		make_derivs(processingVars) # @logme # @dbme
	elif inputType == 'dir':
		for _file in source_list:
			# set processing variables per file 
			ingestLogBoilerplate['filename'] = os.path.basename(_file) # @dbme
			processingVars['filename'] = os.path.basename(_file) # @dbme
			processingVars['inputPath'] = _file # @dbme
			# check that input file is actually a/v
			check_av_status(_file,interactiveMode,ingestLogBoilerplate) # @dbme
			mediaconch_check(_file,ingestType,ingestLogBoilerplate) # @dbme
			move_input_file(processingVars) # @dbme
			input_file_metadata(ingestLogBoilerplate,processingVars) # @dbme
			make_derivs(processingVars) # @dbme
		# reset the processing variables to the original state 
		processingVars['filename'] = ''
		processingVars['inputPath'] = inputPath

	# MOVE SIP TO AIP STAGING
	# a) make a hashdeep manifest @fixme
	# b) move it 
	move_sip(processingVars) # @dbme
	packageVerified = False
	# c) audit the hashdeep manifest @fixme
	# packageVerified = result of audit @fixme

	# FINISH LOGGING
	do_cleanup(cleanupStrategy,packageVerified,inputPath,packageOutputDir,'done') # @dbme

if __name__ == '__main__':
	main()
