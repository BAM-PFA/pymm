#!/usr/bin/env python3
#
# these are functions to output metadata files
# and structured data (xml/json)
#

import os
import subprocess
import sys
import json
import xmltodict

def get_mediainfo_report(inputFilepath,textOutputDir):
	if os.path.isdir(textOutputDir):
		# @fixme CHANGE TO ONLY MAKE FILE IF IT'S NEEDED
		# MAYBE MAKE A TEMP XML FILE THAT CAN BE READ REPEATEDLY IF NEEDED? THEN DELETED?
		mediainfoOutput = '--LogFile='+os.path.join(textOutputDir,'mediainfo.xml')
	else:
		mediainfoOutput = None

	
	# this would make sense to keep here and call it from ingestfile or wherever.
	# if an output directory is set (like if you are creating an AIP) the text fille
	# gets sent to its happy home and this also returns json that can be accessed to
	# check values like duration, frame count, whatever
		
	
	mediainfoXML = subprocess.Popen(['mediainfo',inputFile,'--Output=XML',mediainfoOutput],stdout=PIPE)
	mediainfoJSON = xmltodict.parse(mediainfoXML)

	return mediainfoJSON    # @fixme CHANGE TO RETURN THIS ONLY IF IT'S NEEDED
							# OR MAYBE SPLIT JSON/TEXT CREATION

def make_frame_md5(inputFile,metadataDir):
	print("AND HERE IS WHERE YOU WOULD DO SOME NEAT MD5 STUFF")
	with open('metadata.md5','x') as makethisfile:
		# SAVE THE FILE TO THE METADATA DIR FOR THE PACKAGE
	return "in json format?"
