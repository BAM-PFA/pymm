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
scriptDirectory = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(scriptDirectory,'config/config.ini') 
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

today = date.today()
logPath =  globalConfig['logging']['pymm_log_dir']

# def ingest_log(mediaID,status,message):
# 	logfile = logdir+mediaID+today+"log.txt"
# 	with open(logfile,'w+') as logfile:
# 		# LOG SOME SHIT

# def pymm_log(filename,mediaID,operator,message,status):
# 	# mm log content = echo $(_get_iso8601)", $(basename "${0}"), ${STATUS}, ${OP}, ${MEDIAID}, ${NOTE}" >> "${MMLOGFILE}"
# 	with open(systemLog,'w+') as log:
# 		if status == 'STARTING':
# 			prefix = ('#'*50)+'\r\r'
# 			suffix = ''
# 		elif status == 'ENDING' or status == 'ABORTING':
# 			prefix = ''
# 			suffix = '\r\r'+('#'*50)
# 		else:
# 			prefix = ''
# 			suffix = ''
# 		log.write(prefix,today+' '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+' STATUS: '+status+suffix)

# def cleanup():
# 	status = 'ABORTING'
# 	pymm_log(mediaID,status,"Something went wrong and the process was aborted.")
# 	exit()

def is_video(mediaID):
	ffprobe = FFprobe(
	inputs={mediaID:'-show_streams -select_streams v:0'}
	).run(stdout=subprocess.PIPE)
	if json.loads(ffprobe[0].decode('utf-8')) == something:  #WHATEVER THE index value is supposed to be
		return True
	else: 
		return False
