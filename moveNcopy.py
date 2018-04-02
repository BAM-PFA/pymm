#!/usr/bin/env python3
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

def copy_file(inputPath,rsyncLogPath,destination):
	'''
	call rsync on an input file
	'''
	destFilepath = os.path.join(destination,pymmFunctions.get_base(inputPath))
	if not rsyncLogPath == '':
		rsyncCommand = [
			'rsync','-rtvPih',
			'--log-file={}'.format(rsyncLogPath),
			inputPath,
			destination
			]
	else:
		rsyncCommand = [
			'rsync','-rtvPih',
			inputDir,
			destination
			]		
	# print(rsyncCommand)
	if pymmFunctions.get_system() in ('mac','linux'):
		try:
			subprocess.check_call(rsyncCommand,stderr=subprocess.PIPE)
			return True
		except subprocess.CalledProcessError as error:
			print("rsync failed?")
			print (error)
			return error
	else:
		print('go get a mac, my man.')
	return False

def copy_dir(inputDir,rsyncLogPath,destination):
	'''
	call rsync on an input dir
	'''
	if not rsyncLogPath == '':
		rsyncCommand = [
			'rsync','-rtvPih',
			'--log-file={}'.format(rsyncLogPath),
			inputDir,
			destination
			]
	else:
		rsyncCommand = ['rsync','-rtvPih',inputDir,destination]		

	# print(rsyncCommand)
	if pymmFunctions.get_system() in ('mac','linux'):
		try:
			process = subprocess.Popen(
					rsyncCommand,
					stdout=subprocess.PIPE,
					stderr=subprocess.PIPE
				)
			log,err = process.communicate()
			if not os.path.isfile(rsyncLogPath):
				try:
					with open(rsyncLogPath,'wb') as lf:
						lf.write(log)
				except:
					print("can't write log...")
			return True
		except subprocess.CalledProcessError as error:
			print("rsync failed?")
			print (error)
			return error
	else:
		print('go get a mac, my man.')
	return False

	# WELL THIS WOUND UP BEING IDENTICAL TO THE ABOVE.... 
	# MAYBE MAKE AN 'RSYNC_IT' FUNCTION THAT IS CALLED IF
	# SYS.PLATFORM CHECK == MAC/LINUX

def set_args():
	parser = argparse.ArgumentParser(
		description='functions to move and copy stuff'
		)
	parser.add_argument(
		'-i','--inputPath',
		help='path of input file'
		)
	parser.add_argument(
		'-a','--algorithm',
		choices=['md5','sha1','sha256','sha512'],
		default='md5',
		help='choose an algorithm for checksum hashing; default is md5'
		)
	parser.add_argument(
		'-r','--removeOriginals',
		action='store_true',
		default=False,
		help='remove original files if copy is successful'
		)
	parser.add_argument(
		'-d','--destination',
		help='set destination for files to move/copy'
		)
	parser.add_argument(
		'-l','--loglevel',
		choices=['all','pymm','None'],
		default='all',
		help='set level of logging. default is None.'
		)
	parser.add_argument(
		'-L','--logDir',
		help='set a directory for the rsync log to live in'
		)

	return parser.parse_args()

def main():
	config = pymmFunctions.read_config()
	args = set_args()
	requiredArgs = ['inputPath','destination']
	inputPath = args.inputPath
	algorithm = args.algorithm
	removeOriginals = args.removeOriginals
	destination = args.destination
	loglevel = args.loglevel
	logDir = args.logDir
	now = pymmFunctions.timestamp('now')
	# Quit if there are required variables missing
	missingArgs = 0
	for _arg in requiredArgs:
		if getattr(args,_arg) == None:
			print("CONFIGURATION PROBLEM:\n"
				  "You forgot to set {0}. It is required.\n"
				  "Try again, but set {0} with the flag --{0}\n".format(_arg)
				)
			missingArgs += 1
	if missingArgs > 0:
		sys.exit()

	# set up rsync log
	if loglevel == 'all':
		pymmLogpath = os.path.join(config['logging']['pymm_log_dir'],'pymm_log.txt')
		# AT WHAT POINT WILL WE ACTUALLY WANT TO PYMMLOG A COPY? FINAL AIP XFER?
		try:
			rsyncLogPath = os.path.join(
				logDir,
				'rsync_log_{}_{}.txt'.format(
					pymmFunctions.get_base(inputPath),
					pymmFunctions.timestamp('now')
					)
				)
		except:
			print("there was a problem getting the rsync log path ....")
			rsyncLogPath = ''
	else:
		rsyncLogPath = '.'

	# sniff what the input is
	dir_or_file = pymmFunctions.dir_or_file(inputPath)
	if dir_or_file == False:
		print("oy you've got big problems. {} is not a directory or a file."
			" what is it? is it a ghost?".format(inputPath))
		sys.exit(1)
	# copy the input according to its type
	elif dir_or_file == 'dir':
		# add trailing slash for rsync destination directory
		if not destination[-1] == '/':
			destination = destination+'/'
		copy_dir(inputPath,rsyncLogPath,destination)
	elif dir_or_file == 'file':
		copy_file(inputPath,rsyncLogPath,destination)
	else:
		print("o_O what is going on here? you up to something?")
		sys.exit()

if __name__ == '__main__':
	main()
