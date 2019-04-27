#!/usr/bin/env python3
'''
This script takes an input AV object and outputs an access copy. 
It is relatively tailored to use within BAMPFA's EDITH app, 
but mostly in terms of the output folder structure (it expects you to
want a folder called 'resourcespace'). The transcoding options are 
set in dicts in `pymmconfig`. You can also leave the dicts empty and
use the defaults below for testing.
I haven't (4/2019) put much thought into ProRes output, but that 
may or may not become a necessity for us later. For now, we are outputting 
H264 in mp4 for video and mp3 for audio input.
'''
import argparse
import json
import os
import re
import subprocess
import sys
# local modules:
try:
	import moveNcopy
	import pymmFunctions
	import directoryScanner
except:
	from . import moveNcopy
	from . import pymmFunctions
	from . import directoryScanner

config = pymmFunctions.read_config()

defaultVideoAccessOptions = {
	"-movflags":"faststart",
	"-threads":"12", # just being conservative with hardware
	"-pix_fmt":"yuv420p",
	"-c:v":"libx264",
	"-f":"mp4",
	"-crf":"23",
	"-c:a":"aac",
	"-b:a":"320k",
	"-ar":"48000"
	}

defaultAudioAccessOptions = {
	"-id3v2_version":"3",
	"-dither_method":"rectangular",
	"-qscale:a":"1"
	}

# SET FFMPEG INPUT OPTIONS
def set_input_options(derivType,inputPath,ffmpegLogDir=None,isSequence=None):
	'''
	Set the input options and filepath for ffmpeg
	'''
	inputOptions = {}

	if isSequence:
		# get variables needed to process a derivative from a dpx sequence
		audioPath,\
		filePattern,\
		startNumber,\
		framerate = pymmFunctions.parse_sequence_parent(inputPath)
		# print(audioPath)
		inputOptions['-start_number'] = startNumber
		inputOptions['-i'] = filePattern

		if framerate:
			inputOptions['-r'] = framerate
		if audioPath:
			inputOptions['audioPath'] = audioPath # this gets reset to '-i'

	else:
		audioPath = None
		inputOptions['-i'] = inputPath

	temp = options_to_list(inputOptions)
	if ffmpegLogDir:
		temp.append('-report')
	# change the 'audioPath' key back to second '-i'
	inputOptions = ['-i' if x == 'audioPath' else x for x in temp]

	return inputOptions,audioPath

def set_middle_options(
	derivType,
	inputType,
	inputPath,
	mixdown,
	combine_audio_streams,
	audioPath
	):
	'''
	Set the options for encoding and any filters
	'''
	middleOptions = []
	if derivType == 'resourcespace':
		# make an mp4 file for upload to ResourceSpace
		# also used as our Proxy for access screenings
		# list in config setting requires double quotes
		if inputType in ('VIDEO','sequence'):
			middleOptions = json.loads(
				config['ffmpeg']['resourcespace_video_opts']
				)
		elif inputType == 'AUDIO':
			middleOptions = json.loads(
				config['ffmpeg']['resourcespace_audio_opts']
				)

		# test/set a default proxy command for FFMPEG call
		if middleOptions == {}:
			if inputType in ('VIDEO','sequence'):
				middleOptions = defaultVideoAccessOptions
			elif inputType == 'AUDIO':
				middleOptions = defaultAudioAccessOptions
			print(
				"WARNING: YOU HAVEN'T SET FFMPEG "
				"OPTIONS FOR ACCESS FILE TRANSCODING "
				"IN config.ini.\nWE'RE GOING TO USE SOME DEFAULTS!!"
				)

		dualMono = pymmFunctions.check_dual_mono(inputPath)

		if combine_audio_streams or mixdown:
			if audioPath:
				path = audioPath
			else:
				path = inputPath
			audioFilter = add_audio_merge_filter(middleOptions,path)
			# print(audioFilter)
			if audioFilter:
				middleOptions['-filter_complex'] = audioFilter
				middleOptions['-map'] = '[out] -map 0:v'

				if mixdown:
					middleOptions['-ac'] = '1'
				else:
					middleOptions['-ac'] = '2'
			else:
				middleOptions['-map'] = '0:v -map 0:a?'
		elif dualMono:
			# if the input has two mono tracks, check if one is "empty"
			# and if so, discard it. Checks for RMS peak dB below -50
			empty = pymmFunctions.check_empty_mono_track(inputPath)
			# print(empty)
			# print(type(empty))
			if empty != None:
				middleOptions['-filter_complex'] = \
					"[0:a:{}]aformat=channel_layouts=stereo".format(str(empty))
			else:
				# what if both mono tracks are empty??
				middleOptions['-map'] = '0:v -map 0:a'

		else:
			middleOptions['-map'] = '0:v -map 0:a?'
			if inputType == 'AUDIO':
				# remove video stream map for audio input
				middleOptions['-map'] = middleOptions['-map'].replace(
					'0:v -map ',''
					)

	elif derivType == 'proresHQ':
		# make a HQ prores .mov file as a mezzanine 
		# for color correction, cropping, etc.
		middleOptions = json.loads(config['ffmpeg']['proresHQ_opts'])

	elif True == True:
		print('etc')
		# and so on

	middleOptions = options_to_list(middleOptions)

	return middleOptions

def set_output_options(derivType,inputType,inputPath,outputDir):
	'''
	Set the output filepath and its extension
	'''
	outputOptions = {}
	# the ffmpeg docs say the strict flag is no longer required 
	# for aac encoding in mp4 but I ran into issues without it, 
	# so I'll keep it for now (7/2018)
	base = pymmFunctions.get_base(inputPath)
	baseMinusExtension = pymmFunctions.get_base(
		inputPath,
		'baseMinusExtension'
		)
	# make a delivery directory for a package that is based on the deriv type
	derivDeliv = os.path.join(outputDir,derivType)
	if not os.path.isdir(derivDeliv):
		print("Making a directory at "+derivDeliv)
		try:
			os.mkdir(os.path.join(outputDir,derivType))
		except:
			print("couldn't make a dir at "+derivDeliv)
	if derivType == 'resourcespace':
		if inputType in ('VIDEO','sequence'):
			ext = 'mp4'
			outputOptions['-strict'] = '-2'
		elif inputType == 'AUDIO':
			ext = 'mp3'
		else:
			ext = 'mp4'
			print("FUCK EVERYTHING: ERROR GETTING THE FILE TYPE.")
		outputFilePath = os.path.join(
			derivDeliv,
			baseMinusExtension+'_access.'+ext
			)
	elif derivType == 'proresHQ':
		ext = 'mov'
		outputFilePath = os.path.join(
			derivDeliv,
			baseMinusExtension+'_proresHQ.'+ext
			)
	else:
		print('~ ~ ~ ~ ~')
		# DO STUFF TO OTHER DERIV TYPES

	outputOptions = options_to_list(outputOptions)
	outputOptions.append(outputFilePath)

	return outputOptions

def additional_delivery(derivFilepath,derivType,rsMulti=None):
	destinations = 	{
		'resourcespace': config['paths']['resourcespace_deliver'],
		'proresHQ':config['paths']['prores_deliver']
		}
	deliveryDir = destinations[derivType]

	if deliveryDir == '':
		print(
			"there's no directory set "
			"for {} delivery... SET IT!!".format(derivType)
			)
		pass
	elif deliveryDir != '' and rsMulti != None:
		sys.argv = ['',
			'-i'+derivFilepath,
			'-d'+rsMulti
			]
	else:
		sys.argv = ['',
			'-i'+derivFilepath,
			'-d'+deliveryDir
			]

	try:
		moveNcopy.main()
	except:
		print(
			'there was an error in rsyncing the output '
			'deriv to the destination folder'
			)

def add_audio_merge_filter(middleOptions,inputPath):
	'''
	check for audio streams and add to a filter that will merge them all 
	'''
	audioStreamCount = pymmFunctions.get_stream_count(inputPath,"audio")
	print(str(audioStreamCount)+' audio streams in '+inputPath)

	if audioStreamCount in (None, 0, 1):
		audioFilter = None
	else:
		audioFilter = 'amerge[out]' # this is the end of the filter

		for stream in reversed(range(audioStreamCount)):
			streamIndex = "[0:a:{}]".format(str(stream))
			audioFilter = streamIndex+audioFilter # add each track in reverse order
		# YOU DONT NEED To WRAP THE FILTER (OR ANYTHING ELSE?) IN QUOTES
		# WHEN CALLING FROM SUBPROCESS
		# audioFilter = '"{}"'.format(audioFilter) # wrap the filter in quotes

	return audioFilter

def options_to_list(options):
	'''
	Take in one of the options dicts and turn it into a list for 
	use by `subprocess`
	'''
	temp = []
	[temp.extend([key,value]) for key, value in options.items()]
	temp2 = []
	# print(temp)
	for item in temp:
		if not item == '':
			temp2.extend(item.split(' '))
	# print(temp2)
	options = temp2

	return options

def set_args():
	parser = argparse.ArgumentParser(
		description='make derivatives of an input a/v file or an image sequence'
		)
	parser.add_argument(
		'-i','--inputPath',
		required=True,
		help='path of input material'
		)
	parser.add_argument(
		'-d','--derivType',
		choices=['resourcespace','proresHQ'],
		default='resourcespace',
		help='choose a derivative type to output'
		)
	parser.add_argument(
		'-o','--outputDir',
		help='set output directory for deriv delivery'
		)
	parser.add_argument(
		'-L','--logDir',
		help='set output directory for ffmpeg and rsync logs'
		)
	parser.add_argument(
		'-r','--rspaceMulti',
		help='set directory for multi-part resourcespace object'
		)
	parser.add_argument(
		'-s','--isSequence',
		action='store_true',
		help='flag if the input is an image sequence'
		)
	parser.add_argument(
		'-m','--mixdown',
		action='store_true',
		default=False,
		help=(
			"Do/don't mix down all audio tracks to mono "
			"for access copy. Default=False."
			)
		)
	parser.add_argument(
		'-k','--combine_audio_streams',
		action='store_true',
		help=(
			"Do/don't map all existing audio streams "
			"to access copy. Default is to keep all streams as-is. "
			"Use this flag to mix to single (stereo) track."
			"Set -m if you want mono instead."
			)
		)

	return parser.parse_args()

def main():
	# DO STUFF
	args = set_args()
	inputPath = args.inputPath
	# for ingestfile.py this is the packageDerivDir
	outputDir = args.outputDir
	derivType = args.derivType
	logDir = args.logDir
	rsMulti = args.rspaceMulti
	isSequence = args.isSequence
	mixdown = args.mixdown
	combine_audio_streams = args.combine_audio_streams

	if logDir:
		pymmFunctions.set_ffreport(logDir,'makeDerivs')

	if not isSequence:
		inputType = pymmFunctions.is_av(inputPath)
	else:
		inputType = 'sequence'
	ffmpegArgs = []
	inputOptions,audioPath = set_input_options(
		derivType,
		inputPath,
		logDir,
		isSequence
		)
	middleOptions = set_middle_options(
		derivType,
		inputType,
		inputPath,
		mixdown,
		combine_audio_streams,
		audioPath
		)
	outputOptions = set_output_options(
		derivType,
		inputType,
		inputPath,
		outputDir
		)
	
	ffmpegArgs = inputOptions+middleOptions+outputOptions
	ffmpegArgs.insert(0,'ffmpeg')
	# print(ffmpegArgs)
	print(' '.join(ffmpegArgs))
	output = subprocess.run(
		ffmpegArgs,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)
	# out,err = output.communicate()
	# print(out.decode('utf-8'))
	
	if output.stderr:
		print(output.stderr.decode('utf-8'))
	# if output.stdout:
	# 	print(output.stdout.decode('utf-8'))
	if logDir:
		pymmFunctions.unset_ffreport()
	
	# get the output path to rsync the deriv to access directories
	outputFilePath = outputOptions[-1]
	if pymmFunctions.boolean_answer(
		config['deriv delivery options'][derivType]
		):
		additional_delivery(outputFilePath,derivType,rsMulti)
	# print(outputFilePath)
	return outputFilePath

if __name__ == '__main__':
	main()
