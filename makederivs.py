#!/usr/bin/env python3

# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?

# SET FFMPEG INPUT OPTIONS
def set_input_options():
	inputOptions = ''

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(outputType):
	middleOptions = ''
	if outputType == 'resourcespace':
		middleOptions += '-pix_fmt yuv420p'
		# and all the other stuff for making this deriv type

	elif:
		# and so on

	return middleOptions

