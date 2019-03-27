#!/usr/bin/env python3
'''
This is a WIP class to define an ingest. 
It should have these properties:
  - UUID
  - input path
  - ... uh, everything from the ingestLogBoilerplate and processingVars
  	dicts from the current ingestSip 
'''
# standard library modules
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
# local modules:
from bampfa_pbcore import pbcore, makePbcore
import concatFiles
import dbReporters
import makeDerivs
import moveNcopy
import makeMetadata
import pymmFunctions
import sequenceScanner

class ProcessArguments:
	"""Defines the variables and so on that exist during an ingest."""
	def __init__(
		self,
		user=None,
		objectJSON=None,
		databaseReporting=None,
		ingestType=None,
		makeProres=None,
		concatChoice=None,
		cleanupStrategy=None,
		overrideOutdir=None,
		overrideAIPdir=None,
		overrideRS=None,
		):
		#######
		# GLOBAL CONFIG (this is ConfigParser object, callable as a dict)
		self.config = pymmFunctions.read_config()

		#######
		# INPUT ARGUMENTS (FROM CLI)
		self.user = user
		self.objectJSON = objectJSON
		self.databaseReporting = databaseReporting
		self.ingestType = ingestType
		self.makeProres = makeProres
		self.concatChoice = concatChoice
		self.cleanupStrategy = cleanupStrategy

		if None in (overrideOutdir,overrideAIPdir,overrideRS):
			# if any of the outdirs is empty check for config settings
			pymmFunctions.check_missing_ingest_paths(self.config)
			self.aip_staging = self.config['paths']['aip_staging']
			self.resourcespace_deliver = self.config['paths']['resourcespace_deliver']
			self.outdir_ingestsip = self.config['paths']['outdir_ingestsip']
		else:
			self.aip_staging = overrideAIPdir
			self.resourcespace_deliver = overrideRS
			self.outdir_ingestsip = overrideOutdir

		self.databaseReporting = self.test_db_access(self.user)
		
		#######
		# ENVIRONMENT VARIABLES
		self.computer = pymmFunctions.get_node_name()
		self.ffmpegVersion = 'ffmpeg ver.: '+\
			pymmFunctions.get_ffmpeg_version()

	def test_db_access(self,user):
		if self.databaseReporting:
			if not user in self.config['database users']:
				print(
					"{} is not a valid user in the pymm database."
					"".format(user)
				)
				return False
			else:
				return True
		else:
			return False


class InputObject:
	"""Defines an object to be ingested"""
	def __init__(self,inputPath):
		######
		# CORE ATTRIBUTES
		self.inputPath = inputPath
		self.tempID = pymmFunctions.get_temp_id(inputPath)

		self.inputType = self.sniff_input(self.inputPath)

		# this is the "canonical name" of an object, either the 
		# filename of a single file or the dirname, which should
		# encompass the whole work/package being ingested.
		self.canonicalName = os.path.basename(self.inputPath)
		if self.inputType == 'file':
			self.filename = self.inputName = self.canonicalName
		elif self.inputType == 'dir':
			self.filename = ''
			self.inputName = self.canonicalName

		######
		# ASSIGNED / MUTABLE DURING PROCESSING
		self.componentObjectData = {}
		self.pbcoreXML = pbcore.PBCoreDocument()
		self.pbcoreFile = None

	def sniff_input(self,inputPath):
		'''
		Check whether the input path from command line is a directory
		or single file. 
		If it's a directory, check that the filenames
		make sense together or if there are any outliers.
		'''
		inputType = pymmFunctions.dir_or_file(inputPath)
		if inputType == 'dir':
			# filename sanity check
			goodNames = pymmFunctions.check_for_outliers(inputPath)
			if goodNames:
				print("input is a directory")
			else:
				return False
		
		else:
			print("input is a single file")
		return inputType

class Ingest:
	"""An object representing a single ingest process"""
	def __init__(self,ProcessArguments,InputObject):
		######
		# CORE ATTRIBUTES
		self.ingestUUID = str(uuid.uuid4())
		# These objects must be fully initialized before getting passed here
		self.ProcessArguments = ProcessArguments
		self.InputObject = InputObject
		self.systemInfo = pymmFunctions.system_info()

		######
		# SIP ATTRIBUTES
		self.packageOutputDir = None
		self.packageObjectDir = None
		self.packageMetadataDir = None
		self.packageMetadataObjects = None
		self.packageLogDir = None

		self.includesSubmissionDocumentation = None

		self.source_list = None

		######
		# LOGGING ATTRIBUTES
		self.ingestResults = {
			'status':False,
			'abortReason':'',
			'ingestUUID':self.ingestUUID
			}
		self.ingestLogPath = None
		

		######
		# VARIABLES ASSIGNED DURING PROCESSING
		self.caller = None
		self.currentTargetObject = None
		self.currentTargetObjectPath = None

	def prep_package(self,tempID,outdir_ingestsip):
		'''
		Create a directory structure for a SIP
		'''
		self.packageOutputDir = os.path.join(outdir_ingestsip,tempID)
		self.packageObjectDir = os.path.join(self.packageOutputDir,'objects')
		self.packageMetadataDir = os.path.join(self.packageOutputDir,'metadata')
		self.packageMetadataObjects = os.path.join(self.packageMetadataDir,'objects')
		self.packageLogDir = os.path.join(self.packageMetadataDir,'logs')
		packageDirs = [
			self.packageOutputDir,
			self.packageObjectDir,
			self.packageMetadataDir,
			self.packageMetadataObjects,
			self.packageLogDir
		]
		
		# ... SEE IF THE TOP DIR EXISTS ...
		if os.path.isdir(self.packageOutputDir):
			print("It looks like {} was already ingested. "\
				"If you want to replace the existing package "\
				"please delete the package at\n{}\nand then try again."\
				"".format(self.InputObject.canonicalName,self.packageOutputDir))
			self.ingestResults['abortReason'] = "package previously ingested, remove manually"
			return False

		# ... AND IF NOT, MAKE THEM ALL
		else:
			for directory in packageDirs:
				os.mkdir(directory)

		return True

	def create_ingestLog(self):
		self.ingestLogPath = os.path.join(
			self.packageLogDir,
			'{}_{}_ingestfile-log.txt'.format(
				self.InputObject.tempID,
				pymmFunctions.timestamp('now')
				)
			)
		with open(self.ingestLogPath,'x') as ingestLog:
			print('Laying a log at '+self.ingestLogPath)




		