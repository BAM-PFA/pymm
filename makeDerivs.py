#!/usr/bin/env python3
# YOU WANT TO MAKE SOME DERIVATIVES, PUNK?
import os
import sys
import subprocess
import argparse
import json
# local modules:
import pymmFunctions
import moveNcopy

config = pymmFunctions.read_config()

# SET FFMPEG INPUT OPTIONS
def set_input_options(derivType,inputPath,ffmpegLogDir=None):
	inputOptions = ['-i']
	inputOptions.append(inputPath)
	if ffmpegLogDir:
		inputOptions.append('-report')
	
	return inputOptions

# SET FFMPEG MIDDLE OPTIONS
def set_middle_options(derivType):
	middleOptions = []
	if derivType == 'resourcespace':
		# make an mp4 file for upload to ResourceSpace
		# also used as our Proxy for access screenings
		# list in config setting requires double quotes
		middleOptions = json.loads(config['ffmpeg']['resourcespace_opts'])

	elif derivType == 'proresHQ':
		# make a HQ prores .mov file as a mezzanine for color correction, cropping, etc.
		middleOptions = json.loads(config['ffmpeg']['proresHQ_opts'])
	
	elif True == True:
		print('etc')
		# and so on

	return middleOptions

def set_output_options(derivType,inputPath,outputDir):
	outputOptions = []
	strict = ['-strict','-2'] 
	base = pymmFunctions.get_base(inputPath)
	baseMinusExtension = pymmFunctions.get_base(inputPath,'baseMinusExtension')
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
		outputOptions.extend(strict)
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
	parser.add_argument('-i','--inputPath',help='path of input file')
	parser.add_argument('-d','--derivType',choices=['resourcespace','proresHQ'],help='choose a derivative type to output')
	parser.add_argument('-o','--outputDir',help='set output directory for deriv delivery')
	parser.add_argument('-r','--logDir',help='set output directory for ffmpeg and rsync logs')
	# parser.add_argument('-m','--packageMetadataObjects',help='set directory for deriv metadata')

	return parser.parse_args()

def additional_delivery(derivFilepath,derivType,rsyncLogDir):
	destinations = 	{'resourcespace': config['paths']['resourcespace_deliver'],'proresHQ':config['paths']['prores_deliver']}
	deliveryDir = destinations[derivType]
	if deliveryDir == '':
		print("there's no directory set for "+derivType+" delivery... SET IT!!")
		pass
	else:
		sys.argv = ['','-i'+derivFilepath,'-d'+deliveryDir,'-L'+rsyncLogDir]
		try:
			moveNcopy.main()
		except:
			print('there was an error in rsyncing the output deriv to the destination folder')

def main():
	# DO STUFF
	args = set_args()
	inputPath = args.inputPath
	# for ingestfile.py this is the packageDerivDir
	outputDir = args.outputDir
	derivType = args.derivType
	logDir = args.logDir
	if logDir:
		pymmFunctions.set_ffreport(logDir,'makeDerivs')
	ffmpegArgs = []
	inputOptions = set_input_options(derivType,inputPath,logDir)
	middleOptions = set_middle_options(derivType)
	outputOptions = set_output_options(derivType,inputPath,outputDir)
	ffmpegArgs = inputOptions+middleOptions+outputOptions
	ffmpegArgs.insert(0,'ffmpeg')
	print(ffmpegArgs)
	output = subprocess.Popen(ffmpegArgs,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	out,err = output.communicate()
	# print(out.decode('utf-8'))
	if err:
		print(err.decode('utf-8'))
	if logDir:
		pymmFunctions.unset_ffreport()
	# get the output path to rsync the deriv to access directories
	outputFilePath = outputOptions[-1]
	if pymmFunctions.boolean_answer(config['deriv delivery options'][derivType]):
		additional_delivery(outputFilePath,derivType,logDir)
	# print(outputFilePath)
	return outputFilePath

if __name__ == '__main__':
	main()
