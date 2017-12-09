#!/usr/bin/env python3

import configparser
import os

def config():
	################################################################
	# READ config.ini OR MAKE ONE IF IT DOESN'T EXIST YET
	# currentDirectory = os.path.dirname(os.path.abspath(__file__))
	# configPath = os.path.join(currentDirectory,'config.ini') 
	configPath = 'config.ini'
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

if __name__ == '__main__':
	config()