#!/usr/bin/env python3
# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?

import os
import sys
import ffmpy

# SET FFMPEG INPUT OPTIONS
def set_input_options():
	inputOptions = ''

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(derivType):
	middleOptions = ''
	if derivType == 'resourcespace':
		middleOptions += '-pix_fmt yuv420p'
		middleOptions += '-c:v libx26'
		middleOptions += '-bufsize 1835k'
		middleOptions += '-f mp4'
		middleOptions += '-crf 18'
		middleOptions += '-maxrate 8760k'
		# and all the other stuff for making this deriv type
	elif:
		derivType == 'mezzanine':
		middleOptions += 'BONZO'
		middleOptions += 'BANANAS'
	elif:
		# and so on

	return middleOptions

def set_output_options(derivType,inputFile,packageObjectDir):
	baseMinusExtension = os.path.split(inputFile,'.') # OR WHATEVER IT REALLY IS
	ext = inputFile # EXTENSION
	if derivType == 'resourcespace':
		derivDeliv = os.path.join(packageObjectDir,'resourcespace')
		outputFilePath = derivDeliv+baseMinusExtension+'_lrp'+ext
	else:
		# DO SOMETHING ELSE

def make_deriv(inputFile):
	# DO THE STUFF
	# PROBABLY CALL THIS WITH ALL THE PARAMETERS NEEDED
	# AND THEN CALL THE SUB-FUNCTIONS FROM HERE
	# SO THEY EACH ONLY NEED 1-2 AND I DON'T HAVE TO REPEAT PARAMS


