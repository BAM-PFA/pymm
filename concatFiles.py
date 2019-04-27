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
try:
	import makeMetadata
	import pymmFunctions
except:
	from . import makeMetadata
	from . import pymmFunctions
	
def parse_args(**kwargs):
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--inputPath',
		required=True,
		help=(
			'Full path to either a dir with stuff to concatenate '
			'or a list of paths to files to concatenate.'
			)
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

def count_streams(sourceList):
	status = True
	sources = {}
	for _object in sourceList:
		sources[_object] = {'audio tracks':'','video tracks':''}
		sources[_object]['audio tracks'] = pymmFunctions.get_stream_count(
			_object,
			'audio'
			)
		sources[_object]['video tracks'] = pymmFunctions.get_stream_count(
			_object,
			'video'
			)
	for format in ('audio','video'):
		if len(set([x[format+' tracks'] for x in sources.values()])) > 1:
			# if there's more than one value for stream type,
			# that's no good
			status = False
	# print(sources)

	return status,sources

def get_profiles(input_list):
	# BUILD A DICT OF PROFILES TO COMPARE FOR CONCATENATION
	print("*"*100)
	profiles = {}
	for sourceFile in input_list:
		profiles[sourceFile] = {'video':'','audio':''}
		videoProfile,audioProfile = makeMetadata.get_track_profiles(
			makeMetadata.get_mediainfo_report(
				sourceFile,'',_JSON=True
				)
			)
		profiles[sourceFile]['video'] = json.loads(videoProfile)
		profiles[sourceFile]['audio'] = json.loads(audioProfile)

	print(profiles)
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
	# `-threads` is not really necessary, 
	# added to be conservative with hardware limitations
	'-threads','12',
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

def concat(sourceList,canonicalName,wrapper,simple=None):
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
	# print(ffmpegConcatFile)
	concattedFile = do_ffmpeg_concat(
		ffmpegConcatFile,
		sourceDir,
		canonicalName,
		wrapper
		)

	os.remove(ffmpegConcatFile)

	return concattedFile

def safe_to_concat(sourceList,complex=None):
	'''
	OK this is cheezy but should get it done:
	- pick a random input file to call the 'canonical' spec source.
	- since they all need to match each other it doesn't matter which it is.
	- then we'll try to match each profile to the canonical spec,
	  and if any fails we can report which input file failed.

	If complex=True, test for identical pixel dimensions and stream counts,
	  or report the different stats and refuse to concatenate.
	'''
	profilesDict = get_profiles(sourceList)
	canonicalAudioSpec = list(profilesDict.items())[0][1]['audio']
	canonicalVideoSpec = list(profilesDict.items())[0][1]['video']
	# print(canonicalAudioSpec)

	numberOfFiles = len(sourceList)
	checkedFiles = 0
	outlierFiles = []
	problems = ""

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
				problems += "\n{} failed the audio spec check.".format(
					os.path.basename(inputFile)
					)
				print(problems)
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
				problems += "\n{} failed the video spec check.".format(
					os.path.basename(inputFile)
					)
				print(problems)
				outlierFiles.append((
					inputFile,(profilesDict[inputFile]['video'])
					))

	# print(outlierFiles)
	# print(profilesDict)
	if safeToConcat == True:
		print('go ahead')
	else:
		diffs = get_spec_diffs(
			profilesDict,
			canonicalAudioSpec,
			canonicalVideoSpec
			)

		problems += '\nNot safe to concat. Check file specs.'
		if not diffs == {}:
			for thing,diff in diffs.items():
				base = os.path.basename(thing)
				problems += (
					'\n*** Variances found in {}: ***'
					'\nAudio: {}'
					'\nVideo: {}'.format(base,diff['audio'],diff['video'])
					)
		# print(problems)
		safeToConcat = problems

	return safeToConcat

def get_spec_diffs(profilesDict,canonicalAudioSpec,canonicalVideoSpec):
	'''
	Return the variances from the 'canonical' specs for each input file.
	'''
	diffs = {}
	for _object,profile in profilesDict.items():
		# get any differences from the canonical video spec:
		vidDet = profile['video']
		# print(vidDet)
		vDiff = { 
			k : vidDet[k] \
			for k,_ \
			in set(vidDet.items()) - set(canonicalVideoSpec.items())
		}
		# now get differences from the canonical audio spec:
		audDet = profilesDict[_object]['audio']
		aDiff = { 
			k : audDet[k] \
			for k,_ \
			in set(audDet.items()) - set(canonicalAudioSpec.items())
		}
		# print("aDiff",aDiff)
		# print("vDiff",vDiff)
		if not all([x == {} for x in (aDiff,vDiff)]):
			diffs[_object] = {'audio':'','video':''}
		if not aDiff == {}:
			diffs[_object]["audio"] = aDiff
		if not vDiff == {}:
			diffs[_object]["video"] = vDiff

	return diffs

def main():
	args = parse_args()
	_input = args.inputPath
	canonicalName = args.canonical_name
	wrapper = args.wrapper
	success = False
	problems = ""

	if os.path.isdir(_input):
		# get rid of any hidden files
		pymmFunctions.remove_hidden_system_files(_input)
		# get the abs path of each input file
		sourceList = pymmFunctions.list_files(_input)
	elif isinstance(_input,list):
		sourceList = _input
	else:
		problems += "\ninput is not a dir or list of files. exiting!"
		print(problems)
		# sys.exit()
	if not canonicalName:
		canonicalName = os.path.basename(sourceList[0])
		print(
			"You didn't specify a canonical_name "
			"so we will treat the first item in sourceList as "
			"the canonical name for your object."
			)
	#######################
	#	START TESTING FILES
	stream_compatability,streams = count_streams(sourceList)
	if not stream_compatability:
		problems += (
			"\nCan't concatenate. There are stream count differences "
			"in your input files. See this: \n{}".format(streams)
			)
		success = False
		print(problems)
		return problems,success
	# safe_to_concat returns either True or a list of problems
	simpleConcat = safe_to_concat(sourceList)
	complexConcat = None # placeholder

	if not simpleConcat == True:
		complexConcat = False
		# placeholder:
		# complexConcat = safe_to_concat(sourceList,complex=True)
	if True in (simpleConcat,complexConcat):
		safeToConcat = True
	concattedFile = False

	if safeToConcat == True:
		try: 
			concattedFile = concat(
				sourceList,
				canonicalName,
				wrapper,
				simple=True
				)
		except:
			problems += "\nsome problem with the concat process."
			print(problems)
	else:

		problems += simpleConcat

	# rename the file so it sorts to the top of the output directory
	# maybe this is a stupid idea? but it will be handy
	if not concattedFile == False:
		concatBase = os.path.basename(concattedFile)
		concatDir = os.path.dirname(concattedFile)
		newBase = "00_concatenated_{}".format(concatBase)
		newPath = os.path.join(concatDir,newBase)
		# actually rename the file
		os.rename(concattedFile,newPath)
		# reset the var to the new path name
		concattedFile = newPath
		success = True

	else: 
		success = False
		concattedFile = problems

	return concattedFile,success

if __name__ == '__main__':
	main()
