#!/usr/bin/env python3
'''
these are functions to output metadata files
and structured data (xml/json) about a/v files
'''

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

def get_mediainfo_report(inputPath,destination,_JSON=False):
	basename = pymmFunctions.get_base(inputPath)
	# write mediainfo output to a logfile if the destination is a directory ..
	if os.path.isdir(destination):
		mediainfoOutput = '--LogFile={}_mediainfo.xml'.format(
			os.path.join(destination,basename
				)
			)
		mediainfoXML = subprocess.Popen(
			['mediainfo',inputPath,'--Output=XML',mediainfoOutput],
			stdout=subprocess.PIPE
			)
		# yeah it's an OrderedDict, not JSON, but I will grab the 
		# Video track and Audio track as JSON later
		mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])
		if _JSON:
			return mediainfoJSON    
		else:
			return True
	# ... otherwise pass something like '' as a destination 
	# and just get the raw mediainfo output
	else:
		mediainfoXML = subprocess.Popen(
			['mediainfo','--Output=XML',inputPath],
			stdout=subprocess.PIPE
			)
		mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])
		if _JSON:
			return mediainfoJSON
		else:
			print("{} doesn't exist and you didn't say you "
				"want the raw mediainfo output.\n"
				"What do you want??".format(destination))
			return False

def get_mediainfo_pbcore(inputPath):
	call = subprocess.Popen(
		['mediainfo','--Output=PBCore2',inputPath],
		stdout=subprocess.PIPE
		)
	pbcore = call.communicate()[0]
	return pbcore 

def get_track_profiles(mediainfoDict):
	'''
	Get audio and video track profiles to compare for concatenation of files.
	Takes an OrderedDict as retrned by get_mediainfo_report.

	Discard attributes that are not necessary but keep relevant attributes
	that we want to compare between files. Prob can discard even more?
	Hard coded now to look for track[1] (video) and track[2] (audio),
	so presumably if there are additional tracks things will get screwy. 
	'''
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
		videoTrackProfile = mediainfoDict['MediaInfo']['media']['track'][1]
		for attr in videoAttribsToDiscard:
			videoTrackProfile.pop(attr,None)
	except:
		problems += 1
		print("mediainfo problem: "
			"either there is no video track or you got some issues")
	try:	
		audioTrackProfile = mediainfoDict['MediaInfo']['media']['track'][2]
		for attr in audioAttribsToDiscard:
			audioTrackProfile.pop(attr,None)
	except:
		problems += 1
		print("mediainfo problem: "
			"either there is no audio track or you got some issues")
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

def hash_file(inputPath,algorithm='md5',blocksize=65536):
	# STOLEN DIRECTLY FROM UCSB BRENDAN COATES: https://github.com/brnco/ucsb-src-microservices/blob/master/hashmove.py
	hasher = hashlib.new(algorithm)
	with open(inputPath,'rb') as infile:
		buff = infile.read(blocksize) # read the file into a buffer cause it's more efficient for big files
		while len(buff) > 0: # little loop to keep reading
			hasher.update(buff) # here's where the hash is actually generated
			buff = infile.read(blocksize) # keep reading
	return hasher.hexdigest()

def make_hashdeep_manifest(inputPath):
	'''
	given a directory, make a hashdeep manifest.
	chdir into target dir, make a manifest with relative paths, and get out.
	Now this relies on a bagit-style tree to contain both the manifest and 
	the package.
	proposal: also store the manfest as a blob
	(or as text?) in a db entry... yeah.
	'''
	_object = pymmFunctions.get_base(inputPath)
	# there should be a child dir with the same name as inputPath
	package = os.path.join(inputPath,_object)
	if not os.path.isdir(package):
		print("the expected directory structure is not present.") # @logme
		sys.exit(1)
	else:
		manifestPath = os.path.join(
			inputPath,
			'hashdeep_manifest_{}_{}.txt'.format(
				_object,
				pymmFunctions.timestamp('8601-filename')
				)
			)
		# print(manifestPath)
		# run hashdeep on the package
		command = ['hashdeep', '-rvvl', '-W', manifestPath, '.']
		# print(command)
		here = os.getcwd()
		os.chdir(package)
		manifest = subprocess.call(command,stdout=subprocess.PIPE)
		os.chdir(here)
		return manifestPath

def hashdeep_audit(inputPath,manifestPath):
	'''
	Given a target directory and an existing manifest, run a hashdeep audit.
	-> chdir into the target, audit the relative paths, and get out.
	Updated version creates a bagit-style tree that contains the package,
	along with the existing manifest.
	same idea as above: read manifest from blob in db and write the audit file
	as a new blob.
	'''
	_object = os.path.basename(inputPath)
	package = os.path.join(inputPath,_object)

	# turn off multithreading for auditing on LTO!
	command = ['hashdeep','-rvval','-j0','-k',manifestPath,'.']

	here = os.getcwd()
	os.chdir(package)
	try:
		hashaudit = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		print(hashaudit)
		out = hashaudit.stdout.splitlines()
		for line in out:
			if line.decode().startswith("hashdeep: Audit"):
				outcome = line.decode()
		if outcome == 'hashdeep: Audit failed':
			result = out
		elif outcome == 'hashdeep: Audit passed':
			result = True
		else:
			print("INCONCLUSIVE AUDIT. SIP NOT VERIFIED.")
			result = out

	except:
		print(
			"there was a problem with the hashdeep audit. "
			"package NOT verified."
			)
		result = out
	os.chdir(here)
	return result

def make_frame_md5(inputPath,metadataDir):
	print('making frame md5')
	if not pymmFunctions.is_av(inputPath):
		# FUN FACT: YOU CAN RUN FFMPEG FRAMEMD5 ON A TEXT FILE!!
		print("{} IS NOT AN AV FILE SO "
			"WHY ARE YOU TRYING TO MAKE "
			"A FRAME MD5 REPORT?".format(inputPath))
		return False
	else:
		md5File = pymmFunctions.get_base(inputPath)+"_frame-md5.txt"
		frameMd5Filepath = os.path.join(metadataDir,md5File)
		frameMd5Command = [
			'ffmpeg',
			'-i',inputPath,
			'-f','framemd5',
			frameMd5Filepath
			]
		output = subprocess.Popen(
			frameMd5Command,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
			)
		try:
			out,err = output.communicate()
			if err:
				print(err.decode('utf-8'))
			return frameMd5Filepath
		except:
			return False

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--inputPath',
		help='path of input file'
		)
	parser.add_argument(
		'-m','--mediainfo',
		action='store_true',
		help='generate a mediainfo sidecar file'
		)
	parser.add_argument(
		'-f','--frame_md5',
		action='store_true',
		help='make frame md5 report'
		)
	parser.add_argument(
		'-p','--pbcore',
		action='store_true',
		help='make mediainfo pbcore report'
		)
	parser.add_argument(
		'-j','--getJSON',
		action='store_true',
		help='get JSON output as applicable'
		)
	parser.add_argument(
		'-d','--destination',
		help='set destination for output metadata files'
		)
	args = parser.parse_args()
	
	inputPath = args.inputPath
	destination = args.destination
	frame_md5 = args.frame_md5
	_pbcore = args.pbcore
	mediainfo_report = args.mediainfo
	getJSON = args.getJSON

	if not inputPath:
		print("\n\nHEY THERE, YOU NEED TO SET AN INPUT FILE "
			"TO RUN THIS SCRIPT ON.\rNOW EXITING")
		sys.exit()
	if not destination:
		print('''
			YOU DIDN'T TELL ME WHERE TO PUT THE OUTPUT OF THIS SCRIPT,
			SO WE'LL PUT ANY SIDECAR FILES IN THE 
			SAME DIRECTORY AS YOUR INPUT FILE.
			''')
		destination = os.path.dirname(os.path.abspath(inputPath))
	if mediainfo_report:
		get_mediainfo_report(inputPath,destination,getJSON)
	if frame_md5:
		frameMd5Filepath = make_frame_md5(inputPath,destination)
		print(frameMd5Filepath)
	if _pbcore:
		xml = get_mediainfo_pbcore(inputPath)
		with open(
			os.path.join(
				destination,
				os.path.basename(inputPath)+"_pbcore.xml"
				),
			'wb'
			) as xmlFile:
			xmlFile.write(xml)

if __name__ == '__main__':
	main()
