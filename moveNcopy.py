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
# local modules:
import pymmFunctions

def verify_copy():
	print('woof')

def hash_file(inputFilepath,algorithm,blocksize=65536):
	# STOLEN DIRECTLY FROM UCSB BRENDAN COATES: https://github.com/brnco/ucsb-src-microservices/blob/master/hashmove.py
	hasher = hashlib.new(algorithm)
	with open(inputFilepath,'rb') as infile:
		buff = infile.read(blocksize) # read the file into a buffer cause it's more efficient for big files
		while len(buff) > 0: # little loop to keep reading
			hasher.update(buff) # here's where the hash is actually generated
			buff = infile.read(blocksize) # keep reading
	return hasher.hexdigest()

def check_write_permissions(destination):
	# check out IFI function: https://github.com/kieranjol/IFIscripts/blob/master/copyit.py#L43
	return True

def copy_file(inputFilepath,logpath,destination):
	# GET A HASH, RSYNC THE THING, GET A HASH OF THE DESTINATION FILE, CZECH THE TWO AND RETURN TRUE/FALSE
	inputFileHash = hash_file(inputFilepath)
	destFilepath = os.path.join(destination,inputFilepath)

	if pymmFunctions.get_system() in ('mac','linux'):
		subprocess.call(['rsync','-rtvPih','--log-file='+,''],stderr=subprocess.PIPE) # mm puts the removal of source files in rsync command
	
	return True

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
	parser = argparse.ArgumentParser(help='functions to move and copy stuff')
	parser.add_argument('-i','--inputPath',help='path of input file')
	parser.add_argument('-a','--algorithm',choices=['md5','sha1','sha256','sha512'],default='md5',help='choose an algorithm for checksum hashing; default is md5')
	parser.add_argument('-r','--removeOriginals',action='store_true',help='remove original files if copy is successful')
	# parser.add_argument('-',choices=['',''],help='')
	parser.add_argument('-d','--destination',help='set destination for files to move/copy')

	return parser.parse_args()

def main():
	config = pymmFunctions.read_config()
	args = set_args()

	inputPath = args.inputPath
	algorithm = args.algorithm
	removeOriginals = args.removeOriginals
	destination = args.destination

	

	dir_or_file = pymmFunctions.dir_or_file(inputPath)
	if dir_or_file == False:
		print("oy you've got big problems. "+inputPath+" is not a directory or a file. what is it? is it a ghost?")
		sys.exit()
	elif dir_or_file == 'dir':
		copy_dir(inputFilepath,destination)
	elif dir_or_file == 'file':
		copy_file(inputFilepath,logPath,destination)
	else:
		print("o_O what is going on here? you up to something?")
		sys.exit()


