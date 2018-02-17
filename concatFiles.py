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

	print(profiles)
	return profiles

def main(**kwargs):
	args = parse_args(**kwargs)
	_input = args.input
	ingestID = args.ingestID

	print(type(_input))
	if os.path.isdir(_input):
		source_list = pymmFunctions.list_files(_input)
	elif type(_input) == 'list':
		source_list = _input
	else:
		print("don't know what you are trying to input. not a dir or list of files.")
		sys.exit()

	profilesDict = get_profiles(source_list)

	print(profilesDict.keys())

if __name__ == '__main__':
	main(sys.argv[1:])