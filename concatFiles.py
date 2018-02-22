#!/usr/bin/env python3
'''
pymm is a python port of mediamicroservices
(https://github.com/mediamicroservices/mm)

`concatFiles` is basically ripping off `concat.py` from the Irish Film Archive:
 https://github.com/kieranjol/IFIscripts/blob/master/concat.py

`concatFiles` will take a directory of files (only one level deep)
and concatenate them by copying the bitstreams into a single `mkv` wrapper.

Currently this will only happen if some conditions are met:
1) If the user chooses
2) the files represent parts of a whole (reels of a film, tapes)
   and are named accordingly.
3) the files match each others' technical profiles
   (i.e. the pixel dimensions, frame rate, etc. need to match)

'''
import subprocess
import os
import sys
import argparse
import json
# local modules:
import pymmFunctions
import makeMetadata



def parse_args(**kwargs):
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--input',
		help='stuff to concatenate'
		)
	parser.add_argument(
		'-d','--ingestID',
		help='ingest UUID'
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
											))
		profiles[sourceFile]['video'] = json.loads(videoProfile)
		profiles[sourceFile]['audio'] = json.loads(audioProfile)

	# print(profiles)
	return profiles

def concat(source_list):
	# do stuff:
	# -set ffmpeg report 
	# -get length of files for chapter markers
	# -do the concat
	# -make mkv chapter markers
	return True

def main(**kwargs):
	args = parse_args(**kwargs)
	_input = args.input
	ingestID = args.ingestID

	if os.path.isdir(_input):
		# get the abs path of each input file
		source_list = pymmFunctions.list_files(_input)
	elif type(_input) == 'list':
		source_list = _input
	else:
		print("don't know what you are trying to input. not a dir or list of files.")
		sys.exit()

	# OK this is cheezy but should get it done.
	# pick a random input file to call the 'canonical' spec source.
	# since they all need to match each other it doesn't matter which it is.
	# then we'll try to match each profile to the canonical spec,
	# and if any fails we can report which input file failed.
	profilesDict = get_profiles(source_list)
	canonicalAudioSpec = list(profilesDict.items())[0][1]['audio']
	canonicalVideoSpec = list(profilesDict.items())[0][1]['video']
	# print(canonicalAudioSpec)
	# print(canonicalVideoSpec)

	numberOfFiles = len(source_list)
	checkedFiles = 0
	outlierFiles = []

	while checkedFiles < numberOfFiles:
		for inputFile in source_list:
			safeToConcat = False
			checkedFiles += 1
			if profilesDict[inputFile]['audio'] == canonicalAudioSpec:
				print("{} passed the spec check.".format(os.path.basename(inputFile)))
			else:
				print("{} failed the audio spec check. Exiting".format(os.path.basename(inputFile)))
				outlierFiles.append((inputFile,(profilesDict[inputFile]['audio'])))
			if profilesDict[inputFile]['video'] == canonicalVideoSpec:
				print("{} passed the spec check.".format(os.path.basename(inputFile)))
				safeToConcat = True
			else:
				print("{} failed the video spec check. Exiting".format(os.path.basename(inputFile)))
				outlierFiles.append((inputFile,(profilesDict[inputFile]['video'])))

	print(outlierFiles)
	
	if safeToConcat == True:
		print('go ahead')

	concattedFile = concat(source_list)
	return True






	# audioSpecList = []
	# videoSpecList = []
	# for item in profilesDict.keys():
	# 	profileAudioList = list(profilesDict[item]['audio'].items())
	# 	audioSpecList.append(profileAudioList)
	# 	profileVideoList = list(profilesDict[item]['video'].items())
	# 	videoSpecList.append(profileVideoList)
	# 	# print(profileAudioList)
	
	# print(audioSpecList)
	# for (key, value) in set()
	# print(profilesDict.keys().keys())

	# for constituent in profilesDict.keys():


if __name__ == '__main__':
	main(sys.argv[1:])