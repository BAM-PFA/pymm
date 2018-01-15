#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices
#
# MOVE AND / OR COPY STUFF -- @fixme : investigate borrowing file transfer code from UCSB or IFI
#
# on second thought maybe just use subprocess -> rsync and fuhgeddaboudit. we won't be using windows.
#

import os
import sys
import hashlib
import argparse
import subprocess
# local modules:
import pymmFunctions

def verify_copy():
	print('woof')



def check_write_permissions(destination):
	# check out IFI function: https://github.com/kieranjol/IFIscripts/blob/master/copyit.py#L43
	return True

def copy_file(inputFilepath,rsyncLogOptions,destination):
	# GET A HASH, RSYNC THE THING, GET A HASH OF THE DESTINATION FILE, CZECH THE TWO AND RETURN TRUE/FALSE
	# hashing redundant when using rsync.... 
	# inputFileHash = hash_file(inputFilepath)
	destFilepath = os.path.join(destination,pymmFunctions.get_base(inputFilepath,'basename'))
	if not rsyncLogOptions == '':
		rsyncCommand = ['rsync','-rtvPih','--log-file='+rsyncLogOptions,inputFilepath,destFilepath]
	# print(' '.join(rsyncCommand))
	if pymmFunctions.get_system() in ('mac','linux'):
		try:
			# subprocess.check_call(['rsync','-rtvPih',rsyncLogOptions,inputFilepath,destination],stderr=subprocess.PIPE) # mm puts the removal of source files in rsync command
			subprocess.check_call(rsyncCommand,stderr=subprocess.PIPE)
			return True
		except subprocess.CalledProcessError as error:
			print("rsync failed?")
			print (error)
			return error
	else:
		print('go get a mac, my man.')
	return False

def copy_dir(inputDir,destination):
	if os.path.isdir(destination):
		for _,_,_files in os.walk(inputDir):
			for _file in _files:
				copy_file(_file)
	else:
		print("the destination may or may not be a real directory, OOPS")
		return False
	# MAKE A BAG? HASH THE BAG? CHECK HASH OF DESTIATION BAG?

def set_args():
	parser = argparse.ArgumentParser(description='functions to move and copy stuff')
	parser.add_argument('-i','--inputPath',help='path of input file')
	parser.add_argument('-a','--algorithm',choices=['md5','sha1','sha256','sha512'],default='md5',help='choose an algorithm for checksum hashing; default is md5')
	parser.add_argument('-r','--removeOriginals',action='store_true',help='remove original files if copy is successful')
	# parser.add_argument('-',choices=['',''],help='')
	parser.add_argument('-d','--destination',help='set destination for files to move/copy')
	parser.add_argument('-l','--loglevel',choices=['all','pymm','None'],default='all',help='set the level of logging you want. rsync & pymm logs? just pymm? default is None.')

	return parser.parse_args()

def main():
	config = pymmFunctions.read_config()
	args = set_args()

	print(args)

	requiredArgs = ['inputPath','destination']
	# Quit if there are required variables missing
	missingArgs = 0
	for _arg in requiredArgs:
		if getattr(args,_arg) == None:
			print("CONFIGURATION PROBLEM:\n"
				  "You forgot to set "+_arg+". It is required.\n"
				  "Try again, but set "+_arg+" with the flag --"+_arg+"\n"
				)
			missingArgs += 1
	if missingArgs > 0:
		sys.exit()

	inputPath = args.inputPath
	algorithm = args.algorithm
	removeOriginals = args.removeOriginals
	destination = args.destination
	loglevel = args.loglevel
	now = pymmFunctions.timestamp('now')

	# set up rsync log
	if loglevel == 'all':
		pymmLogpath = os.path.join(config['logging']['pymm_log_dir'],'pymm_log.txt')
		try:
			rsyncLogpath = os.path.join(destination,'rsync_log_'+pymmFunctions.timestamp('now')+'.txt')
			# rsyncLogOptions = '--log-file = '+rsyncLogpath #+' --log-file-format= '+now+" '%f'"+" %l "+destination @fixme
			# print(rsyncLogOptions)
		except:
			print("there was a problem getting the rsync log path ....")
			rsyncLogpath = ''
	else:
		rsyncLogpath = ''

	# sniff what the input is
	dir_or_file = pymmFunctions.dir_or_file(inputPath)
	if dir_or_file == False:
		print("oy you've got big problems. "+inputPath+" is not a directory or a file. what is it? is it a ghost?")
		sys.exit()
	# copy the input according to its type
	elif dir_or_file == 'dir':
		copy_dir(inputPath,destination)
	elif dir_or_file == 'file':
		copy_file(inputPath,rsyncLogpath,destination)
	else:
		print("o_O what is going on here? you up to something?")
		sys.exit()

if __name__ == '__main__':
	main()
