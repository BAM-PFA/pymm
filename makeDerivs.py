#!/usr/bin/env python3
# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?
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
	"-ac":"2",
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
	if isSequence:
		# get variables needed to process a derivative from a dpx sequence
		audioPath,\
		filePattern,\
		startNumber,\
		framerate = pymmFunctions.parse_sequence_parent(inputPath)
		# print(audioPath)
		inputOptions = [
			'-start_number',startNumber,
			'-i',filePattern
			]
		if framerate:
			inputOptions.extend(['-r',framerate])
		if audioPath:
			inputOptions.extend(
				['-i',audioPath]
				)
	else:
		audioPath = None
		inputOptions = ['-i',inputPath]

	if ffmpegLogDir:
		inputOptions.append('-report')
	
	return inputOptions

def set_middle_options(derivType,inputType,inputPath,mixdown):
	'''
	SET FFMPEG MIDDLE OPTIONS
	'''
	middleOptions = []
	if derivType == 'resourcespace':
		# make an mp4 file for upload to ResourceSpace
		# also used as our Proxy for access screenings
		# list in config setting requires double quotes
		if inputType in ('VIDEO','sequence'):
			middleOptions = json.loads(config['ffmpeg']['resourcespace_video_opts'])
		elif inputType == 'AUDIO':
			middleOptions = json.loads(config['ffmpeg']['resourcespace_audio_opts'])

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
		
		audio_filter = add_audio_filter(middleOptions,inputPath)
		# print(audio_filter)
		if audio_filter:
			middleOptions['-filter_complex'] = audio_filter
			middleOptions['-map'] = '[out] -map 0:v'
		if mixdown:
			middleOptions['-ac'] = '1'

	elif derivType == 'proresHQ':
		# make a HQ prores .mov file as a mezzanine 
		# for color correction, cropping, etc.
		middleOptions = json.loads(config['ffmpeg']['proresHQ_opts'])
	
	elif True == True:
		print('etc')
		# and so on

	middleOptions = middleOptions_to_list(middleOptions)

	return middleOptions

def set_output_options(derivType,inputType,inputPath,outputDir):
	outputOptions = []
	# the ffmpeg docs say the strict flag is no longer required 
	# for aac encoding in mp4 but I ran into issues without it, 
	# so I'll keep it for now (7/2018)
	strict = ['-strict','-2'] 
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
			outputOptions.extend(strict)
		elif inputType == 'AUDIO':
			ext = 'mp3'
		else:
			ext = 'mp4'
			print("FUCK EVERYTHING: ERROR GETTING THE FILE TYPE.")
		outputFilePath = os.path.join(
			derivDeliv,
			baseMinusExtension+'_access.'+ext
			)
		outputOptions.append(outputFilePath)
	elif derivType == 'proresHQ':
		ext = 'mov'
		outputFilePath = os.path.join(
			derivDeliv,
			baseMinusExtension+'_proresHQ.'+ext
			)
		outputOptions.append(outputFilePath)
	else:
		print('~ ~ ~ ~ ~')
		# DO STUFF TO OTHER DERIV TYPES
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

def add_audio_filter(middleOptions,inputPath):
	'''
	check for audio streams and add to a filter that will merge them all 
	'''
	audioStreamCount = pymmFunctions.get_audio_stream_count(inputPath)
	if not audioStreamCount:
		audioFilter = None
	else:
		audioFilter = 'amerge[out]' # this is the end of the filter
		
		for stream in reversed(range(audioStreamCount)):
			streamIndex = "[0:a:{}]".format(str(stream))
			audioFilter = streamIndex+audioFilter
		# YOU DONT NEED To WRAP THE FILTER (OR ANYTHING ELSE?) IN QUOTES
		# WHEN CALLING FROM SUBPROCESS
		# audioFilter = '"{}"'.format(audioFilter) # wrap the filter in quotes

	return audioFilter

def middleOptions_to_list(middleOptions):
	temp = []
	[temp.extend([key,value]) for key, value in middleOptions.items()]
	temp2 = []
	# print(temp)
	for item in temp:
		temp2.extend(item.split(' '))
	print(temp2)
	middleOptions = temp2

	return middleOptions

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
		default=True,
		help="Do/don't mix down all audio tracks to mono for access copy. Default=True"
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

	if logDir:
		pymmFunctions.set_ffreport(logDir,'makeDerivs')

	if not isSequence:
		inputType = pymmFunctions.is_av(inputPath)
	else:
		inputType = 'sequence'
	ffmpegArgs = []
	inputOptions = set_input_options(
		derivType,
		inputPath,
		logDir,
		isSequence
		)
	middleOptions = set_middle_options(
		derivType,
		inputType,
		inputPath,
		mixdown
		)
	outputOptions = set_output_options(
		derivType,
		inputType,
		inputPath,
		outputDir
		)
	
	ffmpegArgs = inputOptions+middleOptions+outputOptions
	ffmpegArgs.insert(0,'ffmpeg')
	print(ffmpegArgs)
	print(' '.join(ffmpegArgs))
	arglist = ' '.join(ffmpegArgs)
	output = subprocess.run(
		arglist.split(),
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
