#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
# local modules:
import moveNcopy
import pymmFunctions


'''
WIP JUNK FOR WORKING WITH BEXT METADATA IN BWF FILES
'''

# def set_args():
# 	parser = argparse.ArgumentParser()
# 	parser.add_argument(
# 		'-i','--inputPath',
# 		help='path of input file',
# 		required=True
# 		)
# 	parser.add_argument(
# 		'-a','--make_access',
# 		help="make an access copy while we're here",
# 		action="store_true"
# 		)
# 	parser.add_argument(
# 		'-j','--metadataJSON',
# 		help='full path to a JSON file containing descriptive metadata'
# 		)
# 	parser.add_argument(
# 		'-t','--ingestType',
# 		choices=['film scan','video transfer'],
# 		default='video transfer',
# 		help='type of file(s) being ingested: film scan, video xfer'
# 		)



def check_for_bext(inputPath):
	'''
	If there is nothing in the Originator field 
	we will assume that there is no BEXT data.
	'''
	command = ['bwfmetaedit','--out-core',inputPath]
	out = subprocess.run(command,stdout=subprocess.PIPE)
	# print(out.stdout.decode())
	data = out.stdout.decode().split('\r')[1]
	# print(data)
	originator = data.split(',')[2]
	# print(originator)
	if originator in ('',' ',None):
		hasBext = False
	else:
		hasBext = True

	return hasBext

def set_bexit_chunk(inputPath):
	command = [
	''
	]

