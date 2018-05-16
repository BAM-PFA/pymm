#!/usr/bin/env python3
'''
This is a set of functions used by pymm scripts

This file is organized into 4 main sections:
 * CONFIG CHECK STUFF
 * PYMM ADMIN / LOGGING STUFF
 * FILE CHECK STUFF
 * SYSTEM / ENVIRONMENT STUFF

'''
import glob
import json
import subprocess
import os
import sys
import configparser
import shutil
from datetime import date
import time
import hashlib
# nonstandard libraries:
import Levenshtein
from ffmpy import FFprobe, FFmpeg
# local modules:
import premisSQL

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
					'outdir_ingestfile':'the ingestfile output path',
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
	if not os.path.isfile(pymmLogPath):
		print('wait i need to make a logfile')
		if pymmLogDir == '':
			print("CONFIGURATION PROBLEM:\n"
				  "THERE IS NO DIRECTORY SET FOR THE SYSTEM-WIDE LOG.\n"
				  "PLEASE RUN pymmconfig.py OR EDIT config.ini DIRECTLY\n"
				  "TO ADD A VALID DIRECTORY FOR pymm_log.txt TO LIVE IN.\n"
				  "NOW EXITING. BYE!")
			sys.exit()
		else:
			open(pymmLogPath,'x')
			with open(pymmLogPath,'w+') as pymmLog:
				pymmLog.write(
					((("#"*75)+'\n')*2)+((' ')*4)+'THIS IS THE LOG FOR PYMEDIAMICROSERVICES'
					'\n\n'+((' ')*4)+'THIS VERSION WAS STARTED ON '+today+'\n'+((("#"*75)+'\n')*2)+'\n'
					)
	else:
		pass

def ingest_log(message,status,ingestLogPath,tempID,input_name,filename,operator):
	if message == 'start':
		message = 'onwards and upwards'
		status = 'STARTING TO INGEST '+input_name
		startToday = ('#'*50)+'\r\r'+str(date.today())
	with open(ingestLogPath,'a+') as ingestLog:
		if filename == '':
			ingestLog.write(
				iso8601
				+' Status: '+status
				+' Input Name: '+input_name
				+' tempID: '+tempID
				+' operator: '+operator
				+' MESSAGE: '+message+'\n\n')
		else:
			ingestLog.write(
				iso8601
				+' Status: '+status
				+' Input Name: '+input_name
				+' Filename: '+filename
				+' tempID: '+tempID
				+' operator: '+operator
				+' MESSAGE: '+message+'\n\n')
		# LOG SOME SHIT

def pymm_log(filename,tempID,operator,message,status):
	# mm log content = echo $(_get_iso8601)", $(basename "${0}"), ${STATUS}, ${OP}, ${MEDIAID}, ${NOTE}" >> "${MMLOGFILE}"
	check_pymm_log_exists()
	with open(pymmLogPath,'a') as log:
		if status == 'STARTING':
			prefix = ('&'*50)+'\n\n'
			suffix = '\n'
		elif status == 'ENDING' or status == 'ABORTING':
			prefix = ''
			suffix = '\n\n'+('#'*50)
		else:
			prefix = ''
			suffix = '\n'
		log.write(prefix+now+' '+'Filename: '+filename+'  tempID: '+tempID+'  operator: '+operator+'  MESSAGE: '+message+' STATUS: '+status+suffix+'\n')

def cleanup_package(inputPath,packageOutputDir,reason):
	if reason == 'abort ingest':
		status = 'ABORTING'
		message = ("Something went critically wrong and the process was aborted. "
					+packageOutputDir+
					" and all its contents have been deleted."
					)
	pymm_log(inputPath,'','',message,status)
	if os.path.isdir(packageOutputDir):
		print(packageOutputDir)
		try:
			shutil.rmtree(packageOutputDir)
		except:
			print("Could not delete the package at "+packageOutputDir+". Try deleting it manually? Now exiting.")
	# sys.exit()

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

def validate_SIP_structure(SIPpath,canonicalName=None):
	'''
	Check that all the top-level stuff expected in a package exists.
	Don't go too deep... 
	Current expected structure is:
	UUID/
	  UUID/
	    metadata/
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
	    
	  hashdeep_manifest_UUID_iso8601.txt
	'''
	structureValidated = True
	UUID = os.path.basename(SIPpath)
	# define the directories to check
	ingestDir = os.path.join(SIPpath,UUID)
	metadataDir = os.path.join(ingestDir,'metadata')
	logDir = os.path.join(metadataDir,'logs')
	objectMetadataDir = os.path.join(metadataDir,'objects')
	objectDir = os.path.join(ingestDir,'objects')
	dirs = [ingestDir,metadataDir,logDir,objectMetadataDir,objectDir]
	# check that they exist
	# I should log the non-existence of any of these
	# maybe rename the SIP to FAILED-UUID?
	for thing in dirs:
		if not os.path.isdir(thing):
			structureValidated = False
			print("missing {}".format(os.path.basename(thing))) # @logme

	# use glob to search for the existence of
	# 1) hashdeep manifest
	# 2) pbcore xml file
	manfestPattern = os.path.join(SIPpath,'hashdeep_manifest_*')
	manifest = glob.glob(manfestPattern)
	if manifest == []:
		print("missing a hashdeep manifest for the SIP")
		structureValidated = False # @logme
	pbcorePattern = os.path.join(metadataDir,'*_pbcore.xml')
	pbcore = glob.glob(pbcorePattern)
	if pbcore == []:
		print("missing a pbcore xml description for the object")
		structureValidated = False

	return structureValidated

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

def insert_object(operator,identifier,objectCategory):
	try:
		dbConnection = database_connection(operator)
		
		insertObjectSQL = premisSQL.insertObjectSQL
		cursor = do_query(
			dbConnection,
			insertObjectSQL,
			identifier,
			objectCategory
			)
		objectIdentifierValueID = cursor.lastrowid
		return objectIdentifierValueID
	except:
		return False

#
# END PYMM ADMIN / LOGGING STUFF 
#
################################################################

################################################################
#
# FILE CHECK STUFF
#
def is_video(inputPath):
	# THIS WILL RETURN TRUE IF FILE IS VIDEO BECAUSE
	# YOU ARE TELLING FFPROBE TO LOOK FOR VIDEO STREAM
	# WITH INDEX=0, AND IF v:0 DOES NOT EXIST,
	# ISPO FACTO, YOU DON'T HAVE A RECOGNIZED VIDEO FILE.
	ffprobe = 	FFprobe(
				inputs={
				inputPath:'-v error -print_format json -show_streams -select_streams v:0'
				}
				)
	try:
		FR = ffprobe.run(stdout=subprocess.PIPE)
		output = json.loads(FR[0].decode('utf-8'))
		# print(output)
		try:
			indexValue = output['streams'][0]['index']
			if indexValue == 0:
				return True
		except:
			return False
	except:
		return False
	

def is_audio(inputPath):
	print("THIS ISN'T A VIDEO FILE\n"
		'maybe this is an audio file?')
	# DO THE SAME AS ABOVE BUT '-select_streams a:0'
	# ... HOPEFULLY IF v:0 DOESN'T EXIST BUT a:0 DOES,
	# YOU HAVE AN AUDIO FILE ON YOUR HANDS. WILL HAVE
	# TO CONFIRM... COULD THIS RETURN TRUE IF v:0 IS BROKEN/CORRUPT?
	ffprobe = 	FFprobe(
				inputs={
				inputPath:'-v error -print_format json -show_streams -select_streams a:0'
				}
				)
	try:
		FR = ffprobe.run(stdout=subprocess.PIPE)
		output = json.loads(FR[0].decode('utf-8'))
		try:
			indexValue = output['streams'][0]['index']
			if indexValue == 0:
				print("This appears to be an audio file!")
				return True
		except:
			print("THIS DOESN'T SMELL LIKE AN AUDIO FILE EITHER")
			print(output)
			return False
	except:
		print("INVALID FILE INPUT, NOT AUDIO EITHER")
		return False

def is_av(inputPath):
	_is_video = is_video(inputPath)
	if not _is_video:
		_is_audio = is_audio(inputPath)
		if not _is_audio:
			print("THIS DOES NOT SMELL LIKE AN AV FILE SO WHY ARE WE EVEN HERE?")
			return False
	else:
		return True

def is_dpx_sequence(inputPath):
	# MAYBE USE A CHECK FOR DPX INPUT TO DETERMINE A CERTAIN OUTPUT
	# AUTOMATICALLY? 
	if os.path.isdir(inputPath):
		for root,dirs,files in os.walk(inputPath):
			print("WELL SELL ME A PICKLE AND CALL ME SALLY")

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
		if is_av(name):
			names.append(name)
	median = Levenshtein.median(_list)
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
		sys.exit()

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
		return 'mac'
	elif sys.platform.startswith("win"):
		return 'windows'
	elif sys.platform.startswith("linux"):
		return 'linux'
	else:
		return False

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
	gcpCommand = gcpPath
	if gcpPath == '':
		print('gcp is not installed.')
	else:
		tryGcp = subprocess.run([gcpCommand],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		if "DBusException" in tryGcp.stderr.decode():
			gcpCommand = "dbus-launch {}".format(gcpCommand)

	return gcpCommand

#
# SYSTEM / ENVIRONMENT STUFF
#
################################################################

today = str(date.today())
now = timestamp('now')
iso8601 = timestamp('iso8601')
pymmConfig = read_config()
pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')
