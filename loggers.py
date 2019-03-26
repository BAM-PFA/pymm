#!/usr/bin/env python3
# standard library modules
import os


import dbAccess
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


##############################################
##############################################

# DATABASE STUFF

##############################################
##############################################

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

def insert_object(CurrentIngest,objectCategory,objectCategoryDetail):
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
