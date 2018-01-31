#!/usr/bin/env python3
# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?
import os
import sys
import subprocess
import argparse
# nonstandard libraries;
from ffmpy import FFprobe, FFmpeg
# local modules:
import pymmFunctions
import moveNcopy

config = pymmFunctions.read_config()

# SET FFMPEG INPUT OPTIONS
def set_input_options(derivType,inputFilepath,ffmpegLogDir=None):
	# ARE THERE CASES WHERE I WILL ACTUALLY WANT TO SET MORE INPUT OPTIONS?
	# IT'S USED IN mm BUT WILL WE??
	inputOptions = ['-i']
	inputOptions.append(inputFilepath)
	if ffmpegLogDir:
		inputOptions.append('-report')
	
	return inputOptions

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(derivType):
	middleOptions = []
	if derivType == 'resourcespace':
		# make an mp4 file for upload to ResourceSpace
		# also used as our Proxy for access screenings
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
	elif derivType == 'proresHQ':
		# make a HQ prores .mov file as a mezzanine for color correction, cropping, etc.
		middleOptions = [
			'-map','0:v',
			'-c:v','prores_ks',
			'-profile:v','3',
			 # keep it interlaced
			'-flags','+ildct+ilme',
			# map for audio if it exists
			'-map','0:a?',
			# is 16 bit good for our HQ mezzanine? 
			'-c:a','pcm_s16le'
			]
	elif True == True:
		print('etc')
		# and so on

	# print(middleOptions)
	return middleOptions

def set_output_options(derivType,inputFilepath,outputDir):
	outputOptions = []
	base = pymmFunctions.get_base(inputFilepath)
	baseMinusExtension = pymmFunctions.get_base(inputFilepath,'baseMinusExtension')
	# make a delivery directory for a package that is based on the deriv type
	derivDeliv = os.path.join(outputDir,derivType)
	if not os.path.isdir(derivDeliv):
		print("Making a directory at "+derivDeliv)
		try:
			os.mkdir(os.path.join(outputDir,derivType))
		except:
			print("couldn't make a dir at "+derivDeliv)
	if derivType == 'resourcespace':
		ext = 'mp4'
		outputFilePath = os.path.join(derivDeliv,baseMinusExtension+'_lrp.'+ext)
		outputOptions.append(outputFilePath)
	elif derivType == 'proresHQ':
		ext = 'mov'
		outputFilePath = os.path.join(derivDeliv,baseMinusExtension+'_proresHQ.'+ext)
		outputOptions.append(outputFilePath)
	else:
		print('~ ~ ~ ~ ~')
		# DO STUFF TO OTHER DERIV TYPES
	return outputOptions

def set_args():
	parser = argparse.ArgumentParser(description='make derivatives of an input a/v file')
	parser.add_argument('-i','--inputFilepath',help='path of input file')
	parser.add_argument('-d','--derivType',choices=['resourcespace','proresHQ'],help='choose a derivative type to output')
	parser.add_argument('-o','--outputDir',help='set output directory for deriv delivery')
	parser.add_argument('-r','--ffmpegReportDir',help='set output directory for ffmpeg report')

	return parser.parse_args()

def additional_delivery(derivFilepath,derivType):
	destinations = 	{'resourcespace': config['paths']['resourcespace_deliver'],'proresHQ':config['paths']['prores_deliver']}
	deliveryDir = destinations[derivType]
	if deliveryDir == '':
		print("there's no directory set for "+derivType+" delivery... SET IT!!")
		pass
	else:
		sys.argv = ['','-i'+derivFilepath,'-d'+deliveryDir,'-L'+deliveryDir]
		try:
			moveNcopy.main()
		except:
			print('there was an error in rsyncing the output deriv to the destination folder')

def main():
	# DO STUFF
	args = set_args()
	inputFilepath = args.inputFilepath
	# for ingestfile.py this is the packageDerivDir
	outputDir = args.outputDir
	derivType = args.derivType
	ffmpegReportDir = args.ffmpegReportDir
	if ffmpegReportDir:
		pymmFunctions.set_ffreport(ffmpegReportDir,'makeDerivs')
	ffmpegArgs = []
	inputOptions = set_input_options(derivType,inputFilepath,ffmpegReportDir)
	middleOptions = set_middle_options(derivType)
	outputOptions = set_output_options(derivType,inputFilepath,outputDir)
	ffmpegArgs = inputOptions+middleOptions+outputOptions
	ffmpegArgs.insert(0,'ffmpeg')
	print(ffmpegArgs)
	output = subprocess.Popen(ffmpegArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	out,err = output.communicate()
	print(out.decode('utf-8'))
	if err:
		print(err.decode('utf-8'))
	if ffmpegReportDir:
		pymmFunctions.unset_ffreport()
	outputFilePath = outputOptions[-1]
	additional_delivery(outputFilePath,derivType)


if __name__ == '__main__':
	main()
