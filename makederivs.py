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
def set_input_options(inputFilepath):
	inputOptions = []

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(derivType):
	middleOptions = []
	if derivType == 'resourcespace':
		middleOptions.append('-pix_fmt yuv420p')
		middleOptions.append('-c:v libx26')
		middleOptions.append('-bufsize 1835k')
		middleOptions.append('-f mp4')
		middleOptions.append('-crf 18')
		middleOptions.append('-maxrate 8760k')
		# and all the other stuff for making this deriv type
	elif derivType == 'mezzanine':
		middleOptions.append('BONZO')
		middleOptions.append('BANANAS')
	elif True == True:
		print('etc')
		# and so on
	print(middleOptions)
	return middleOptions

def set_output_options(derivType,inputFile,packageObjectDir):
	outputOptions = []
	baseMinusExtension = str(os.path.splitext(inputFile[0]))
	ext = str(os.path.splitext(inputFile[1]))
	if derivType == 'resourcespace':
		derivDeliv = os.path.join(packageObjectDir,'resourcespace')
		outputFilePath = derivDeliv+baseMinusExtension+'_lrp'+ext

	else:
		print('')
		# DO SOMETHING ELSE

	return outputOptions

def make_deriv(inputFilepath,derivType,packageObjectDir):
	print('doing stuff here')
	ffmpegCommand = []
	inputOptions = set_input_options(inputFilepath)
	middleOptions = set_middle_options(derivType)
	outputOptions = set_output_options(derivType,inputFilepath,packageObjectDir)
	ffmpegCommand = []
	# DO THE STUFF
	# PROBABLY CALL THIS WITH ALL THE PARAMETERS NEEDED
	# AND THEN CALL THE SUB-FUNCTIONS FROM HERE
	# SO THEY EACH ONLY NEED 1-2 AND I DON'T HAVE TO REPEAT PARAMS


