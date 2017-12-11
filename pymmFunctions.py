#!/usr/bin/env python3

#get config settings??

import json
import subprocess
import os
import sys
import configparser
from datetime import date
from ffmpy import FFprobe, FFmpeg

################################################################
# READ config.ini OR MAKE ONE IF IT DOESN'T EXIST YET
pymmDirectory = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(pymmDirectory,'config/config.ini') 
if not os.path.isfile(configPath):
	open(configPath,'x')
	with open(configPath,'w+') as config:
		config.write("[paths]\routdir_ingestfile:\raip_storage:\rresourcespace_deliver:\rpymm_scriptdir:\
			\r\r[database settings]\rpymm_db:\rpymm_db_user_profile:\rpymm_db_name:\
			\r\r[logging]\rpymm_log_dir:")
globalConfig = configparser.SafeConfigParser()
globalConfig.read(configPath)

# check for the existence of required output paths
requiredPaths = {'outdir_ingestfile':'the ingestfile output path','aip_storage':'the AIP storage path','resourcespace_deliver':'the resourcespace output path'}
missingPaths = 0
for path in requiredPaths.items():
	if not os.path.isdir(globalConfig['paths'][path[0]]):
		missingPaths += 1
		print("CONFIGURATION PROBLEM:\n\
			You have not yet set a directory for "+path[0]+". Please edit the config file or\n\
			use '--"+path[0]+"' to set "+path[1])
if missingPaths > 0:
	print("You are missing some required file paths and we have to quit. Sorry.")
	exit()
################################################################

today = str(date.today())
pymmLogPath =  globalConfig['logging']['pymm_log_dir']+'/pymm_log.txt'

def check_pymmLogExists ():
	if not os.path.isfile(pymmLogPath):
		print('wait i need to make a logfile')
		open(pymmLogPath,'x')
	with open(pymmLogPath,'w+') as pymmLog:
		pymmLog.write(((("#"*75)+'\r')*2)+((' ')*4)+'THIS IS THE LOG FOR PYMEDIAMICROSERVICES\
\r\r'+((' ')*4)+'THIS COPY WAS STARTED ON '+today+'\r'+((("#"*75)+'\r')*2)+'\r')

def ingest_log(ingestLogPath,mediaID,filename,operator,message,status):
	if message == 'start':
		message = 'onwards and upwards'
		status = 'STARTING TO INGEST '+filename
		today = ('#'*50)+'\r\r'+str(date.today())
	with open(ingestLogPath,'a+') as ingestLog:
		ingestLog.write(today+' '+status+'  Filename: '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+'\r')
		# LOG SOME SHIT

def pymm_log(filename,mediaID,operator,message,status):
	# mm log content = echo $(_get_iso8601)", $(basename "${0}"), ${STATUS}, ${OP}, ${MEDIAID}, ${NOTE}" >> "${MMLOGFILE}"
	check_pymmLogExists()
	with open(pymmLogPath,'a+') as log:
		if status == 'STARTING':
			prefix = ('#'*50)+'\r\r'
			suffix = ''
		elif status == 'ENDING' or status == 'ABORTING':
			prefix = ''
			suffix = '\r\r'+('#'*50)
		else:
			prefix = ''
			suffix = ''
		log.write(prefix+today+' '+'Filename: '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+' STATUS: '+status+suffix+'\r')

# def cleanup():
# 	status = 'ABORTING'
# 	pymm_log(mediaID,status,"Something went wrong and the process was aborted.")
# 	exit()

def is_video(inputFile):
	# THIS FOLLOWS THE MM LOGIC BUT I DON'T
	# KNOW ENOUGH TO BE CONVINCED THAT THE 
	# LOGIC IS SOUND. WHAT'S index = 0 ANYWAY?
	ffprobe = FFprobe(
	inputs={inputFile:'-v error -print_format json -show_streams -select_streams v:0'}
	)
	FR = ffprobe.run(stdout=subprocess.PIPE)
	output = json.loads(FR[0].decode('utf-8'))
	indexValue = output['streams'][0]['index']
	if indexValue == 0:
		return True
	else:
		return False
