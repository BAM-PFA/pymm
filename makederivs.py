#!/usr/bin/env python3
# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?

import os
import sys
import configparser
import subprocess
import time
from datetime import date
from ffmpy import FFprobe, FFmpeg
import pymmFunctions

pymmConfig = pymmFunctions.read_config()


# SET FFMPEG INPUT OPTIONS
def set_input_options(derivType,inputFilepath):
	inputOptions = ['-i']
	inputOptions.append(inputFilepath)
	
	return inputOptions

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(derivType):
	middleOptions = []
	if derivType == 'resourcespace':
		middleOptions = [
			'-movflags','faststart',
			'-pix_fmt','yuv420p',
			'-c:v','libx264',
			'-bufsize','1835k',
			'-f','mp4',
			'-crf','18',
			'-maxrate','8760k',
			'-c:a','aac',
			'-ac','2',
			'-b:a','320k',
			'-ar','48000'
			]
	elif derivType == 'mezzanine':
		middleOptions = [
			'BONZO',
			'BANANAS'
			]
	elif True == True:
		print('etc')
		# and so on

	# print(middleOptions)
	return middleOptions

def set_output_options(derivType,inputFile,packageDerivDir):
	outputOptions = []
	base = os.path.basename(inputFile)
	baseAndExt = os.path.splitext(base)
	baseMinusExtension = baseAndExt[0]
	ext_original = baseAndExt[1]
	if derivType == 'resourcespace':
		ext = 'mp4'
		derivDeliv = os.path.join(packageDerivDir,'resourcespace')
		if not os.path.isdir(derivDeliv):
			os.mkdir(derivDeliv)
		outputFilePath = os.path.join(derivDeliv,baseMinusExtension+'_lrp.'+ext)
		outputOptions.append(outputFilePath)
	else:
		print('~ ~ ~ ~ ~')
		# DO STUFF TO OTHER DERIV TYPES

	return outputOptions

def make_deriv(inputFilepath,derivType,packageDerivDir):
	print('doing stuff here')
	ffmpegArgs = []
	inputOptions = set_input_options(derivType,inputFilepath)
	middleOptions = set_middle_options(derivType)
	outputOptions = set_output_options(derivType,inputFilepath,packageDerivDir)
	ffmpegArgs = inputOptions+middleOptions+outputOptions
	ffmpegArgs.insert(0,'ffmpeg')
	# print(' '.join(ffmpegArgs))
	# print(ffmpegArgs)
	output = subprocess.Popen(ffmpegArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	out,err = output.communicate()
	print(out.decode('utf-8'))
	if err:
		print(err.decode('utf-8'))
	# DO THE STUFF
	# PROBABLY CALL THIS WITH ALL THE PARAMETERS NEEDED
	# AND THEN CALL THE SUB-FUNCTIONS FROM HERE
	# SO THEY EACH ONLY NEED 1-2 AND I DON'T HAVE TO REPEAT PARAMS


