#!/usr/bin/env python3
# Python standard library modules
import argparse
import os
import sys
# non-standard libraries
from lxml import etree
# local modules
import dbReporters
'''
This is intended to parse an LTFS index.schema XML file in order to 
list the contents of the tape in the pymm database. 

The basics of this (the content we're looking for) is taken from `mm`
but as of (8/2018) I am going to skip over access files, logs, 
and stuff other than master files. 

The XPATH used here is specific to the AIP structure that we are using. 
It would need to be altered to account for any different structure.

Also, I don't want to index each file in a DPX sequence, but rather 
index the 'canonical name' of the object as a single unit and reference its
length in terms of number of files in the sequence. I think.
'''

def set_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-l','--ltoSchemaPath',
		required=True,
		help='path to input schema file'
		)
	parser.add_argument(
		'-u','--user',
		help='user (must be a valid PYMM DB user)'
		)

	return parser.parse_args()

def parse_it(ltoSchemaPath):
	contents = {'ltoID':'','objects':{}}
	# this XPATH expression gets the files that are direct children
	# of the `objects` directory in the AIP. i.e., just the master files
	xpathMasters = '//directory[name="objects" and ../../name!="metadata"]/contents/file/name'
	# this gets the directory names above each file
	# we can get this b/c the actual etree Element node is returned
	# (not just the filename string)
	xpathFilepath = 'ancestor-or-self::directory/name/text()'
	# this gets the filesize in bytes
	xpathFilesize = '../length/text()'
	# this gets the modified time
	xpathModifyTime = '../modifytime/text()'
	xpathLTOid = '/ltfsindex/directory/name/text()'

	tree = etree.parse(ltoSchemaPath)
	contents['ltoID'] = str(tree.xpath(xpathLTOid)[0])
	files = tree.xpath(xpathMasters)
	for item in files:
		filename = str(item.text)
		# init a subdict for each item
		contents['objects'][filename] = {}
		contents['objects'][filename]['path'] = str('/'.join(item.xpath(xpathFilepath)))
		contents['objects'][filename]['size'] = str(item.xpath(xpathFilesize)[0])
		contents['objects'][filename]['modified'] = str(item.xpath(xpathModifyTime)[0])

	return contents

def main():
	args = set_args()
	ltoSchemaPath = args.ltoSchemaPath
	user = args.user


	contents = parse_it(ltoSchemaPath)
	print(contents)
	for k,v in contents.items():
		print(v)
		print(type(v))

	if user:
		report = dbReporters.ReportLTFS(
			user,
			contents
			)
		report.report_to_db()
		del report

	return contents

if __name__ == '__main__':
	main()