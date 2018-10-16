#!/usr/bin/env python3
'''
This is a set of functions used by pymm scripts

This file is organized into 4 main sections:
 * CONFIG CHECK STUFF
 * PYMM ADMIN / LOGGING STUFF
 * FILE CHECK STUFF
 * SYSTEM / ENVIRONMENT STUFF

'''
import configparser
from datetime import date
import glob
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import shutil
import time
# nonstandard libraries:
import Levenshtein
# local modules:
import dbReporters
import makeMetadata
import MySQLqueries
import sequenceScanner

################################################################
# 
# CONFIG CHECK STUFF
#
def read_config():
	pymmDirectory = os.path.dirname(os.path.abspath(__file__))
	configPath = os.path.join(pymmDirectory,'pymmconfig','config.ini') 
	if not os.path.isfile(configPath):
		print('''
			CONFIGURATION PROBLEM:\n
			YOU HAVE NOT YET SET CONFIG.INI OR IT IS MISSING.\n
			RUN pymmconfig.py TO CREATE CONFIG.INI AND CHOOSE YOUR DESIRED SETTINGS.\n
			NOW EXITING.
			''')
		sys.exit()
	config = configparser.SafeConfigParser()
	config.read(configPath)
	return config

def check_missing_ingest_paths(pymmConfig):
	requiredPaths = {
		'outdir_ingestsip':'the ingestSip.py output path',
		'aip_staging':'the AIP storage path',
		'resourcespace_deliver':'the resourcespace output path'
		}
	missingPaths = 0
	for path in requiredPaths.items():
		if not os.path.isdir(pymmConfig['paths'][path[0]]):
			missingPaths += 1
			print('''
				CONFIGURATION PROBLEM:
				You have not yet set a valid directory for '{}.' Please run pymmConfig.py,
				edit the config file directly,
				or use '--{}' to set {}.
				HINT: Check that the filepath is entered correctly.
				'''.format(path[0],path[0],path[1])
				)
	if missingPaths > 0:
		print("\nYou are missing some required file paths and we have to quit. Sorry.")
		sys.exit()	
# 
# END CONFIG CHECK STUFF
# 
################################################################

################################################################
#
# PYMM ADMIN / LOGGING STUFF
#
# have to import dbAccess after init config to avoid circular error
import dbAccess

def check_pymm_log_exists():
	# open a local instance of config here in case 
	# it has changed since importing this file
	pymmConfig = read_config()
	pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
	pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')
	# sys.exit()
	opener = (
		((("#"*75)+'\n')*2)+((' ')*4)+'THIS IS THE LOG FOR PYMEDIAMICROSERVICES'
		'\n\n'+((' ')*4)+'THIS VERSION WAS STARTED ON '+today+'\n'+((("#"*75)+'\n')*2)+'\n'
		)

	if not os.path.isfile(pymmLogPath):
		print('wait i need to make a logfile')
		if pymmLogDir == '':
			print("!~"*75)
			print(
				"CONFIGURATION PROBLEM:\n"
				"THERE IS NO DIRECTORY SET FOR THE SYSTEM-WIDE LOG.\n"
				"PLEASE RUN pymmconfig.py OR EDIT config.ini DIRECTLY\n"
				"TO ADD A VALID DIRECTORY FOR pymm_log.txt TO LIVE IN.\n"
				"WE'RE JUST GOING TO PUT IT ON YOUR DESKTOP FOR NOW..."
				)
			desktop = get_desktop()
			pymmLogPath = os.path.join(
				desktop,
				'pymm_log.txt'
				)
			from pymmconfig import pymmconfig
			pymmconfig.set_value('logging','pymm_log_dir',desktop)
			with open(pymmLogPath,'w+') as pymmLog:
				pymmLog.write(opener)
		else:
			open(pymmLogPath,'x')
			with open(pymmLogPath,'w+') as pymmLog:
				pymmLog.write(
					opener
					)
	else:
		pass

def ingest_log(\
	event,\
	outcome,\
	status,\
	ingestLogPath,\
	tempID,\
	inputName,\
	filename,\
	operator,\
	inputPath,\
	ingestUUID\
	):
	stamp = timestamp("iso8601")

	if event == "ingestion start":
		stamp = ("#"*50)+"\n\n"+stamp+"\n\n"
		systemInfo = system_info()
		workingDir = os.path.join(
			pymmConfig["paths"]["outdir_ingestsip"],
			tempID
			)
		stuffToLog = [
			stamp,
			"Event Type: ingestion start\n",
			"Object Canonical Name: {}\n".format(inputName),
			"Object Input Filepath: {}\n".format(inputPath),
			"Object Temp ID: {}\n".format(tempID),
			"Ingest UUID: {}\n".format(ingestUUID),
			"Ingest Working Directory: {}\n".format(workingDir),
			"Operator: {}\n".format(operator),
			"\n### SYSTEM INFO: ### \n{}\n".format(systemInfo),
			("#"*50)
			]
		if filename not in ("",None):
			name = "Object Filename: {}\n".format(filename)
			stuffToLog.insert(3,name)

	else:
		stuffToLog = [
			"{} | ".format(stamp),
			"Status: {} | ".format(status),
			"Event Type: {} | ".format(event),
			"Event Outcome: {} | ".format(outcome),
			"Operator: {} | ".format(operator),
			"Object Canonical Name: {} | ".format(inputName)
			]
		if filename not in ("",None):
			name = "Object Filename: {} | ".format(filename)
			path = "Object Filepath: {} | ".format(inputPath)
			stuffToLog.insert(4,name)
			stuffToLog.insert(5,path)

	with open(ingestLogPath,"a+") as ingestLog:
		for item in stuffToLog:
			ingestLog.write(item)
		ingestLog.write("\n\n")

def pymm_log(processingVars,event,outcome,status):
	check_pymm_log_exists()
	# open a local instance of config here in case 
	# it has changed since importing this file
	pymmConfig = read_config()
	pymmConfig = read_config()
	pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
	pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')
	stamp = timestamp('iso8601')
	systemInfo = system_info()
	objectRootPath = processingVars['inputPath']
	objectName = processingVars['inputName']
	operator = processingVars['operator']
	ingestUUID = processingVars['ingestUUID']
	tempID = get_temp_id(objectRootPath)
	workingDir = os.path.join(
			pymmConfig["paths"]["outdir_ingestsip"],
			tempID
			)
	prefix = ''
	suffix = '\n'
	basename = os.path.basename(objectRootPath)
	if status == 'STARTING':
		prefix = ('&'*50)+'\n\n'
		stuffToLog = [
			prefix,
			stamp,
			"\nEvent type: Ingestion start\n",
			"Object canonical name: {}\n".format(objectName),
			"Object filepath: {}\n".format(objectRootPath),
			"Ingest UUID: {}\n".format(ingestUUID),
			"Operator: {}\n".format(operator),
			"Ingest working directory: {}\n".format(workingDir),
			"\n### SYSTEM INFO: ### \n{}".format(systemInfo),
			suffix
			]
	elif status in ("ENDING","ABORTING"):
		suffix = '\n\n'+('#'*50)+"\n\n"
		stuffToLog = [
			prefix,
			stamp,
			" | Status: {} |".format(status),
			" | Event type: Ingestion end | ",
			"Outcome: {}".format(outcome),
			suffix
			]
	else:
		stuffToLog = [
			prefix,
			stamp,
			" | Status: {}".format(status),
			" | Object name: {}".format(basename),
			" | Event type: {}".format(event),
			" | Event outcome: {}".format(outcome),
			suffix
			]

	with open(pymmLogPath,'a') as log:
		for item in stuffToLog:
			log.write(item)

def log_event(processingVars,ingestLogBoilerplate,event,outcome,status):
	'''
	log an event to all logs: database, system log, ingest log
	'''
	pymm_log(
		processingVars,
		event,
		outcome,
		status
		)
	ingest_log(
		event,
		outcome,
		status,
		**ingestLogBoilerplate
		)
	eventID = insert_event(
		processingVars,
		event,
		outcome,
		status
		)

	return eventID

def short_log(processingVars,ingestLogBoilerplate,event,outcome,status):
	'''
	same as log_event() but skip the system log for when the event
	is too detailed.
	'''
	ingest_log(
		event,
		outcome,
		status,
		**ingestLogBoilerplate
		)
	eventID = insert_event(
		processingVars,
		event,
		outcome,
		status
		)

	return eventID

def end_log(processingVars,event,outcome,status):
	'''
	same as short_log() but skip the ingest log 
	so as not to bungle the hashdeep manifest
	'''
	pymm_log(
		processingVars,
		event,
		outcome,
		status
		)
	eventID = insert_event(
		processingVars,
		event,
		outcome,
		status
		)

	return eventID

def cleanup_package(processingVars,pathForDeletion,reason,outcome=None):
	# print(pathForDeletion)
	if reason == "ABORTING":
		status = 'ABORTING'
		event = 'ingestion end'
		if not outcome:
			outcome = (
				"Something went critically wrong... "
				"The ingest process was aborted."
				"\n{}\nand its contents have been deleted.".format(
					pathForDeletion
					)
				)
	elif reason == 'done':
		status = 'OK'
		event = 'deletion'
		outcome = (
			"Deleting original copies "
			"of object at {}".format(pathForDeletion)
			)

	if os.path.isdir(pathForDeletion):
		try:
			shutil.rmtree(pathForDeletion)
		except:
			outcome = (
				"Could not delete the package at "
				+pathForDeletion+
				". Try deleting it manually?"
				)
			print(outcome)
	processingVars['caller'] = 'pymmFunctions.cleanup_package()'
	end_log(
		processingVars,
		event,
		outcome,
		status
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
		print(
			"Either you selected no or your answer didn't make sense"
			"so we will just leave things where they are when we finish."
			)
	return cleanupStrategy

def validate_SIP_structure(SIPpath):
	'''
	Check that all the top-level stuff expected in a package exists.
	Don't go too deep... 
	Current expected structure is:
	UUID/
	  UUID/
	    metadata/
	      objects_manifest_UUID_iso8601.txt
	      objectCanonicalName_pbcore.xml
	      logs/
	        ingestLog.txt
	        ffmpeglog
	        rsyncLog
	      objects/
		    masterobject1_framemd5.md5
		    masterobject2_framemd5.md5
	        masterobject1_mediainfo.xml
	        masterobject2_mediainfo.xml
	        resourcespace/
	          resourcespace_mediainfo.xml
	    objects/
	      masterobject1
	      masterobject2
	      resourcespace/
	        resourcespace1
	        resourcespace2
	    
	  # (changed this 7/16/18) hashdeep_manifest_UUID_iso8601.txt
	'''
	structureValidated = True
	status = "OK"

	_UUID = os.path.basename(SIPpath)
	# define the directories to check
	ingestDir = os.path.join(SIPpath,_UUID)
	metadataDir = os.path.join(ingestDir,'metadata')
	logDir = os.path.join(metadataDir,'logs')
	objectMetadataDir = os.path.join(metadataDir,'objects')
	objectDir = os.path.join(ingestDir,'objects')
	dirs = [ingestDir,metadataDir,logDir,objectMetadataDir,objectDir]
	reasonsFailed = []
	# check that they exist
	# I should log the non-existence of any of these
	# maybe rename the SIP to FAILED-UUID?
	for thing in dirs:
		if not os.path.isdir(thing):
			structureValidated = False
			failure = "missing {}".format(os.path.basename(thing))
			reasonsFailed.append(failure)
			print(failure)

	# use glob to search for the existence of
	# 1) hashdeep manifest
	# 2) pbcore xml file
	objectManifestPattern = os.path.join(
		metadataDir,
		'objects_manifest_*'
		)
	manifest = glob.glob(objectManifestPattern)
	if manifest == []:
		failure = "missing a hashdeep manifest for the SIP object directory"
		reasonsFailed.append(failure)
		print(failure)
		structureValidated = False
	
	pbcorePattern = os.path.join(metadataDir,'*_pbcore.xml')
	pbcore = glob.glob(pbcorePattern)
	if pbcore == []:
		failure = "missing a pbcore xml description for the object"
		reasonsFailed.append(failure)
		print(failure)
		structureValidated = False
	if structureValidated:
		outcome = "SIP validated against expected structure"
	else:
		outcome = "SIP failed to validate for these reasons:\n~ {}\n".format(
			"\n~ ".join(reasonsFailed)
			)

	return structureValidated,outcome

def database_connection(user):
	connection = dbAccess.DB(user)
	try:
		connection.connect()
		return connection
	except:
		print("DB connection problem...")
		return False

def do_query(connection,sql,*args):
	'''
	must be passed an open mysql.connector.connection.MySQLConnection object
	'''
	cursor = connection.query(sql,*args)
	return cursor

def insert_object(processingVars,objectCategory,objectCategoryDetail):
	operator = processingVars['operator']
	if processingVars['filename'] in ('',None):
		theObject = processingVars['inputName']
	else:
		theObject = processingVars['filename']
	if processingVars['database_reporting'] == True:
		# init an insertion instance
		objectInsert = dbReporters.ObjectInsert(
				operator,
				theObject,
				objectCategory,
				objectCategoryDetail
				)
		try:
			# report the details to the db
			objectIdentifierValueID = objectInsert.report_to_db()
			del objectInsert
		except:
			print("CAN'T MAKE DB CONNECTION")
			pymm_log(
				processingVars,
				event = "connect to database",
				outcome = "NO DATABASE CONNECTION!!!",
				status = "WARNING"
				)
			processingVars['database_reporting'] = False
	else:
		objectIdentifierValueID = None
	# update the processingVars with the unique db ID of the object
	processingVars['componentObjectData'][theObject] = {}
	processingVars['componentObjectData'][theObject]['databaseID'] = str(
		objectIdentifierValueID
		)
	# set the object category in component object data
	processingVars['componentObjectData'][theObject]\
		['objectCategory'] = objectCategory
	processingVars['componentObjectData'][theObject]\
		['objectCategoryDetail'] = objectCategoryDetail

	return processingVars

def insert_event(processingVars,eventType,outcome,status):
	if processingVars['filename'] in ('',None):
			theObject = processingVars['inputName']
	else:
		theObject = processingVars['filename']
	# get the name of the computer
	computer = processingVars['computer']
	# get the name of the program, script, or function doing the event
	callingAgent = processingVars['caller']

	objectID = processingVars['componentObjectData'][theObject]['databaseID']
	if processingVars['database_reporting'] == True:
		#insert the event
		eventInsert = dbReporters.EventInsert(
			eventType,
			objectID,
			theObject,
			timestamp('iso8601'),
			status,
			outcome,
			callingAgent,
			computer,
			processingVars['operator'],
			eventID=None
			)

		eventID = eventInsert.report_to_db()
		del eventInsert
	else:
		eventID = None
	return eventID

def insert_obj_chars(processingVars,ingestLogBoilerplate):
	'''
	report obect characteristics to db:
	- get the object dict
	- for files report the mediainfo text
	- for SIPs report the pbcore, ingestLog
	- 
	'''
	if processingVars['database_reporting'] != True:
		return processingVars
	user = processingVars['operator']
	for _object,chars in processingVars['componentObjectData'].items():
		data = processingVars['componentObjectData'][_object]
		category = data['objectCategory']
		categoryDetail = data['objectCategoryDetail']
		if category == 'file':
			try:
				mediainfoPath = data['mediainfoPath']
				objID = data['databaseID']
				with open(mediainfoPath,'r') as MI:
					mediainfoText = MI.read()
				objectCharsInsert = dbReporters.InsertObjChars(
					user,
					objID,
					_object,
					mediainfoText
					)
				objectCharsInsert.report_to_db()
				del objectCharsInsert
			except:
				pass
		elif category == 'intellectual entity'\
			and categoryDetail == 'Archival Information Package':
			try:
				objID = data['databaseID']
				pbcorePath = processingVars['pbcore']
				# print(pbcorePath)
				if os.path.isfile(pbcorePath):
					with open(pbcorePath,'r') as PB:
						pbcoreText = PB.read()
						# print(pbcoreText)
				else:
					pbcoreText = None
					pbcorePath = None
				ingestLogPath = ingestLogBoilerplate['ingestLogPath']
				if os.path.isfile(ingestLogPath):
					with open(ingestLogPath,'r') as IL:
						ingestLogText = IL.read()
				else:
					ingestLogText = None				
				# theres some mysql permission preventing
				# load_file(pbcorePath) as BLOB
				# @fixme ... also, is it worth it?
				objectCharsInsert = dbReporters.InsertObjChars(
					user,
					objID,
					_object,
					mediaInfo=None,
					ingestLog=ingestLogText,
					pbcoreText=pbcoreText,
					pbcoreXML=pbcorePath
					)
				objectCharsInsert.report_to_db()
			except:
				print(
					"COULDN'T REPORT characteristics FOR {}".format(_object)
					)
	return processingVars


def get_event_timestamp(eventID,user):
	connection = database_connection(user)
	sql = MySQLqueries.getEventTimestamp

	cursor = do_query(
		connection,
		sql,
		eventID
		)
	# this returns a datetime.datetime tuple like 
	# (datetime.datetime(2018, 7, 16, 15, 21, 13),)
	value = cursor.fetchone()
	timestamp =  value[0].strftime("%Y-%m-%dT%H:%M:%S")
	return timestamp

def insert_fixity(\
	processingVars,\
	eventID,\
	messageDigestAlgorithm,\
	messageDigestHashValue,\
	messageDigestSource=None,
	eventDateTime=None
	):
	# if processingVars['database_reporting'] == True:
	# 	pass
	# else:
	# 	return None
	inputFile = processingVars['filename']
	objectID = processingVars['componentObjectData'][inputFile]['databaseID']
	objectIDValue = processingVars['filename']
	eventDetailCallingFunc = processingVars['caller']
	messageDigestFilepath = processingVars['inputPath']
	
	if processingVars['database_reporting'] == True:
		eventTimestamp = get_event_timestamp(
			eventID,
			processingVars['operator']
			)

		if not eventTimestamp:
			eventDateTime = None
		else:
			eventDateTime = eventTimestamp

		fixityInsert = dbReporters.FixityInsert(
			processingVars['operator'],
			eventID,
			objectID,
			objectIDValue,
			eventDetailCallingFunc,
			messageDigestAlgorithm,
			messageDigestFilepath,
			messageDigestHashValue,
			messageDigestSource,
			eventDateTime
			)

		fixityID = fixityInsert.report_to_db()
		del fixityInsert
	else:
		fixityID = None
	# print("HEY-O")
	return fixityID

def parse_object_manifest(manifestPath):
	'''
	parse an object manifest to grab md5 hashes for db reporting
	returns tuple (True/False,{'filename1':'hash1','filename2':'hash2'})
	'''
	parsed = False
	data = []
	hashes = {}
	if not os.path.basename(manifestPath).startswith('objects_manifest_'):
		parsed = 'Not an object manifest'
	else:
		try:
			with open(manifestPath,'r') as f:
				for line in f:
					# notes in the hashdeep manifest start with 
					# '%' or '%'
					if not (line.startswith('%') or line.startswith('#')):
						data.append(line)
			for element in data:
				# this is the file
				_file = element.split(',')[2].rstrip()
				_file = os.path.basename(_file)
				# this is the hash
				hashes[_file] = element.split(',')[1]
			parsed = True
		except:
			parsed = 'error parsing object manifest'

	# hashes should look like {'filename':'md5 hash'}
	return parsed,hashes

def parse_pbcore_xml(pbcoreFile):
	pbcoreString = ''
	with open(pbcoreFile,'r') as f:
		for line in f:
			pbcoreString += line

	return pbcoreString
#
# END PYMM ADMIN / LOGGING STUFF 
#
################################################################

################################################################
#
# FILE CHECK STUFF
#
def is_video(inputPath):
	# Look for a video stream with codec_type == 'video'
	ffprobe = [
		'ffprobe',
		'-i',inputPath,
		# '-v','error',
		'-print_format','json',
		'-show_streams',
		'-select_streams','v'
		]
	try:
		probe = subprocess.run(ffprobe,stdout=subprocess.PIPE)
		out = probe.stdout.decode('utf-8')
		output = json.loads(out)
		# print(output)
		try:
			codec_type = output['streams'][0]['codec_type']
			if codec_type == 'video':
				return True
		except:
			return False
	except:
		return False
	

def is_audio(inputPath):
	print("THIS ISN'T A VIDEO FILE\n"
		'maybe this is an audio file?')
	# DO THE SAME AS ABOVE BUT codec_type == 'audio'
	ffprobe = [
		'ffprobe',
		'-i',inputPath,
		'-print_format','json',
		'-show_streams',
		'-select_streams','a'
		]
	try:
		probe = subprocess.run(ffprobe,stdout=subprocess.PIPE)
		out = probe.stdout.decode('utf-8')
		output = json.loads(out)
		try:
			codec_type = output['streams'][0]['codec_type']
			if codec_type == 'audio':
				print("This appears to be an audio file!")
				return True
		except:
			print("THIS DOESN'T SMELL LIKE AN AUDIO FILE EITHER")
			# print(output)
			return False
	except:
		print("INVALID FILE INPUT, NOT AUDIO EITHER")
		return False

def is_av(inputPath):
	'''
	run tests for video, then audio, then DPX seq, then give up.
	@FIXME - this should return a more verbose/useful
		explanation of failed tests.
		Currently the expected return value os Boolean when is_av() is called. 
	'''
	_is_video = is_video(inputPath)
	_is_audio = False
	_is_dpx = False
	_is_dpx_av = False
	if _is_video == True:
		return 'VIDEO'
	else:
		_is_audio = is_audio(inputPath)
		if _is_audio:
			return 'AUDIO'
		else:
			try:
				_is_dpx,details = sequenceScanner.main(inputPath)
			except:
				print('error scanning a sequence directory')
				return False
			if _is_dpx:
				if details in ('single reel dpx','multi-reel dpx'):
					# insert test for only dpx contents
					status, failedDirs = test_sequence_reel_dir(inputPath)
					if status == True:
						print('THIS IS AN IMAGE SEQUENCE!')
						return 'DPX'
					else:
						print(
							'ERROR: check out this list of '
							'problem directories: {}'.format(failedDirs)
							)
						return False

			elif _is_dpx == None:
				# if we are dealing with an actual sequence folder,
				# run a different test
				_is_dpx_av = is_dpx_sequence(inputPath)
				if _is_dpx_av:
					print('THIS IS AN IMAGE SEQUENCE!')
					return 'DPX'
			else:
				return None

def test_sequence_reel_dir(reelPath):
	'''
	Take a directory that should contain only a wav file
	and a corresponding directory with an image sequence in it.
	If there's a problem with one or more of the directories return
	it/them in a list.
	'''
	failedDirs = []
	failures = 0
	for item in os.scandir(reelPath):
		if item.is_dir():
			# print(item.path)
			_is_dpx_av = is_dpx_sequence(item.path)
			if not _is_dpx_av:
				failedDirs.append(item.path)
				failures += 1
			else:
				pass
	if failures > 0:
		return False, failedDirs
	else:
		return True, failedDirs

def is_dpx_sequence(inputPath):
	'''
	run mediainfo on the 'dpx' folder
	if there's anything other than dpx files in there
	the result will not parse as json and it indicates
	noncompliance with expected structure
	(PS-this is a hack)
	'''
	_is_dpx_av = False
	try:
		mediainfo = makeMetadata.get_mediainfo_report(inputPath,'',_JSON=True)
		mediainfo = json.loads(mediainfo)
	except:
		_is_dpx_av = False
	if mediainfo:
		_is_dpx_av = True

	return _is_dpx_av

def check_policy(ingestType,inputPath):
	print('do policy check stuff')
	policyStatus = "result of check against mediaconch policy"
	return policyStatus

def dir_or_file(inputPath):
	if os.path.isdir(inputPath):
		return 'dir'
	elif os.path.isfile(inputPath):
		return 'file'
	else:
		return False

def get_base(inputPath,base='basename'):
	bases = {'basename':'','baseMinusExtension':'','ext_original':''}
	if not base in bases.keys():
		return "_:(_"
	else:
		try:
			basename = os.path.basename(inputPath)
			bases['basename'] = basename
			baseAndExt = os.path.splitext(basename)
			baseMinusExtension = baseAndExt[0]
			bases['baseMinusExtension'] = baseMinusExtension
			ext_original = baseAndExt[1]
			bases['ext_original'] = ext_original

			return bases[base]
		except:
			print("error getting basename")
			return "_:(_"

def abspath_list(directory):
	paths = []
	for filename in os.listdir(directory):
		path = os.path.abspath(os.path.join(directory, filename))
		# path = path.replace(' ','\\ ')
		paths.append(path)
	return paths 

def check_dir_filename_distances(directory):
	'''
	Check a directory to be ingested for wildly divergent filenames. 
	We will currently only want to allow single-level directories of 
	files that represent parts of a whole and thus have fairly 
	similar filenames.
	'''

	_list = abspath_list(directory)
	names = []
	for name in _list:
		if os.path.isfile(name):
			if not os.path.basename(name).startswith('.'):
				names.append(name)
	median = Levenshtein.median(names)
	# print(median)
	outliers = 0 # start a counter for the number of files that diverge from the median name
	outlierList = []  # and list them
	for name in names:
		distance = Levenshtein.distance(median,name)
		# print(distance)
		if distance > 10:
			outliers += 1
			outlierList.append(name)

	return outliers,outlierList

def check_for_outliers(inputPath):
	'''
	Use distance check function to approve/deny
	viability of directory ingest.
	'''
	outliers, outlierList = check_dir_filename_distances(inputPath)
	if outliers > 0: 
		print(
			"Hey, there are {} files that seem like they might not belong"
			" in the input directory.\n".format(str(outliers)))
		print("Here's a list of them:\n"
			+'\n'.join(outlierList)
			)
		return False
	else:
		return True

def list_files(_input):
	'''
	Take in an absolute path of a directory and return a list of the paths
	for everything in it.
	'''
	if os.path.isdir(_input):
		source_list = []
		for _file in os.listdir(_input):
			if os.path.isdir(_file):
				print("you have unexpected subdirectories. now exiting.")
				sys.exit()
			else:
				source_list.append(os.path.join(_input,_file))
		source_list.sort()
		return source_list
	else:
		print("you're trying to list files but the input is a file. go away.")
		# sys.exit()
		pass

def get_temp_id(_string):
	'''
	Generate a hash of a string (i.e., of an input path) that can be used
	to produce a *locally* unique temporary ID during the ingestSIP process.
	For convenience (?) I'm cutting it down to 10 digits.
	example: ingestSIP -i 'foo.mov' --> tempID = a8bcd6d073
	where:
	sha256 = a8bcd6d073c91f6132f6d64674ecaf658a33c4aedde4046b0b7bf64e9c723073
	'''
	pathHash = hashlib.sha256(_string.encode()).hexdigest()
	tempID = pathHash[:10]

	return tempID

def rename_dir(_dir,newName):
	if os.path.isdir(_dir):
		path = os.path.dirname(_dir)
		newPath = os.path.join(path,newName)
		try:
			newDir = os.rename(_dir,newPath)
			return newPath
		except OSError as e:
			print("OOPS: {}".format(e))
	else:
		print("{} is not a directory so go away.".format(_dir))

def convert_millis(milli):
    '''
    Lifted directly from IFIscripts. Written by Kieran O'Leary.
    Requires an integer that is the number of milliseconds.
      For example mediainfo returns '00:51:58.824' as a string '3118.824'
      so you gotta remove the period, convert to integer, and parse here.
    Accepts milliseconds and returns this value as HH:MM:SS.NNN
    '''
    # get the number of seconds and milliseconds 
    a = datetime.timedelta(milliseconds=milli)
    # convert to a handy string that looks like '0:51:58.824000'
    # so we can check for milliseconds present
    b = str(a)
    # no millseconds are present if there is no remainder. We need milliseconds!
    if len(b) == 7:
        b += '.000000'
    # convert seconds-based tuple to H:M:S:ms tuple
    timestamp = datetime.datetime.strptime(b, "%H:%M:%S.%f").time()
    # turn that into a string like '0:51:58.824000'
    c = str(timestamp)
    if len(c) == 8:
        c += '.000000'
    # trim off the unneeded zeros
    return str(c)[:-3]

def get_audio_sample_rate(inputPath):
	# get the sample rate for an audio file
	_type = 'Audio'
	fieldName = 'SamplingRate'
	rate = get_mediainfo_value(
		inputPath,
		_type,
		fieldName
		)

	return rate

def get_encoded_date(inputPath):
	encodedDate = get_mediainfo_value(
		inputPath,
		'General',
		'Encoded_Date'
		)

	return encodedDate

def get_mediainfo_value(inputPath,_type,fieldName):
	'''
	inspired by IFIscripts and StackOverflow answer by Jerome M.
	Note: you don't need quotation marks here after --inform parameter
		which you do need when calling mediainfo from command line.
	`_type` is either General, Audio, or Video
	`fieldName` is the raw field name 
		(look at `mediainfo --Language=raw --Full /file/path` 
		to see all the fields)
	'''
	mediainfo = [
	'mediainfo',
	'--inform={};%{}%'.format(_type,fieldName),
	inputPath
	]
	out = subprocess.run(mediainfo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	value = out.stdout.decode().rstrip()

	return value

def get_framerate(inputPath):
	'''
	get the framerate from a video file
	'''
	framerate = get_mediainfo_value(
		inputPath,
		'Video',
		'FrameRate'
		)
	return framerate

def parse_sequence_parent(inputPath):
	'''
	input path should only ever be:
	title_acc#_barcode_reel#/
		dpx/
			title_acc#_barcode_reel#_sequence#.dpx
		[optionaltitle_acc#_barcode_reel#.wav]

	this function returns a few variables:
		* audioPath = path to an audio file (should be .wav in all our cases)
		* filePattern = pattern for ffmpeg to parse
		* startNumber = first sequence number
		* framerate = embedded by scanner in DPX files
	'''
	sequenceScanner.main(inputPath)
	for entry in os.scandir(inputPath):
		if entry.is_file():
			if entry.name.endswith('.wav'):
				audioPath = entry.path
			else:
				audioPath = None
		elif entry.is_dir():
			# should be a single DPX dir with only dpx files in it
			filePattern,startNumber,file0 = parse_sequence_folder(entry.path)

	try:
		framerate = get_framerate(file0)
	except:
		framerate = None

	return audioPath,filePattern,startNumber,framerate

def parse_sequence_folder(dpxPath):
	'''
	Grab some information needed for ffmpeg transcoding of an image sequence:
		* the /path/plus/file_%6d.dpx type pattern needed for ffmpeg
		* the starting number of the sequence
		* the /path/to/first/file in the sequence
	'''
	files = []
	scan = os.scandir(dpxPath)
	for entry in scan:
		files.append(entry.path)
	files.sort()
	file0 = files[0]
	match = re.search(r'(.*)(\d{7})(\..+)',file0)
	fileBase = match.group(1)
	startNumber = match.group(2)
	numberOfDigits = len(startNumber)
	extension = match.group(3)
	filePattern = "{}%0{}d{}".format(fileBase,numberOfDigits,extension)
	# print(filePattern,startNumber,file0)
	return filePattern,startNumber,file0

#
# END FILE CHECK STUFF 
#
################################################################

################################################################
#
# SYSTEM / ENVIRONMENT STUFF
#
def get_system():
	if sys.platform.startswith("darwin"):
		return "mac"
	elif sys.platform.startswith("win"):
		return "windows"
	elif sys.platform.startswith("linux"):
		return "linux"
	else:
		return False

def system_info():
	info = platform.uname()
	systemDict = dict(info._asdict())
	systemString = ""
	systemDict['ffmpeg version'] = get_ffmpeg_version()
	systemDict['mediainfo version'] = get_mediainfo_version()
	# format a string to be returned with each bit of info on a new line
	for k,v in systemDict.items():
		systemString += "{} : {}\n".format(k,v)

	return systemString

def get_node_name():
	nodeName = platform.uname().node

	return nodeName

def timestamp(style=None):
	knownStyles = ['iso8601','YMD','now','8601-filename']
	if style in knownStyles:
		if style == 'iso8601':
			timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
		elif style == 'YMD':
			timestamp = str(date.today())
		elif style == '8601-filename':
			timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
		elif style == 'now':
			timestamp = time.strftime("%Y%m%d_%H%M%S")
		return timestamp
	else:
		return str(date.today())

def get_caller():
	caller = sys.argv[0]
	caller = os.path.splitext(caller)
	return caller

def get_ffmpeg_version():
	call = subprocess.check_output(['ffmpeg','-version'])
	version = call.decode('utf-8').split()[2]
	return version

def get_mediainfo_version():
	call = subprocess.check_output(['mediainfo','--version'])
	version = ' '.join(call.decode('utf-8').split())
	return version

def set_ffreport(dest,caller):
	ffmpegVersion = get_ffmpeg_version()
	os.environ["FFREPORT"] = "file="+os.path.join(dest,"ffmpeg-"+ffmpegVersion+"_"+timestamp('now')+"_"+caller+".txt")
	return "set FFREPORT to "+dest

def unset_ffreport():
	del os.environ["FFREPORT"]

def get_unix_ip():
	# totally stolen from mmfunctions
	ifconfig = subprocess.Popen(['ifconfig'],stdout=subprocess.PIPE)
	grep = subprocess.Popen(['grep','inet '],stdin=ifconfig.stdout,stdout=subprocess.PIPE)
	tail = subprocess.Popen(['tail','-n1'],stdin=grep.stdout,stdout=subprocess.PIPE)
	thestuff = subprocess.Popen(['cut','-d',' ','-f2'],stdin=tail.stdout,stdout=subprocess.PIPE)
	ip = thestuff.communicate()[0].decode().rstrip()
	return ip

def boolean_answer(string):
	thumbsUp = ['YES','Yes','yes','y','Y',True,1,'True','1']
	thumbsDown = ['NO','No','no','n','N',False,0,'False','0']
	if string in thumbsUp:
		return True
	elif string in thumbsDown:
		return False
	else:
		print("Not a Boolean answer... try again.")
		return "Not Boolean"

def sanitize_dragged_linux_path(var):
	if get_system() == 'linux':
		if len(var) >= 3 and var[0] == var[-1] == "'":
			var = var[1:-1]
			return var

		else:
			print("???")
			return var
	else:
		return var

def gcp_test():
	'''
	test that  `gcp` is installed and get the path for the binary.
	test for a dbus error on linux and add `dbus-launch` if needed.
	'''
	whichGcp = subprocess.run(['which','gcp'],stdout=subprocess.PIPE)
	gcpPath = whichGcp.stdout.decode().rstrip()
	gcpCommand = [gcpPath]
	if gcpPath == '':
		print('gcp is not installed.')
	else:
		tryGcp = subprocess.run(gcpCommand,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		if "DBusException" in tryGcp.stderr.decode():
			gcpCommand.insert(0,"dbus-launch")

	return gcpCommand

def recursive_chmod(path,mode=0o777):
	chmodded = False
	try:
		os.chmod(path,mode)
		chmodded = True
		for root,dirs,files in os.walk(path):
			for directory in dirs:
				try:
					os.chmod(os.path.join(root,directory),mode)
					chmodded = True
				except:
					chmodded = False
			
			for f in files:
				try:
					os.chmod(os.path.join(root,f),mode)
					chmodded = True
				except:
					chmodded = False

	except:
		chmodded = False
	
	return chmodded

def remove_hidden_system_files(inputPath):
	removed = []
	dont_remove = ['.git','.tmp.drivedownload']
	for root,dirs,files in os.walk(inputPath):
		for f in os.listdir(root):
			if f.startswith('.'):
				# weird list comprehension to make sure not to delete
				# files accidentally - checks for .git/gitignore 
				# and Drive hidden files; can add to list!!
				if not any(
					[x for x in f if (f in dont_remove) or (
						[x for x in dont_remove if x in f]
						)
					]
					):
						target = os.path.join(root,f)
						os.remove(target)
						removed.append(target)
						print("removed a system file at {}".format(target))
		for _dir in dirs:
			for f in os.listdir(os.path.join(root,_dir)):
				if f.startswith('.'):
					if not any(
					[x for x in f if (f in dont_remove) or (
						[x for x in dont_remove if x in f]
						)
					]
					):
						target = os.path.join(root,_dir,f)
						removed.append(target)
						os.remove(target)
						print("removed a system file at {}".format(target))

	return removed

def get_desktop():
	desktop = os.path.expanduser("~/Desktop")
	return desktop

def get_filesystem_id(path):
	'''
	input a path and return the filesystem id
	* use to compare filesystem identities for `mv` vs `rsync` 
		when running moveNcopy
	'''
	fs_id = os.stat(path).st_dev
	return fs_id

#
# SYSTEM / ENVIRONMENT STUFF
#
################################################################

today = str(date.today())
now = timestamp('now')
iso8601 = timestamp('iso8601')
pymmConfig = read_config()
# pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
# pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')
