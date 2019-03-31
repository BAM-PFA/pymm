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
		# path to optional JSON file of descriptive mentadata
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

class ComponentObject:
	'''
	Defines a single component of an InputObject.
	Can be a single file,
		an image sequence directory,
		or a folder of documentation.
	'''
	def __init__(self,inputPath,objectCategoryDetail=None):
		######
		# CORE ATTRIBUTES
		self.inputPath = inputPath
		self.basename = os.path.basename(inputPath)
		self.objectCategory = pymmFunctions.dir_or_file(inputPath)
		self.objectCategoryDetail = objectCategoryDetail

		self.databaseID = None
		self.objectIdentifierValue = self.basename

		self.isDocumentation = False
		if self.basename.lower() == 'documentation':
			self.isDocumentation = True
		if not self.isDocumentation or (self.objectCategoryDetail == 'Archival Information Package'):
			self.avStatus = pymmFunctions.is_av(inputPath)
		else:
			self.avStatus = None

		self.mediainfoPath = None
		self.md5hash = None

	def update_path(self,oldPath,newBasePath):
		newPath = oldPath.replace(
			os.path.dirname(oldPath),
			newBasePath
			)
		return newPath

class InputObject:
	'''
	Defines an object to be ingested.
	There should/can only be one object per ingestSip call.
	Can be simple (a single file), complex (a multi-reel DPX scan),
	or mixed (a/v material with supplementary documentation)
	'''
	def __init__(self,inputPath):
		######
		# CORE ATTRIBUTES
		self.inputPath = inputPath
		self.basename = os.path.basename(inputPath)
		self.filename = None
		# self.databaseID = None
		# self.objectIdentifierValue = self.basename

		self.outlierComponents = []
		self.inputType = self.sniff_input(inputPath)

		# Initialize a list to be filled with component objects. 
		# There should be at least one in the case of a single file input.
		# Objects should either be AV or a single documentation folder called 
		# 'documentation'
		self.ComponentObjects = []

		if self.inputType == 'dir':
			pymmFunctions.remove_hidden_system_files(inputPath)
			for item in os.listdir(self.inputPath):
				self.ComponentObjects.append(
					ComponentObject(
						os.path.join(inputPath,item)
						)
					)
		elif self.inputType == 'file':
			self.filename = self.basename
			self.ComponentObjects.insert(
				0,
				ComponentObject(inputPath)
				)

		# this is the "canonical name" of an object, either the 
		# filename of a single file or the dirname, which should
		# encompass the whole work/package being ingested.
		self.canonicalName = os.path.basename(self.inputPath)

		######
		# ASSIGNED / MUTABLE DURING PROCESSING
		self.pbcoreXML = pbcore.PBCoreDocument()
		self.pbcoreFile = None

		self.source_list = None

	def sniff_input(self,inputPath):
		'''
		Check whether the input path from command line is a directory
		or single file. 
		If it's a directory, check that the filenames
		make sense together or if there are any outliers.
		'''
		# returns 'dir' or 'file'
		inputType = pymmFunctions.dir_or_file(inputPath)
		if inputType == 'dir':
			# filename sanity check
			goodNames,badList = pymmFunctions.check_for_outliers(inputPath)
			if goodNames:
				print("input is a directory")
			else:
				if badList != None:
					for outlier in badList:
						self.outlierComponents.append(outlier)
		else:
			print("input is a single file")
		return inputType

class Ingest:
	'''
	An object representing the high-level aspects of a single ingest process.
	This includes information about the SIP like paths, high-level logging,
	  and contains attributes that get updated throughout the ingest process
	  to facilitate logging and file transfers.
	There are two classes (not *technically* subclasses) required as 
	  attributes of this class:
	  * ProcessArguments- defines the various CLI and environment details
	  * InputObject- one thing that is being ingested. 
	    * This object in turn must contain one or many ComponentObjects.
          These are the individual objects that are actually being ingested, 
          so they can be a single file, 
          or something like a WAV+DPX sequence folder.
	'''
	def __init__(self,ProcessArguments,InputObject):
		######
		# CORE ATTRIBUTES
		self.ingestUUID = str(uuid.uuid4())
		self.databaseID = None
		self.objectIdentifierValue = self.ingestUUID
		self.systemInfo = pymmFunctions.system_info() 

		# These objects must be fully initialized before getting passed here
		self.ProcessArguments = ProcessArguments
		self.InputObject = InputObject
		self.tempID = pymmFunctions.get_temp_id(self.InputObject.inputPath)

		######
		# SIP ATTRIBUTES
		self.packageOutputDir = None
		self.packageObjectDir = None
		self.packageMetadataDir = None
		self.packageMetadataObjects = None
		self.packageLogDir = None

		self.objectManifestPath = None

		self.includesSubmissionDocumentation = None


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
		self.currentMetadataDestination = None

	def prep_package(self,tempID,outdir_ingestsip):
		'''
		Create a directory structure for a SIP
		'''
		self.packageOutputDir = os.path.join(outdir_ingestsip,tempID)
		self.packageObjectDir = os.path.join(self.packageOutputDir,'objects')
		self.packageMetadataDir = os.path.join(self.packageOutputDir,'metadata')
		self.packageMetadataObjects = os.path.join(self.packageMetadataDir,'objects')
		self.packageLogDir = os.path.join(self.packageMetadataDir,'logs')
		self.packageDirs = [
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
			for directory in self.packageDirs:
				os.mkdir(directory)

		return True

	def create_ingestLog(self):
		self.ingestLogPath = os.path.join(
			self.packageLogDir,
			'{}_{}_ingestfile-log.txt'.format(
				self.tempID,
				pymmFunctions.timestamp('now')
				)
			)
		with open(self.ingestLogPath,'x') as ingestLog:
			print('Laying a log at '+self.ingestLogPath)

	def update_paths(self,target,replacement):
		'''
		Update some part of the main working paths for a SIP
		to include a new portion of a file path
		'''
		packageDirs = [
			self.packageOutputDir,
			self.packageObjectDir,
			self.packageMetadataDir,
			self.packageMetadataObjects,
			self.packageLogDir
		]
		for path in packageDirs:
			path = path.replace(target,replacement)
		