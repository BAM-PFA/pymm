#!/usr/bin/env python3
import os
from pathlib import Path
import sys
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
	# system files should already be removed by the time it's called but...
	pymmFunctions.remove_hidden_system_files(inputPath)
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

def check_formats(inputPath):
	'''
	This function is insane and duplicates efforts in pymmFunctions.
	What is it even trying to accomplish?
	@fixme
	'''
	badFiles = []
	result = True
	for root, dirs, files in os.walk(inputPath):
		for _file in files:
			if not _file.startswith('.'):
				filePath = os.path.join(root,_file)
				_,ext = os.path.splitext(_file)
				parentDir = Path(filePath).resolve().parent
				parentDir = os.path.basename(str(parentDir))
				if not ext.lower() in ('.dpx','.wav'):
					if not parentDir.lower() == 'documentation':
						result = False
						badFiles.append(filePath)

	return result,badFiles

def check_complexity(inputPath,details):
	# by the time it gets here the structure and contents 
	# should be valid, so if there's any subdir other than dpx, 
	# we can assume that it is a multi-reel scan input

	# NO LONGER TRUE, @fixme
	if 'discrete' not in details:
		complexity = 'single reel dpx'
		for item in os.scandir(inputPath):
			if item.is_dir() and item.name.lower() != 'dpx':
				complexity = 'multi-reel dpx'
			else:
				pass
	else:
		complexity = details

	return complexity

def main(inputPath):
	result,details = scan_dir(inputPath)
	if not result:
		pass

	else:
		if details == 'documentation':
			details = 'discrete file(s) with documentation'
			pass
		else:
			result,details = check_formats(inputPath)
	print(result,details)

	if result == True:
		complexity = check_complexity(inputPath,details)
		details = complexity
	return result,details

if __name__ == "__main__":
	main()