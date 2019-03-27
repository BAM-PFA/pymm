#!/usr/bin/env python3
# standard library modules
import os

# local modules
import dbAccess
import dbReporters
import pymmFunctions

def check_pymm_log_exists():
	# open a local instance of config here in case 
	# it has changed since importing this file
	pymmConfig = pymmFunctions.read_config()
	pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
	pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')
	# sys.exit()
	opener = (
		((("#"*75)+'\n')*2)+((' ')*4)+'THIS IS THE LOG FOR PYMEDIAMICROSERVICES'
		'\n\n'+((' ')*4)+'THIS VERSION WAS STARTED ON '+pymmFunctions.today+'\n'+((("#"*75)+'\n')*2)+'\n'
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
			desktop = pymmFunctions.get_desktop()
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

def ingest_log(CurrentIngest,event,outcome,status):
	stamp = pymmFunctions.timestamp("iso8601")

	canonicalName = CurrentIngest.InputObject.canonicalName
	inputPath = CurrentIngest.InputObject.inputPath
	tempID = CurrentIngest.InputObject.tempID
	user = CurrentIngest.ProcessArguments.user
	filename = CurrentIngest.InputObject.filename
	ingestLogPath = CurrentIngest.ingestLogPath


	if event == "ingestion start":
		stamp = ("#"*50)+"\n\n"+stamp+"\n\n"
		systemInfo = CurrentIngest.systemInfo
		workingDir = CurrentIngest.ProcessArguments.outdir_ingestsip
		ingestUUID = CurrentIngest.ingestUUID
		stuffToLog = [
			stamp,
			"Event Type: ingestion start\n",
			"Object Canonical Name: {}\n".format(canonicalName),
			"Object Input Filepath: {}\n".format(inputPath),
			"Object Temp ID: {}\n".format(tempID),
			"Ingest UUID: {}\n".format(ingestUUID),
			"Ingest Working Directory: {}\n".format(workingDir),
			"Operator: {}\n".format(user),
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
			"Operator: {} | ".format(user),
			"Object Canonical Name: {} | ".format(canonicalName)
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

def pymm_log(CurrentIngest,event,outcome,status):
	check_pymm_log_exists()
	pymmConfig = pymmFunctions.read_config()
	pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
	pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')
	stamp = pymmFunctions.timestamp('iso8601')
	systemInfo = CurrentIngest.systemInfo

	objectRootPath = CurrentIngest.InputObject.inputPath
	canonicalName = CurrentIngest.InputObject.canonicalName
	
	user = CurrentIngest.ProcessArguments.user
	ingestUUID = CurrentIngest.ingestUUID
	tempID = CurrentIngest.InputObject.tempID
	workingDir = CurrentIngest.ProcessArguments.outdir_ingestsip

	prefix = ''
	suffix = '\n'
	# I think basename gets updated depending on what is getting logged... ? @fixme
	basename = os.path.basename(objectRootPath)
	if status == 'STARTING':
		prefix = ('&'*50)+'\n\n'
		stuffToLog = [
			prefix,
			stamp,
			"\nEvent type: Ingestion start\n",
			"Object canonical name: {}\n".format(canonicalName),
			"Object filepath: {}\n".format(objectRootPath),
			"Ingest UUID: {}\n".format(ingestUUID),
			"Operator: {}\n".format(user),
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

def log_event(CurrentIngest,event,outcome,status):
	'''
	log an event to all logs: database, system log, ingest log
	'''
	pymm_log(
		CurrentIngest,
		event,
		outcome,
		status
		)
	ingest_log(
		CurrentIngest,
		event,
		outcome,
		status
		)
	eventID = insert_event(
		CurrentIngest,
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
		CurrentIngest,
		event,
		outcome,
		status
		)
	eventID = insert_event(
		CurrentIngest,
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

##############################################
##############################################

# DATABASE STUFF

##############################################
##############################################
def insert_object(CurrentIngest,objectCategory,objectCategoryDetail):
	user = CurrentIngest.ProcessArguments.user
	theObject = CurrentIngest.currentTargetObject

	if CurrentIngest.ProcessArguments.databaseReporting == True:
		# init an insertion instance
		objectInsert = dbReporters.ObjectInsert(
			user,
			theObject,
			objectCategory,
			objectCategoryDetail
			)
		try:
			# report the details to the db
			objectIdentifierValueID = objectInsert.report_to_db()
			print(objectInsert.user)
			del objectInsert
		except:
			print("CAN'T MAKE DB CONNECTION")
			pymm_log(
				CurrentIngest,
				event = "connect to database",
				outcome = "NO DATABASE CONNECTION!!!",
				status = "WARNING"
				)
			objectIdentifierValueID = None
			CurrentIngest.ProcessArguments.databaseReporting = False
	else:
		objectIdentifierValueID = None
	# update the processingVars with the unique db ID of the object
	CurrentIngest.InputObject.componentObjectData[theObject] = {}
	CurrentIngest.InputObject.componentObjectData[theObject]['databaseID'] = str(
		objectIdentifierValueID
		)
	# set the object category in component object data
	CurrentIngest.InputObject.componentObjectData[theObject]\
		['objectCategory'] = objectCategory
	CurrentIngest.InputObject.componentObjectData[theObject]\
		['objectCategoryDetail'] = objectCategoryDetail

	return True

def insert_event(CurrentIngest,eventType,outcome,status):
	# this is the THING the event is being performed on
	theObject = CurrentIngest.currentTargetObject

	# get the name of the computer
	computer = CurrentIngest.ProcessArguments.computer
	# get the name of the program, script, or function doing the event
	callingAgent = CurrentIngest.caller
	user = CurrentIngest.ProcessArguments.user

	objectID = CurrentIngest.InputObject.componentObjectData[theObject]['databaseID']
	if CurrentIngest.ProcessArguments.databaseReporting == True:
		#insert the event
		eventInsert = dbReporters.EventInsert(
			eventType,
			objectID,
			theObject,
			pymmFunctions.timestamp('iso8601'),
			status,
			outcome,
			callingAgent,
			computer,
			user,
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
	if processingVars['databaseReporting'] != True:
		return processingVars
	user = processingVars['user']
	for _object,chars in CurrentIngest.InputObject.componentObjectData.items():
		data = CurrentIngest.InputObject.componentObjectData[_object]
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
	# if processingVars['databaseReporting'] == True:
	# 	pass
	# else:
	# 	return None
	inputFile = processingVars['filename']
	objectID = CurrentIngest.InputObject.componentObjectData[inputFile]['databaseID']
	objectIDValue = processingVars['filename']
	eventDetailCallingFunc = processingVars['caller']
	messageDigestFilepath = processingVars['inputPath']
	
	if processingVars['databaseReporting'] == True:
		eventTimestamp = get_event_timestamp(
			eventID,
			processingVars['user']
			)

		if not eventTimestamp:
			eventDateTime = None
		else:
			eventDateTime = eventTimestamp

		fixityInsert = dbReporters.FixityInsert(
			processingVars['user'],
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
