#!/usr/bin/env python3
#
# these are functions to output metadata files
# and structured data (xml/json)
#

import os
import subprocess
import sys
import json
import argparse
import configparser
import hashlib
# nonstandard libraries:
import xmltodict
# local modules:
import pymmFunctions

def get_mediainfo_report(inputFilepath,destination,_JSON=False):
	basename = pymmFunctions.get_base(inputFilepath)
	# write mediainfo output to a logfile if the destination is a directory
	if os.path.isdir(destination):
		mediainfoOutput = '--LogFile='+os.path.join(destination,basename+'_mediainfo.xml')
		mediainfoXML = subprocess.Popen(['mediainfo',inputFilepath,'--Output=XML',mediainfoOutput],stdout=subprocess.PIPE)
		# yeah it's an OrderedDict, not JSON, but I will grab the Video track and Audio track as JSON later...
		mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])
		if _JSON:
			# videoTrack = mediainfoJSON['Mediainfo']['File']['track'][1]
			return mediainfoJSON    
		else:
			return True
	# otherwise pass something like '' as a destination and just get the raw mediainfo output
	else:
		mediainfoXML = subprocess.Popen(['mediainfo','--Output=XML',inputFilepath],stdout=subprocess.PIPE)
		# print(mediainfoXML.communicate()[0])
		mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])
		if _JSON:
			# print(mediainfoJSON)
			return mediainfoJSON
		else:
			print(destination+" doesn't exist and you didn't say you want the raw mediainfo output.\n"
					"What do you want??")
			return False

def get_track_profiles(mediainfoDict):
	'''
	Get audio and video track profiles to compare for concatenation of files.
	Takes an OrderedDict as retrned by get_mediainfo_report.

	Discard attributes that are not necessary but keep relevant attributes
	that we want to compare between files. Prob can discard even more?
	Hard coded now to look for track[1] (video) and track[2] (audio),
	so presumably if there are additional tracks things will get screwy. 
	'''
	# investigating mac vs linux mediainfo output. this is mac video stream:
	# print(mediainfoDict['MediaInfo']['media']['track'][1])
	problems = 0
	videoAttribsToDiscard = [
		'@type', 'ID', 'Format_Info', 'Format_profile',
		'Format_settings__CABAC', 'Format_settings__ReFrames', 
		'Format_settings__GOP', 'Codec_ID', 'Codec_ID_Info', 'Duration', 
		'Scan_type', 'Bits__Pixel_Frame_', 'Stream_size', 'Language', 
		'Tagged_date', 'Encoded_date'
		]
	audioAttribsToDiscard = [
		'@type', 'ID', 'Codec_ID', 'Duration', 'Stream_size', 
		'Language', 'Encoded_date', 'Tagged_date'
		]
	try:
		videoTrackProfile = mediainfoDict['Mediainfo']['File']['track'][1]
		for attr in videoAttribsToDiscard:
			videoTrackProfile.pop(attr,None)
	except:
		problems += 1
		print("mediainfo problem: either there is no video track or you got some issues")
	try:	
		audioTrackProfile = mediainfoDict['Mediainfo']['File']['track'][2]
		for attr in audioAttribsToDiscard:
			audioTrackProfile.pop(attr,None)
	except:
		problems += 1
		print("mediainfo problem: either there is no audio track or you got some issues")
	if problems == 0:
		return json.dumps(videoTrackProfile),json.dumps(audioTrackProfile)
	else:	
		print("there might be problems")
		if videoTrackProfile:
			return json.dumps(videoTrackProfile)
		elif audioTrackProfile:
			return json.dumps(audioTrackProfile)
		else:
			return "",""

def hash_file(inputFilepath,algorithm='md5',blocksize=65536):
	# STOLEN DIRECTLY FROM UCSB BRENDAN COATES: https://github.com/brnco/ucsb-src-microservices/blob/master/hashmove.py
	hasher = hashlib.new(algorithm)
	with open(inputFilepath,'rb') as infile:
		buff = infile.read(blocksize) # read the file into a buffer cause it's more efficient for big files
		while len(buff) > 0: # little loop to keep reading
			hasher.update(buff) # here's where the hash is actually generated
			buff = infile.read(blocksize) # keep reading
	return hasher.hexdigest()

def make_hashdeep_manifest(inputPath):
	manifest = "hello i'm a mainfest"

def make_frame_md5(inputFilepath,metadataDir):
	print('making frame md5')
	print(metadataDir)
	if not pymmFunctions.is_av(inputFilepath):
		# FUN FACT: YOU CAN RUN FFMPEG FRAMEMD5 ON A TEXT FILE!!
		print(inputFilepath+" IS NOT AN AV FILE SO WHY ARE YOU TRYING TO MAKE A FRAME MD5 REPORT?")
		return False
	else:
		md5File = pymmFunctions.get_base(inputFilepath)+"_frame-md5.txt"
		frameMd5Filepath = os.path.join(metadataDir,md5File)
		frameMd5Command = ['ffmpeg','-i',inputFilepath,'-f','framemd5',frameMd5Filepath]
		output = subprocess.Popen(frameMd5Command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		try:
			out,err = output.communicate()
			if err:
				print(err.decode('utf-8'))
			return frameMd5Filepath
		except:
			return False

def main():
	config = pymmFunctions.read_config() # THIS IS PROBABLY NOT GOING TO BE NEEDED

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--inputFilepath',help='path of input file')
	parser.add_argument('-m','--mediainfo',action='store_true',help='generate a mediainfo sidecar file')
	parser.add_argument('-f','--frame_md5',action='store_true',help='make frame md5 report')
	parser.add_argument('-j','--getJSON',action='store_true',help='get JSON output as applicable')
	parser.add_argument('-d','--destination',help='set destination for output metadata files')
	args = parser.parse_args()
	
	inputFilepath = args.inputFilepath
	destination = args.destination
	frame_md5 = args.frame_md5
	mediainfo_report = args.mediainfo
	getJSON = args.getJSON

	if not inputFilepath:
		print("\n\nHEY THERE, YOU NEED TO SET AN INPUT FILE TO RUN THIS SCRIPT ON.\rNOW EXITING")
		sys.exit()
	if not destination:
		print('''
			YOU DIDN'T TELL ME WHERE TO PUT THE OUTPUT OF THIS SCRIPT,
			SO WE'LL PUT ANY SIDECAR FILES IN THE SAME DIRECTORY AS YOUR INPUT FILE.
			''')
		destination = os.path.dirname(os.path.abspath(inputFilepath))
	# print(destination,inputFilepath)
	# fileHash = hash_file(inputFilepath)
	# print(fileHash)
	if mediainfo_report:
		get_mediainfo_report(inputFilepath,destination,getJSON)
	if frame_md5:
		frameMd5Filepath = make_frame_md5(inputFilepath,destination)
		print(frameMd5Filepath)

if __name__ == '__main__':
	main()
