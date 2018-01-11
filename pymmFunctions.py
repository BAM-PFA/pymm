#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices
#
# this is a set of functions used by pymm scripts
#

import json
import subprocess
import os
import sys
import configparser
import shutil
from datetime import date
import time
from ffmpy import FFprobe, FFmpeg

today = str(date.today())
now = time.strftime("%Y-%m-%d_%H:%M:%S")

################################################################
# 
# CONFIG CHECK STUFF
#
def read_config():
	pymmDirectory = os.path.dirname(os.path.abspath(__file__))
	configPath = os.path.join(pymmDirectory,'config','config.ini') 
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
	requiredPaths = {'outdir_ingestfile':'the ingestfile output path','aip_storage':'the AIP storage path',
					'resourcespace_deliver':'the resourcespace output path'}
	missingPaths = 0
	for path in requiredPaths.items():
		if not os.path.isdir(pymmConfig['paths'][path[0]]):
			missingPaths += 1
			print('''
				CONFIGURATION PROBLEM:
				You have not yet set a directory for '''+path[0]+'''. Please run pymmConfig.py,
				edit the config file directly,
				or use \'--'''+path[0]+"\' to set "+path[1]+"."
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

def ingest_log(ingestLogPath,mediaID,filename,operator,message,status):
	if message == 'start':
		message = 'onwards and upwards'
		status = 'STARTING TO INGEST '+filename
		startToday = ('#'*50)+'\r\r'+str(date.today())
	with open(ingestLogPath,'a+') as ingestLog:
		ingestLog.write(today+' '+status+'  Filename: '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+'\n')
		# LOG SOME SHIT

def pymm_log(filename,mediaID,operator,message,status):
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
		log.write(prefix+now+' '+'Filename: '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+' STATUS: '+status+suffix+'\n')

def cleanup_package(inputFilepath,packageOutputDir,reason):
	if reason == 'abort ingest':
		status = 'ABORTING'
		message = ("Something went critically wrong and the process was aborted. "
					+packageOutputDir+
					" and all its contents have been deleted."
					)
	pymm_log(inputFilepath,'','',message,status)
	if os.path.isdir(packageOutputDir):
		print(packageOutputDir)
		try:
			shutil.rmtree(packageOutputDir)
		except:
			print("Could not delete the package at "+packageOutputDir+". Try deleting it manually? Now exiting.")
	# sys.exit()
#
# END PYMM ADMIN / LOGGING STUFF 
#
################################################################

################################################################
#
# FILE CHECK STUFF
#
def is_video(inputFilepath):
	# THIS WILL RETURN TRUE IF FILE IS VIDEO BECAUSE
	# YOU ARE TELLING FFPROBE TO LOOK FOR VIDEO STREAM
	# WITH INDEX=0, AND IF v:0 DOES NOT EXIST,
	# ISPO FACTO, YOU DON'T HAVE A RECOGNIZED VIDEO FILE.
	ffprobe = FFprobe(
	inputs={inputFilepath:'-v error -print_format json -show_streams -select_streams v:0'}
	)
	FR = ffprobe.run(stdout=subprocess.PIPE)
	output = json.loads(FR[0].decode('utf-8'))
	try:
		indexValue = output['streams'][0]['index']
		if indexValue == 0:
			return True
	except:
		return False

def is_audio(inputFilepath):
	print("THIS ISN'T A VIDEO FILE\n"
		'¿maybe this is an audio file?')
	# DO THE SAME AS ABOVE BUT '-select_streams a:0'
	# ... HOPEFULLY IF v:0 DOESN'T EXIST BUT a:0 DOES,
	# YOU HAVE AN AUDIO FILE ON YOUR HANDS. WILL HAVE
	# TO CONFIRM... COULD THIS RETURN TRUE IF v:0 IS BROKEN/CORRUPT?
	ffprobe = FFprobe(
	inputs={inputFilepath:'-v error -print_format json -show_streams -select_streams a:0'}
	)
	FR = ffprobe.run(stdout=subprocess.PIPE)
	output = json.loads(FR[0].decode('utf-8'))
	try:
		indexValue = output['streams'][0]['index']
		if indexValue == 0:
			print("This appears to be an audio file!")
			return True
	except:
		print("THIS DOESN'T SMELL LIKE AN AUDIO FILE EITHER")
		return False

def is_av(inputFilepath):
	_is_video = is_video(inputFilepath)
	_is_audio = is_audio(inputFilepath)
	if not is_video or is_audio:
		print("THIS DOES NOT SMELL LIKE AN AV FILE SO WHY ARE WE EVEN HERE?")
		return False
	else:
		return True

def is_dpx_sequence(inputFilepath):
	# MAYBE USE A CHECK FOR DPX INPUT TO DETERMINE A CERTAIN OUTPUT
	# AUTOMATICALLY? 
	if os.path.isdir(inputFilepath):
		for root,dirs,files in os.walk(inputFilepath):
			print("WELL SELL ME A PICKLE AND CALL ME SALLY")


def phase_check(inputFilepath):
	# THIS PRINTS THE LAVFI.APHASEMETER.PHASE VALUE PLUS 'PTS_TIME' VALUE:
	#
	# [Parsed_ametadata_1 @ 0x7fd720d01dc0] frame:128  pts:131072  pts_time:2.97215
	# [Parsed_ametadata_1 @ 0x7fd720d01dc0] lavfi.aphasemeter.phase=-0.634070
	# 
	# GOING TO HAVE TO RETURN TO THIS ONE LATER.
	ffpmpeg = FFmpeg(
		inputs={'''
		/path/to/file':'-af aphasemeter=video=0,ametadata=print:key=lavfi.aphasemeter.phase -f null -'
		'''
		}
		)

def check_policy(ingestType,inputFilepath):
	print('do policy check stuff')
	policyStatus = "result of check against mediaconch policy"
	return policyStatus
#
# END FILE CHECK STUFF 
#
################################################################

################################################################
#
# FILE MOVE STUFF -- @fixme : investigate borrowing file transfer code from UCSB or IFI
#
def check_write_permissions(destination):
	# check out IFI function: https://github.com/kieranjol/IFIscripts/blob/master/copyit.py#L43
	return True

def copy_file(inputFilepath,destination):
	# GET A HASH, RSYNC THE THING, GET A HASH OF THE DESTINATION FILE, CZECH THE TWO AND RETURN TRUE/FALSE
	return True

def copy_dir(inputDir,destination):
	if os.path.isdir(destination):
		for _,_,_file in os.walk(inputDir):
			copy_file(_file)
	else:
		print("the destination may or may not be a real directory, OOPS")
		return False
	# MAKE A BAG? HASH THE BAG? CHECK HASH OF DESTIATION BAG?

#
# END FILE MOVE STUFF
#
################################################################

pymmConfig = read_config()
pymmLogDir =  pymmConfig['logging']['pymm_log_dir']
pymmLogPath = os.path.join(pymmLogDir,'pymm_log.txt')