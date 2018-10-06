#!/usr/bin/env python3
#
# MOVE AND / OR COPY STUFF -- @fixme : investigate borrowing file transfer code from UCSB or IFI
#
# This is basically a couple of functions to call rsync :/
#
import glob
import os
import sys
import hashlib
import argparse
import subprocess
# local modules:
import makeMetadata
import pymmFunctions

def move_n_verify_sip(
	stagedSIPpath,
	destination,
	destinationLogPath=None
	):
	'''
	move a valid sip to a destination 
	(intended for LTO) and run a hashdeep audit on it
	'''
	safe = False
	# test for the gcp path and if `dbus-launch` is needed in linux
	# this returns a list of either one or two items:
	# ['/path/to/gcp/binary'] or ['dbus-launch','/path/etc']
	gcpPath = pymmFunctions.gcp_test()
	if gcpPath == ['']:
		# if gcp is not installed, exit the function
		return safe

	gcpOptions = [
	'--preserve=mode,timestamps',
	'-rv',
	stagedSIPpath,
	destination
	]
	gcpCommand = gcpPath+gcpOptions

	manifestPattern = os.path.join(stagedSIPpath,'hashdeep_manifest*')
	SIPmanifestName = os.path.basename(glob.glob(manifestPattern)[0])
	SIPbase = os.path.basename(stagedSIPpath)
	destSIP = os.path.join(destination,SIPbase)

	destManifest = os.path.join(destSIP,SIPmanifestName)

	gcp = subprocess.run(
		gcpCommand,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
		)

	verify = makeMetadata.hashdeep_audit(
		destSIP,
		destManifest,
		'SIP'
		)
	if verify == True:
		safe = True
	else:
		safe = False

	try:
		verify = verify.decode()
	except:
		verify = str(verify)


	print("HASHDEEP AUDIT RESULT|{}|{}".format(SIPbase,verify))
	print(verify)
	return destSIP,safe

def mv_object(inputPath,destination):
	'''
	call mv on an object... 
	'''
	command = [
		'mv','-f',
		inputPath,
		destination
		]
	out = subprocess.run(command,stdout=subprocess.PIPE)
	if out.returncode == 0:
		return True
	else:
		return False

def rsync_object(inputDir,rsyncLogPath,destination):
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
	parser.add_argument(
		'-s','--movingSIP',
		action='store_true',
		default=False,
		help='run move_n_verify_sip on input'
		)
	parser.add_argument(
		'-m','--useMV',
		action='store_true',
		default=False,
		help='try to use `mv` instead of rsync on the same filesystem'
		)

	return parser.parse_args()

def main():
	config = pymmFunctions.read_config()
	args = set_args()
	requiredArgs = ['inputPath','destination']
	inputPath = args.inputPath
	movingSIP = args.movingSIP
	algorithm = args.algorithm
	removeOriginals = args.removeOriginals
	destination = args.destination
	loglevel = args.loglevel
	logDir = args.logDir
	useMV = args.useMV
	now = pymmFunctions.timestamp('now')
	# Quit if there are required variables missing
	missingArgs = 0

	try:
		# see if the input/destination are on the same filesystem
		# if so, we will use mv rather than rsync for efficiency
		inputFS = pymmFunctions.get_filesystem_id(inputPath)
		destFS = pymmFunctions.get_filesystem_id(destination)
		print(inputFS,destFS)
		if inputFS == destFS:
			print("HEYYYY")
			sameFilesystem = True
		else:
			sameFilesystem = False
	except:
		sameFilesystem = False

	for _arg in requiredArgs:
		if getattr(args,_arg) == None:
			print("CONFIGURATION PROBLEM:\n"
				  "You forgot to set {0}. It is required.\n"
				  "Try again, but set {0} with the flag --{0}\n".format(_arg)
				)
			missingArgs += 1
	if missingArgs > 0:
		sys.exit()

	if not movingSIP:
		# set up rsync log
		if loglevel == 'all':
			pymmLogpath = os.path.join(config['logging']['pymm_log_dir'],'pymm_log.txt')
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
			return False,False
			# sys.exit(1)
		# copy the input according to its type
		elif dir_or_file == 'dir':
			# add trailing slash for rsync destination directory
			if not destination[-1] == '/':
				destination = destination+'/'
			if not sameFilesystem == True:
				rsync_object(inputPath,rsyncLogPath,destination)
			else:
				mv_object(inputPath,destination)
		elif dir_or_file == 'file':
			if not sameFilesystem == True or useMV == False:
				rsync_object(inputPath,rsyncLogPath,destination)
			else:
				mv_object(inputPath,destination)
		else:
			print("o_O what is going on here? you up to something?")
			# sys.exit()
		
	else:
		stagedSIPpath,safe = move_n_verify_sip(inputPath,destination)
		print(stagedSIPpath)
		return stagedSIPpath,safe

if __name__ == '__main__':
	main()
