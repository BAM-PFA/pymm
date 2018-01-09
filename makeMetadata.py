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
import argparse
import configparser
import pymmFunctions

def get_mediainfo_report(inputFilepath,metadataDir):
	basename = os.path.basename(inputFilepath)
	if os.path.isdir(metadataDir):
		# @fixme CHANGE TO ONLY MAKE FILE IF IT'S NEEDED
		# MAYBE MAKE A TEMP XML FILE THAT CAN BE READ REPEATEDLY IF NEEDED? THEN DELETED?
		mediainfoOutput = '--LogFile='+os.path.join(metadataDir,basename+'_mediainfo.xml')
	else:
		mediainfoOutput = None
		
	mediainfoXML = subprocess.Popen(['mediainfo',inputFilepath,'--Output=XML',mediainfoOutput],stdout=subprocess.PIPE)
	mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])

	return mediainfoJSON    # @fixme CHANGE TO RETURN THIS ONLY IF IT'S NEEDED
							# OR MAYBE SPLIT JSON/TEXT CREATION

def make_frame_md5(inputFile,metadataDir):
	print("AND HERE IS WHERE YOU WOULD DO SOME NEAT MD5 STUFF")
	
	with open(os.path.join(metadataDir,'metadata.md5'),'x') as makethisfile:
		print('make a frame md5 report')
		# SAVE THE FILE TO THE METADATA DIR FOR THE PACKAGE
	return "in json format?"

def main():
	#######################
	#  INITILIZE STUFF
	config = pymmFunctions.read_config() # THIS IS PROBABLY NOT GOING TO BE NEEDED

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--inputFilepath',help='path of input file')
	parser.add_argument('-m','--mediainfo',action='store_true',help='generate a mediainfo sidecar file')
	parser.add_argument('-f','--frame_md5',action='store_true',help='make frame md5 report')
	parser.add_argument('-d','--destination',help='set destination for output metadata files')
	args = parser.parse_args()
	
	inputFilepath = args.inputFilepath
	destination = args.destination
	frame_md5 = args.frame_md5
	mediainfo_report = args.mediainfo

	if not inputFilepath:
		print("\n\nHEY THERE, YOU NEED TO SET AN INPUT FILE TO RUN THIS SCRIPT ON.\rNOW EXITING")
		sys.exit()
	if not destination:
		print('''
			YOU DIDN'T TELL ME WHERE TO PUT THE OUTPUT OF THIS SCRIPT,
			SO WE'LL PUT ANY SIDECAR FILES IN THE SAME DIRECTORY AS YOUR INPUT FILE.
			''')
		destination = os.path.dirname(os.path.abspath(inputFilepath))
	print(destination,inputFilepath)
	# END INITILIZE STUFF
	#######################

	if mediainfo_report:
		get_mediainfo_report(inputFilepath,destination)
	if frame_md5:
		make_frame_md5(inputFile,destination)

if __name__ == '__main__':
	main()
