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
try: 
	import dbReporters
	import loggers
	import makeMetadata
	import MySQLqueries
	import directoryScanner
except:
	from . import dbReporters
	from . import loggers
	from . import makeMetadata
	from . import MySQLqueries
	from . import directoryScanner


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
try:
	import dbAccess
except:
	from . import dbAccess
def cleanup_package(CurrentIngest,pathForDeletion,reason,outcome=None):
	# print(pathForDeletion)
	inputType = CurrentIngest.InputObject.inputType
	dontDelete = False

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
		# put the things back
		try:
			if inputType == 'file':
				_object = [
					thing.path for thing in 
					os.scandir(CurrentIngest.packageObjectDir)
					if thing.is_file()
					][0]
				if os.path.isfile(CurrentIngest.InputObject.inputPath):
					pass
				else:
					shutil.move(
						_object,
						CurrentIngest.InputObject.inputParent
						)
			else:
				if not os.path.isdir(CurrentIngest.InputObject.inputPath):
					os.mkdir(CurrentIngest.InputObject.inputPath)
				for _object in os.scandir(CurrentIngest.packageObjectDir):
					if _object.name not in ('resourcespace','prores'):
						shutil.move(
							_object.path,
							CurrentIngest.InputObject.inputPath
							)
		except:
			dontDelete = True
			outcome = ("COULD NOT REPLACE ORIGINAL COPIES!! \
				NOT DELETING {}!".format(pathForDeletion))
			print(outcome)

	elif reason == 'done':
		status = 'OK'
		event = 'deletion'
		outcome = (
			"Deleting original copies "
			"of object at {}".format(pathForDeletion)
			)

	if os.path.isdir(pathForDeletion) and dontDelete == False:
		try:
			shutil.rmtree(pathForDeletion)
		except:
			outcome = (
				"Could not delete the package at "
				+pathForDeletion+
				". Try deleting it manually?"
				)
			print(outcome)

	CurrentIngest.caller = 'pymmFunctions.cleanup_package()'
	loggers.end_log(
		CurrentIngest,
		event,
		outcome,
		status
		)

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
		'-v','error',
		'-i',inputPath,
		'-print_format','json',
		'-show_streams',
		'-select_streams','v'
		]
	try:
		probe = subprocess.run(ffprobe,stdout=subprocess.PIPE)
		out = probe.stdout.decode('utf-8')
		output = json.loads(out)
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
		'-v','error',
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
			if os.path.isdir(inputPath):
				# if it's a folder, see if it's a DPX sequence
				try:
					# test for a valid folder structure
					_is_dpx,details = directoryScanner.main(inputPath)
					print(_is_dpx)
					print(details)
				except:
					print('error scanning input!')
					return False
				if _is_dpx:
					if _is_dpx == 'dpx':
						print('THIS IS AN IMAGE SEQUENCE!')
						return 'DPX'
					else:
						# if it passes the folder structure, run
						# mediainfo to check for dpx contents
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
				else:
					return None
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
		if item.name == 'documentation':
			break
		if item.is_dir():
			print(item.path)
			if item.name.lower() == 'dpx':
				_is_dpx = is_dpx_sequence(item.path)
				if not _is_dpx:
					failedDirs.append(item.path)
					failures += 1
			else:
				failedDirs.append(item.path)
				failures += 1
			
	if failures > 0:
		return False, failedDirs
	else:
		return True, failedDirs

def is_dpx_sequence(inputPath):
	'''
	run mediainfo on the 'dpx' folder
	'''
	_is_dpx_av = False
	try:
		format = get_mediainfo_value(inputPath,'General','Format')
		if any([('dpx','directory') for x in format.lower()]):
			_is_dpx_av = True
		else:
			pass
	except:
		_is_dpx_av = False

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
		if distance > 15:
			outliers += 1
			outlierList.append(name)

	return outliers,outlierList

def check_for_outliers(inputPath):
	'''
	Use distance check function to approve/deny
	viability of directory ingest.
	'''
	goodNames = True
	outliers, outlierList = check_dir_filename_distances(inputPath)
	if outliers > 0: 
		outlierListString = '\n'.join(outlierList)
		warning = (
			"Hey, there are {} files that seem like they might not belong"\
			" in the input directory. If you think this is incorrect, check"\
			" the filenames below. Maybe make them more consistent.\n"\
			"Here's a list of possible outliers:\n{}".format(
				str(outliers),
				outlierListString
				)
			)		
		return False,outlierList
	else:
		return True,None

def list_files(_input):
	'''
	Take in an absolute path of a directory and return a list of the paths
	for everything in it.
	'''
	if os.path.isdir(_input):
		source_list = []
		for _file in os.listdir(_input):
			if os.path.isdir(_file) and not _file.lower() == 'documentation':
				print("you have unexpected subdirectories!")
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
	directoryScanner.main(inputPath)
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

	# try/except test to catch no audio path in silent DPX scans
	try:
		audioPath = audioPath
	except:
		audioPath = None

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
	match = re.search(r'(.*)(\d{6}|\d{7})(\..+)',file0)
	fileBase = match.group(1)
	startNumber = match.group(2)
	numberOfDigits = len(startNumber)
	extension = match.group(3)
	filePattern = "{}%0{}d{}".format(fileBase,numberOfDigits,extension)
	# print(filePattern,startNumber,file0)
	return filePattern,startNumber,file0

def get_stream_count(inputPath,_type="video"):
	'''
	Count the data streams present in an av file.
	Specify _type as "audio" or "video" (default)
	For example, a file with audio track(s) should return one line per stream:
		'streams.stream.0.index=1'
	Tally these lines and take that as the count of audio streams. 
	'''

	probeCommand = [
		'ffprobe', '-hide_banner',
		inputPath,
		'-select_streams', _type[:1], # get the first letter of _type (a or v)
		'-show_entries', 'stream=index',
		'-of', 'flat'
		]
	count = None
	try:
		count = 0
		probe = subprocess.run(
			probeCommand,
			stdout=subprocess.PIPE, # this should return a list of streams
			stderr=subprocess.PIPE
			)
		count += len(probe.stdout.splitlines())
	except Exception as e:
		print(e)
		pass

	return count

def check_dual_mono(inputPath):
	'''
	Check if a video file has the first two audio streams mono
	inspired by `mmfunctions` _has_first_two_tracks_mono()
	'''
	probes = []
	dualMono = None
	for index in range(2):		
		probe = [
		'ffprobe',
		inputPath,
		"-show_streams",
		"-select_streams","a:{}".format(index)
		]
		out = subprocess.run(
			probe,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
			)
		probes.append(out)
	probe1 = probes[0]
	probe2 = probes[1]
	stream1Channels = [
		x for x in probe1.stdout.decode().splitlines() \
			if x.startswith('channels=')
		]
	stream2Channels = [
		x for x in probe2.stdout.decode().splitlines() \
			if x.startswith('channels=')
		]
	if stream1Channels == stream2Channels == ['channels=1']:
		dualMono = True
	else:
		dualMono = False

	return dualMono

def check_empty_mono_track(inputPath):
	'''
	Check if one mono audio track is basically empty.
	Intended usage is with a dual mono file so we can remove
	an empty track and use the non-empty one as track 1.
	
	NB: setting "empty" as below -50dB RMS (root mean square) level,
	  this could be tweaked!
	'''
	# ffmpeg -i /Users/michael/Desktop/test_files/illuminated_extract.mov -map 0:a:1 -af astats -f null -
	empty = {0:False,1:False}

	for stream in range(2):
		command = [
		'ffmpeg',
		'-i',inputPath,
		'-map','0:a:{}'.format(stream),
		'-af','astats',
		'-f','null','-'
		]
		# print(command)
		output = subprocess.run(
			command,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
			)
		stats = [line for line in output.stderr.decode().splitlines()]
		chopped = [re.sub(r'\[Parsed_astats.+\]\ ','',line) for line in stats]
		leveldB = [
			int(float(line.replace('RMS level dB: ',''))) for line in chopped \
				if line.startswith('RMS level dB: ')
			]
		# print(leveldB)
		try:
			if leveldB[1] < -50:
				empty[stream] = True
		except:
			pass

	# print(empty)
	returnValue = None
	count = 0
	if any([v for v in empty.values()]):		
		for k,v in empty.items():
			if not v:
				returnValue = k # return the stream id to keep
			else:
				count += 1
		if count > 1:
			returnValue = 'both'
	else:
		returnValue = None

	return returnValue


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
