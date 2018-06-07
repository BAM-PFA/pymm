#!/usr/bin/env python3
'''
`concatFiles` is basically ripping off `concat.py` from the Irish Film Archive:
 https://github.com/kieranjol/IFIscripts/blob/master/concat.py

`concatFiles` will take a directory of files (only one level deep)
and concatenate them by copying the bitstreams into a single `mkv` wrapper.

This is currently only intended to be used with our access copies,
for reference purposes only.
'''
# standard library modules
import argparse
import json
import os
import subprocess
import sys
import tempfile
# local modules:
import makeMetadata
import pymmFunctions

def parse_args(**kwargs):
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--inputPath',
		required=True,
		help='stuff to concatenate'
		)
	parser.add_argument(
		'-d','--ingestID',
		help='ingest UUID'
		)
	parser.add_argument(
		'-c','--canonical_name',
		help='object canonical name'
		)
	parser.add_argument(
		'-w','--wrapper',
		help='wrapper for output file',
		default='mkv'
		)

	return parser.parse_args()

def get_profiles(input_list):
	# BUILD A DICT OF PROFILES TO COMPARE FOR CONCATENATION
	profiles = {}
	for sourceFile in input_list:
		profiles[sourceFile] = {'video':'','audio':''}
		videoProfile,audioProfile = makeMetadata.get_track_profiles(
			makeMetadata.get_mediainfo_report(
				sourceFile,'','GET JSON'
				)
			)
		profiles[sourceFile]['video'] = json.loads(videoProfile)
		profiles[sourceFile]['audio'] = json.loads(audioProfile)

	# print(profiles)
	return profiles

def make_ffmpeg_concat_file(sourceList):
	tempDir = tempfile.gettempdir()
	concatFile = os.path.join(tempDir,'concat.txt')
	with open(concatFile,'w') as f:
		for path in sourceList:
			# write a line in the concat file for each path in sourceList
			# that should look like
			# file '/path/to/file1'
			# file '/path/to/file2'
			f.write("file '{}'\n".format(path))

	# with open(concatFile,'r') as d:
	# 	for line in d.readlines():
	# 		print(line)
	return concatFile

def do_ffmpeg_concat(ffmpegConcatFile,sourceDir,canonicalName,wrapper):
	# run the actual ffmpeg command to concat files
	print("HEYY")
	outputPath = os.path.join(
		sourceDir,'{}.{}'.format(
			canonicalName,
			wrapper
			)
		)
	# print(outputPath)
	command = [
	'ffmpeg',
	'-f','concat',
	'-safe','0',
	'-i',ffmpegConcatFile,
	outputPath
	]

	out = subprocess.run(
		command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)

	# for line in out.stderr.splitlines():
		# print(line.decode())

	return outputPath

def concat(sourceList,canonicalName,wrapper):
	# do stuff:
	# -set ffmpeg report 
	# -get length of files for chapter markers
	# -do the concat
	# -make mkv chapter markers
	fileInfo = {}
	for _file in sourceList:
		fileInfo[_file] = {}
		duration = makeMetadata.get_duration(_file)
		milliseconds = int(duration.replace(".",""))
		# pymmFunctions.convert_millis(duration)
		fileInfo[_file]['duration in milliseconds'] = milliseconds

	# generate a temp file for ffmpeg to read and concatenate files by path
	ffmpegConcatFile = make_ffmpeg_concat_file(sourceList)
	sourceDir = os.path.dirname(sourceList[0])
	print(ffmpegConcatFile)
	concattedFile = do_ffmpeg_concat(
		ffmpegConcatFile,
		sourceDir,
		canonicalName,
		wrapper
		)

	os.remove(ffmpegConcatFile)

	return concattedFile

def safe_to_concat(sourceList):
	'''
	OK this is cheezy but should get it done:
	- pick a random input file to call the 'canonical' spec source.
	- since they all need to match each other it doesn't matter which it is.
	- then we'll try to match each profile to the canonical spec,
	  and if any fails we can report which input file failed.
	'''
	profilesDict = get_profiles(sourceList)
	canonicalAudioSpec = list(profilesDict.items())[0][1]['audio']
	canonicalVideoSpec = list(profilesDict.items())[0][1]['video']
	# print(canonicalAudioSpec)
	# print(canonicalVideoSpec)

	numberOfFiles = len(sourceList)
	checkedFiles = 0
	outlierFiles = []

	while checkedFiles < numberOfFiles:
		for inputFile in sourceList:
			safeToConcat = False
			checkedFiles += 1
			
			if profilesDict[inputFile]['audio'] == canonicalAudioSpec:
				print(
					"{} passed the audio spec check.".format(
						os.path.basename(inputFile)
						)
					)
			else:
				print(
					"{} failed the audio spec check. Exiting".format(
						os.path.basename(inputFile)
						)
					)
				outlierFiles.append((
					inputFile,(profilesDict[inputFile]['audio'])
					))
			if profilesDict[inputFile]['video'] == canonicalVideoSpec:
				print(
					"{} passed the video spec check.".format(
						os.path.basename(inputFile)
						)
					)
				safeToConcat = True
			else:
				print(
					"{} failed the video spec check. Exiting".format(
						os.path.basename(inputFile)
						)
					)
				outlierFiles.append((
					inputFile,(profilesDict[inputFile]['video'])
					))

	print(outlierFiles)
	
	if safeToConcat == True:
		print('go ahead')
	else:
		print('not safe to concat. check file specs.')

	return safeToConcat

def main():
	args = parse_args()
	_input = args.inputPath
	ingestID = args.ingestID
	canonicalName = args.canonical_name
	wrapper = args.wrapper

	if os.path.isdir(_input):
		# get rid of any hidden files
		pymmFunctions.remove_hidden_system_files(_input)
		# get the abs path of each input file
		sourceList = pymmFunctions.list_files(_input)
	elif isinstance(_input,list):
		sourceList = _input
	else:
		print("input is not a dir or list of files. exiting!")
		sys.exit()

	safeToConcat = safe_to_concat(sourceList)
	concattedFile = False

	if safeToConcat == True:
		try: 
			concattedFile = concat(sourceList,canonicalName,wrapper)
		except:
			print("some problem with the concat process.")
	else:
		pass

	# rename the file so it sorts to the top of the output directory
	# maybe this is a stupid idea? but it will be handy
	if not concattedFile == False:
		concatBase = os.path.basename(concattedFile)
		concatDir = os.path.dirname(concattedFile)
		newBase = "0_{}".format(concatBase)
		newPath = os.path.join(concatDir,newBase)
		concattedFile = newPath
		
	return concattedFile


if __name__ == '__main__':
	main()#sys.argv[1:])