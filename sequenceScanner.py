#!/usr/bin/env python3
import os
import sys

import pymmFunctions

# inputPath = sys.argv[1]

def scan_dir(inputPath):
	'''
	expected image sequence dir structure:
	- title_accesssion#_barcode_r01of01/
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
					print("removing empty dir at "+path)
					os.rmdir(path)
	# start looking for inappropriate/unrecorgnized folders
	problems = []
	dirs = []
	outcome = None
	for entry in os.scandir(inputPath):
		# cast the fiery circle,
		# summon all the subdirectories for judgement before my wrath
		if entry.is_dir():
			dirs.append(entry.path)
	if len(dirs) > 0:
		if (len(dirs) == 1) and (os.path.basename(dirs[0]).lower() != 'dpx'):
			# if there is only one subdir and it isn't DPX, shit it out
			problems = dirs
			return False,problems

		elif len(dirs) > 1:
			baddies = []
			for _dir in dirs:
				for root,subs,_ in os.walk(_dir):
					# grab any non-dpx dirs to return
					things = [os.path.join(root,sub) for sub in subs if sub.lower() != 'dpx']
					for thing in things:
						baddies.append(thing)
			if baddies != []:
				# there shouldn't be anything other than dpx folders at this level
				outcome = False
				for baddie in baddies:
					problems.append(baddie)
			else:
				print("DPX dirs are ok")
				outcome = True
		else:
			outcome = True

	return outcome,problems

def check_formats(inputPath):
	badFiles = []
	result = True
	for root, dirs, files in os.walk(inputPath):
		for _file in files:
			if not _file.startswith('.'):
				# print(_file)
				filePath = os.path.abspath(_file)
				_,ext = os.path.splitext(_file)
				if not ext.lower() in ('.dpx','.wav'):
					result = False
					badFiles.append(os.path.join(root,_file))

	return result,badFiles

def check_complexity(inputPath):
	# by the time it gets here the structure and contents 
	# should be valid, so if there's any subdir other than dpx, 
	# we can assume that it is a multi-reel scan input
	complexity = 'single reel dpx'
	for item in os.scandir(inputPath):
		if item.is_dir() and item.name.lower() != 'dpx':
			complexity = 'multi-reel dpx'
		else:
			pass

	return complexity

def main(inputPath):
	result,details = scan_dir(inputPath)
	if not result:
		pass

	else:
		result,details = check_formats(inputPath)
	print(result,details)

	if result == True:
		complexity = check_complexity(inputPath)
		details = complexity
	return result,details

if __name__ == "__main__":
	main()