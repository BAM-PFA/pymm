#!/usr/bin/env python3

#get config settings??

import json
import subprocess
from datetime import date
from ffmpy import FFprobe, FFmpeg

today = date.today()
logPath =  



def ingest_log(mediaID,status,message):
	logfile = logdir+mediaID+today+"log.txt"
	with open(logfile,'w+') as logfile:
		# LOG SOME SHIT


def pymm_log(filename,mediaID,operator,message,status):
	# mm log content = echo $(_get_iso8601)", $(basename "${0}"), ${STATUS}, ${OP}, ${MEDIAID}, ${NOTE}" >> "${MMLOGFILE}"
	with open(systemLog,'w+') as log:
		if status == 'STARTING':
			prefix = ('#'*50)+'\r\r'
			suffix = ''
		elif status == 'ENDING' or status == 'ABORTING':
			prefix = ''
			suffix = '\r\r'+('#'*50)
		else:
			prefix = ''
			suffix = ''
		log.write(prefix,today+' '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+' STATUS: '+status+suffix)

def cleanup():
	status = 'ABORTING'
	system_log(mediaID,status,"Something went wrong and the process was aborted.")
	exit()

def is_video(mediaID):
	ffprobe = FFprobe(
	inputs={mediaID:'-show_streams -select_streams v:0'}
	).run(stdout=subprocess.PIPE)
	if json.loads(ffprobe[0]decode('utf-8'))== something:  #WHATEVER THE index value is supposed to be
		return True
	else: 
		return False
