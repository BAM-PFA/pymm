#!/usr/bin/env python3
'''
these are functions to output metadata files
and structured data (xml/json) about a/v files
'''
import argparse
import ast
import configparser
import datetime
import hashlib
import json
import os
import subprocess
import sys
# nonstandard libraries:
# import xmltodict
# local modules:
import pymmFunctions

def get_mediainfo_report(inputPath,destination,_JSON=None,altFileName=None):
	# handle an exception for the way 
	# DPX folders are named in processingVars
	if altFileName:
		basename = altFileName
	else:
		basename = pymmFunctions.get_base(inputPath)
	# write mediainfo output to a logfile if the destination is a directory ..
	if os.path.isdir(destination):
		if _JSON:
			outputType = "JSON"
		else:
			outputType = "XML"
		outputFilepath = '{}_mediainfo.xml'.format(
			os.path.join(destination,basename)
			)
		mediainfoOutput = '--LogFile={}'.format(outputFilepath)
		out = subprocess.run(
			['mediainfo',
			inputPath,
			'--Output={}'.format(outputType),
			mediainfoOutput],
			stdout=subprocess.PIPE
			)
		mediainfoJSON = out.stdout.decode('utf-8')
		if _JSON:
			return mediainfoJSON    
		else:
			return outputFilepath
	# ... otherwise pass something like '' as a destination 
	# and just get the raw mediainfo output
	else:
		out = subprocess.run(
			['mediainfo','--Output=JSON',inputPath],
			stdout=subprocess.PIPE
			)
		mediainfoJSON = out.stdout.decode('utf-8')
		# print(mediainfoJSON)
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
	# print(pbcore)
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
	if isinstance(mediainfoDict,str):
		mediainfoDict = ast.literal_eval(mediainfoDict)
	videoAttribsToDiscard = [
		'@type', 'ID', 'Format_Info', 'Format_profile',
		'Format_settings__CABAC', 'Format_settings__ReFrames', 
		'Format_settings__GOP', 'Codec_ID', 'Codec_ID_Info', 'Duration', 
		'Scan_type', 'Bits__Pixel_Frame_', 'StreamSize', 'Language', 
		'Tagged_date', 'Encoded_date', 'BitRate_Mode', 'BitRate', 
		'FrameCount', 'BufferSize'
		]
	audioAttribsToDiscard = [
		'@type', 'ID', 'Codec_ID', 'Duration', 'Stream_size', 
		'Language', 'Encoded_date', 'Tagged_date'
		]
	# `tracks` should be a list of track dicts
	tracks = mediainfoDict['media']['track']
	# print(tracks)
	videoTrackProfile = None
	audioTrackProfile = None
	for track in tracks:
		# print(track)
		if track['@type'] == 'Video':
			videoTrackProfile = track
		elif track['@type'] == 'Audio':
			audioTrackProfile = track

	if videoTrackProfile:
		for attr in videoAttribsToDiscard:
			videoTrackProfile.pop(attr,None)
	else:
		problems += 1
		print("mediainfo problem: "
			"either there is no video track or you got some issues")
	if audioTrackProfile:
		for attr in audioAttribsToDiscard:
			audioTrackProfile.pop(attr,None)
	else:
		problems += 1
		print("mediainfo problem: "
			"either there is no audio track or you got some issues")

	if problems == 0:
		return json.dumps(videoTrackProfile),json.dumps(audioTrackProfile)
	else:
		print("there might be problems")
		if videoTrackProfile:
			return json.dumps(videoTrackProfile),"{}"
		elif audioTrackProfile:
			return "{}",json.dumps(audioTrackProfile)
		else:
			return "{}","{}"

def hash_file(inputPath,algorithm='md5',blocksize=65536):
	# STOLEN DIRECTLY FROM UCSB BRENDAN COATES: https://github.com/brnco/ucsb-src-microservices/blob/master/hashmove.py
	hasher = hashlib.new(algorithm)
	with open(inputPath,'rb') as infile:
		buff = infile.read(blocksize) # read the file into a buffer cause it's more efficient for big files
		while len(buff) > 0: # little loop to keep reading
			hasher.update(buff) # here's where the hash is actually generated
			buff = infile.read(blocksize) # keep reading
	return hasher.hexdigest()

def manifest_path(inputPath,_uuid,_type):
	manifestPath = os.path.join(
		inputPath,
		'{}_manifest_{}_{}.txt'.format(
			_type,
			_uuid,
			pymmFunctions.timestamp('8601-filename')
			)
		)
	return manifestPath

def make_hashdeep_manifest(inputPath,_type):
	'''
	given a directory, make a hashdeep manifest.
	chdir into target dir, make a manifest with relative paths, and get out.
	For the SIP manifest, this currently relies on a bagit-style tree 
		to contain both the manifest and the package.
	proposal: also store the manifest as a blob
	(or as text?) in a db entry... yeah.
	'''
	_uuid = pymmFunctions.get_base(inputPath)
	if _type == 'hashdeep':
		# there should be a child dir with the same name as inputPath
		target = os.path.join(inputPath,_uuid)
		if not os.path.isdir(target):
			print("the expected directory structure is not present.") # @logme
			return False
	elif _type == 'objects':
		# were in the 'real' SIP dir so look for a subdir called 'objects'
		target = os.path.join(inputPath,_uuid,'objects')
		# we want to write the manifest to the metadata dir
		inputPath = os.path.join(inputPath,_uuid,'metadata')
		if not os.path.isdir(target) or not os.path.isdir(inputPath):
			print("the expected directory structure is not present.") # @logme
			return False
	manifestPath = manifest_path(inputPath,_uuid,_type)
	# run hashdeep on the package
	command = ['hashdeep', '-rvvl', '-c','md5','-W', manifestPath, '.']
	# print(command)
	here = os.getcwd()
	os.chdir(target)
	manifest = subprocess.call(command,stdout=subprocess.PIPE)
	os.chdir(here)
	return manifestPath

def hashdeep_audit(inputPath,manifestPath,_type=None):
	'''
	Given a target directory and an existing manifest, run a hashdeep audit.
	-> chdir into the target, audit the relative paths, and get out.
	Updated version creates a bagit-style tree that contains the package,
	along with the existing manifest.
	same idea as above: read manifest from blob in db and write the audit file
	as a new blob.
	'''
	_uuid = os.path.basename(inputPath)
	package = os.path.join(inputPath,_uuid)
	if _type == 'SIP':
		target = package
	elif _type == 'objects':
		target = os.path.join(package,'objects')

	# turn off multithreading for auditing on LTO!
	command = ['hashdeep','-rvval','-j0','-k',manifestPath,'.']
	# print(command)
	# print(target)
	here = os.getcwd()
	os.chdir(target)
	try:
		hashaudit = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		# print(hashaudit)
		out = hashaudit.stdout.splitlines()
		result = ""
		error = False
		for line in out:
			if line.decode().startswith("hashdeep: Audit"):
				outcome = line.decode()
				print(outcome)
		if outcome == 'hashdeep: Audit failed':
			status = False
		elif outcome == 'hashdeep: Audit passed':
			status = True
		else:
			status = False
			error = True
			print("INCONCLUSIVE AUDIT. SIP NOT VERIFIED.")
			result = [out,hashaudit.stderr.decode()]
		# gather the results for logging
		if not error:
			for line in out:
				result += line.decode()+"\n"
	except:
		print(
			"there was a problem with the hashdeep audit. "
			"package NOT verified."
			)
		status = False
		result = "hashdeep error"
	os.chdir(here)
	return result,status

def make_frame_md5(inputPath,metadataDir):
	print('making frame md5')
	print(inputPath)
	md5File = pymmFunctions.get_base(inputPath)+"_frame-md5.txt"
	frameMd5Filepath = os.path.join(metadataDir,md5File)
	av = pymmFunctions.is_av(inputPath)
	returnValue = False
	if not av:
		# FUN FACT: YOU CAN RUN FFMPEG FRAMEMD5 ON A TEXT FILE!!
		print("{} IS NOT AN AV FILE SO "
			"WHY ARE YOU TRYING TO MAKE "
			"A FRAME MD5 REPORT?".format(inputPath))
	elif av == 'VIDEO':
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
				# this output is captured in stderr for some reason
				print("FRAME MD5 CHA CHA CHA")
				# print(err.decode('utf-8'))
			returnValue = frameMd5Filepath
		except:
			print(out.decode())
	elif av == 'AUDIO':
		sampleRate = pymmFunctions.get_audio_sample_rate(inputPath)
		frameMd5Command = [
			'ffmpeg',
			'-i',inputPath,
			'-af','asetnsamples=n={}'.format(sampleRate),
			'-f','framemd5',
			'-vn',
			frameMd5Filepath
			]
		output = subprocess.run(frameMd5Command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		# print(output.returncode)
		try:
			if output.returncode == 0: 
				# print(output)
				print("FRAME MD5 CHA CHA CHA")
				returnValue = frameMd5Filepath
		except:
			print(output.stderr.decode())

	elif av == 'DPX':
		pass
		'''
		OK: FOOD FOR THOUGHT: 
			IT TAKES EFFING FOREVER TO CALCULATE FRAMEMD5 VALUES FOR A DPX
			SEQUENCE. SLIGHTLY LONGER THAN THE HASHDEEP MANIFEST THAT WILL 
			BE CREATED LATER. SO... SKIP FRAMEMD5 FOR DPX? SINCE WE ARE ALREADY
			CALCULATING A HASH MANIFEST LATER ON?
			MAYBE LATER GET A FUNCTION TO PARSE A HASH MANIFEST FOR THE FOLDER AND 
			TURN IT INTO A 

		ACTUALLY ON THE SOUPED UP LINUX SERVER THIS IS REALLY FAST. 
		SO MAYBE RUN A BENCH MARK AND IF THE SYSTEM CAN HANDLE IT RUN THIS FUNCTION
		'''
		# filePattern,startNumber,file0 = pymmFunctions.parse_sequence_folder(inputPath)
		# frameMd5Command = [
		# 	'ffmpeg',
		# 	'-start_number',startNumber,
		# 	'-i',filePattern,
		# 	'-f','framemd5',
		# 	frameMd5Filepath
		# 	]
		# print(' '.join(frameMd5Command))
		# output = subprocess.Popen(
		# 	frameMd5Command,
		# 	stdout=subprocess.PIPE,
		# 	stderr=subprocess.PIPE
		# 	)
		# try:
		# 	out,err = output.communicate()
		# 	if err:
		# 		# this output is captured in stderr for some reason
		# 		print("FRAME MD5 CHA CHA CHA")
		# 		# print(err.decode('utf-8'))
		# 	returnValue = frameMd5Filepath
		# except:
		# 	print(out.decode())

	return returnValue

def get_duration(inputPath):
	print('getting input file duration via general track 0')
	command = [
	'mediainfo',
	'--output=JSON',
	inputPath
	]
	mediainfoJSON = subprocess.run(
		command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)
	out = mediainfoJSON.stdout
	fileJson = json.loads(out.decode())

	try:
		duration = fileJson['media']['track'][0]['Duration']
	except:
		print("Error getting duration via mediainfo.")

	return duration

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--inputPath',
		help='path of input file',
		required=True
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
	parser.add_argument(
		'-v','--getValue',
		help='declare a valid MediaInfo raw tag to get it.'\
			'REQUIRES you to declare a stream type!'
		)
	parser.add_argument(
		'-t','--valueType',
		help='declare a valid stream type from which to grab a value.',
		choices=['General','Audio','Video']
		)
	args = parser.parse_args()
	
	inputPath = args.inputPath
	destination = args.destination
	frame_md5 = args.frame_md5
	_pbcore = args.pbcore
	mediainfo_report = args.mediainfo
	getJSON = args.getJSON
	value = args.getValue
	valueType = args.valueType

	if not inputPath:
		print("\n\nHEY THERE, YOU NEED TO SET AN INPUT FILE "
			"TO RUN THIS SCRIPT ON.\rNOW EXITING")
		sys.exit()
	if not destination:
		# print('''
		# 	YOU DIDN'T TELL ME WHERE TO PUT THE OUTPUT OF THIS SCRIPT,
		# 	SO WE'LL PUT ANY SIDECAR FILES IN THE 
		# 	SAME DIRECTORY AS YOUR INPUT FILE.
		# 	''')
		destination = os.path.dirname(os.path.abspath(inputPath))
	if mediainfo_report:
		get_mediainfo_report(inputPath,destination,getJSON)
	if frame_md5:
		frameMd5Filepath = make_frame_md5(inputPath,destination)
		# print(frameMd5Filepath)
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
	if value:
		if not valueType:
			print("YOU NEED TO DECLARE A STREAM TYPE:"\
					"Audio, General, or Video"
				)
			sys.exit()
		else:
			theValue = pymmFunctions.get_mediainfo_value(
				inputPath,
				valueType,
				value
			)
			print(theValue)
			return theValue		

if __name__ == '__main__':
	main()
