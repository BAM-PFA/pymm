#!/usr/bin/env python3
#
# these are functions to output metadata files
# and structured data (xml/json)
#

import os
import subprocess
import sys
import json
import argparse
import configparser
import hashlib
# nonstandard libraries:
import xmltodict
# local modules:
import pymmFunctions

def get_mediainfo_report(inputFilepath,destination,json=False):
	basename = pymmFunctions.get_base(inputFilepath)
	# write mediainfo output to a logfile if the destination is a directory
	if os.path.isdir(destination):
		mediainfoOutput = '--LogFile='+os.path.join(destination,basename+'_mediainfo.xml')
		mediainfoXML = subprocess.Popen(['mediainfo',inputFilepath,'--Output=XML',mediainfoOutput],stdout=subprocess.PIPE)
		mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])
		if json:
			return mediainfoJSON    
		else:
			return True
	# otherwise pass something like '' as a destination and just get the raw mediainfo output
	else:
		mediainfoXML = subprocess.Popen(['mediainfo',inputFilepath],stdout=subprocess.PIPE)
		mediainfoJSON = xmltodict.parse(mediainfoXML.communicate()[0])
		if json:
			return mediainfoJSON
		else:
			print(destination+" doesn't exist and you didn't say you want the raw mediainfo output.\n"
					"What do you want??")
			return False

def hash_file(inputFilepath,algorithm='md5',blocksize=65536):
	# STOLEN DIRECTLY FROM UCSB BRENDAN COATES: https://github.com/brnco/ucsb-src-microservices/blob/master/hashmove.py
	hasher = hashlib.new(algorithm)
	with open(inputFilepath,'rb') as infile:
		buff = infile.read(blocksize) # read the file into a buffer cause it's more efficient for big files
		while len(buff) > 0: # little loop to keep reading
			hasher.update(buff) # here's where the hash is actually generated
			buff = infile.read(blocksize) # keep reading
	return hasher.hexdigest()

def make_frame_md5(inputFilepath,metadataDir):
	print('making frame md5')
	print(metadataDir)
	if not pymmFunctions.is_av(inputFilepath):
		# FUN FACT: YOU CAN RUN FFMPEG FRAMEMD5 ON A TEXT FILE!!
		print(inputFilepath+" IS NOT AN AV FILE SO WHY ARE YOU TRYING TO MAKE A FRAME MD5 REPORT?")
		return False
	else:
		md5File = pymmFunctions.get_base(inputFilepath)+"_frame-md5.txt"
		frameMd5Filepath = os.path.join(metadataDir,md5File)
		frameMd5Command = ['ffmpeg','-i',inputFilepath,'-f','framemd5',frameMd5Filepath]
		output = subprocess.Popen(frameMd5Command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		try:
			out,err = output.communicate()
			if err:
				print(err.decode('utf-8'))
			return frameMd5Filepath
		except:
			return False

def main():
	config = pymmFunctions.read_config() # THIS IS PROBABLY NOT GOING TO BE NEEDED

	parser = argparse.ArgumentParser()
	parser.add_argument('-i','--inputFilepath',help='path of input file')
	parser.add_argument('-m','--mediainfo',action='store_true',help='generate a mediainfo sidecar file')
	parser.add_argument('-f','--frame_md5',action='store_true',help='make frame md5 report')
	parser.add_argument('-j','--getJSON',action='store_true',default=False,help='get JSON output as applicable')
	parser.add_argument('-d','--destination',help='set destination for output metadata files')
	args = parser.parse_args()
	
	inputFilepath = args.inputFilepath
	destination = args.destination
	frame_md5 = args.frame_md5
	mediainfo_report = args.mediainfo
	getJSON = args.getJSON

	if not inputFilepath:
		print("\n\nHEY THERE, YOU NEED TO SET AN INPUT FILE TO RUN THIS SCRIPT ON.\rNOW EXITING")
		sys.exit()
	if not destination:
		print('''
			YOU DIDN'T TELL ME WHERE TO PUT THE OUTPUT OF THIS SCRIPT,
			SO WE'LL PUT ANY SIDECAR FILES IN THE SAME DIRECTORY AS YOUR INPUT FILE.
			''')
		destination = os.path.dirname(os.path.abspath(inputFilepath))
	# print(destination,inputFilepath)
	# fileHash = hash_file(inputFilepath)
	# print(fileHash)
	if mediainfo_report:
		get_mediainfo_report(inputFilepath,destination,getJSON)
	if frame_md5:
		frameMd5Filepath = make_frame_md5(inputFilepath,destination)
		print(frameMd5Filepath)

if __name__ == '__main__':
	main()
