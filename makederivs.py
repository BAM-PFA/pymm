#!/usr/bin/env python3
import os
import ffmpy

# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?

# SET FFMPEG INPUT OPTIONS
def set_input_options():
	inputOptions = ''

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(outputType):
	middleOptions = ''
	if outputType == 'resourcespace':
		middleOptions += '-pix_fmt yuv420p'
		middleOptions += '-c:v libx26'
		middleOptions += '-bufsize 1835k'
		middleOptions += '-f mp4'
		middleOptions += '-crf 18'
		middleOptions += '-maxrate 8760k'
		# and all the other stuff for making this deriv type

	elif:
		# and so on

	return middleOptions

