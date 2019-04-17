#!/usr/bin/env python3
import os
from pathlib import Path
import sys
import time
# local modules
try:
	import pymmFunctions
except:
	from . import pymmFunctions
# inputPath = sys.argv[1]

def scan_dir(inputPath):
	'''
	expected image sequence dir structure:
	- title_accesssion#_barcode_r01of01/
		documentation [optional]/
			documentation.jpg
			documentation.txt
		dpx/
			title_accesssion#_barcode_r01of01_0008600.dpx
			title_accesssion#_barcode_r01of01_0008601.dpx
			<etc>
		title_accesssion#_barcode_r01of01.wav
	~OR~
	- title_accesssion#/
		title_accesssion#_barcode_r01of02/
			dpx/
				title_accesssion#_barcode_r01of02_0008600.dpx
				title_accesssion#_barcode_r01of02_0008601.dpx
				<etc>
			title_accesssion#_barcode_r01of02.wav
		title_accesssion#_barcode_r01of02/
			dpx/
				title_accesssion#_barcode_r02of02_0008600.dpx
				title_accesssion#_barcode_r02of02_0008601.dpx
				<etc>
			title_accesssion#_barcode_r02of02.wav

	return a tuple: (True/False, [list of illegal subdirs])
	'''
	# remove any empty folders
	for root,dirs,files in os.walk(inputPath):
		for _dir in dirs:
			path = os.path.join(root,_dir)
			if os.path.isdir(path):
				contents = os.listdir(path)
				if len(contents) == 0:
					print("removing an empty folder at "+path)
					os.rmdir(path)
	# start looking for inappropriate/unrecorgnized folders
	outcome = []
	dirs = []
	status = None
	hasDocumentation = False
	for entry in os.scandir(inputPath):
		# cast the fiery circle,
		# summon all the subdirectories 
		# for judgement before my wrath
		if entry.is_dir():
			dirs.append(entry.path)
	print(dirs)
	if len(dirs) > 0:
		if len(dirs) == 1:
			dirname = os.path.basename(dirs[0]).lower()
			# if there is only one subdir and it isn't
			# DPX or documentation, report it as a problem
			if dirname not in ('dpx','documentation'):
				outcome = dirs
				status = False
			elif dirname == 'documentation':
				# if the only subdir is documentation, return that

				status = True
				outcome = 'documentation'
			elif dirname == 'dpx':
				status = True
				outcome = 'dpx'

		elif len(dirs) > 1:
			baddies = []
			for _dir in dirs:
				# if there's more than one subdirectory make sure it either:
				# a) is documentation OR
				# b) contains a DPX subfolder
				if not os.path.basename(_dir).lower() == 'documentation':
					for root,subs,_ in os.walk(_dir):
						# grab any non-dpx dirs to return
						badThings = [
							os.path.join(root,sub) for sub in subs \
								if sub.lower() != 'dpx'
							]
						for thing in badThings:
							baddies.append(thing)
			if baddies != []:
				# there shouldn't be anything other than dpx
				# or documentation folders at this level
				status = False
				for baddie in baddies:
					outcome.append(baddie)
			else:
				print("Image sequence folders are ok")
				status = True
				outcome = 'dpx' # is this true?? @fixme

	return status,outcome

def check_for_bad_files(inputPath):
	'''
	This function is insane and duplicates efforts in pymmFunctions.
	What is it even trying to accomplish?
	@fixme
	'''
	# print(time.time())
	toCheck = []
	badFiles = []
	result = True
	for root, dirs, files in os.walk(inputPath):
		for _file in files:
			if not _file.startswith('.'):
				filePath = os.path.join(root,_file)
				if '/documentation/' not in filePath:
					_,ext = os.path.splitext(_file)
					if not ext.lower() in ('.dpx','.wav'):
						result = False
						badFiles.append(filePath)
				else:
					pass

	# print(time.time())
	if badFiles == []:
		badFiles = None
	else:
		badFiles = (
			"You have the following files in your DPX folder that "
			"don't appear to belong:\n{}".format(' \n'.join(badFiles))
			)
	return result,badFiles

def check_complexity(inputPath,details):
	# by the time it gets here the structure and contents 
	# should be valid, so if there's any subdir other than dpx or documentation, 
	# we can assume that it is a multi-reel scan input
	if 'discrete' not in details:
		complexity = 'single reel dpx'
		for item in os.scandir(inputPath):
			if item.is_dir() and item.name.lower() not in ('dpx','documentation'):
				complexity = 'multi-reel dpx'
			else:
				pass
	else:
		complexity = details

	return complexity

def main(inputPath):
	'''
	Check whether the inputPath meets one of several possible configurations:
	- single discrete file with documentation
	- multiple discrete files
	- multiple discrete files with documentation
	- single reel dpx (and possible wav)
	- multi-reel dpx (and possible wavs)
	- a single dpx directory (the 'actual' dpx folder)
	'''
	badFiles = None
	result = None
	details = None
	# first look for the special case of a simple dpx input
	if os.path.basename(inputPath).lower() == 'dpx':
		is_dpx = pymmFunctions.is_dpx_sequence(inputPath)
		if is_dpx:
			result = 'dpx'
			details = None
		else:
			result = False
			details = ''
	else:
		result,details = scan_dir(inputPath)
	if not result:
		pass

	if details == 'documentation':
		# if there is only one thing in inputPath that isn't the 
		# documentation folder, then it is a single-file input.
		# if there are more than one file, we can assume it is 
		# a multiple discrete file input.
		if len([x for x in os.scandir(inputPath) if not x.is_dir()]) > 1:
			details = 'multiple discrete files'
		else:
			details = 'single discrete file'
	elif details != None:
		result,badFiles = check_for_bad_files(inputPath)

	print(result,details)

	if (result and details) and not badFiles:
		complexity = check_complexity(inputPath,details)
		details = complexity
	else:
		details = badFiles
	return result,details

if __name__ == "__main__":
	main()