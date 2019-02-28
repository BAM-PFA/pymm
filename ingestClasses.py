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
		operator,
		objectJSON,
		databaseReporting,
		ingestType,
		makeProres,
		concatChoice,
		cleanupStrategy,
		overrideOutdir,
		overrideAIPdir,
		overrideRS,
		):
		# INPUT ARGUMENTS (FROM CLI)
		self.operator = operator
		self.objectJSON = objectJSON
		self.databaseReporting = databaseReporting
		self.ingestType = ingestType
		self.makeProres = makeProres
		self.concatChoice = concatChoice
		self.cleanupStrategy = cleanupStrategy
		self.overrideOutdir = overrideOutdir
		self.overrideAIPdir = overrideAIPdir
		self.overrideRS = overrideRS

		if None in (self.overrideOutdir,self.overrideAIPdir,self.overrideRS):
			# if any of the outdirs is empty check for config settings
			pymmFunctions.check_missing_ingest_paths(self.config)
			self.aip_staging = self.config['paths']['aip_staging']
			self.resourcespace_deliver = self.config['paths']['resourcespace_deliver']
			self.outdir_ingestsip = config['paths']['outdir_ingestsip']
		else:
			self.aip_staging = self.overrideAIPdir
			self.resourcespace_deliver = self.overrideRS
			self.outdir_ingestsip = self.overrideOutdir

		# GLOBAL CONFIG (this is ConfigParser object, callable as a dict)
		self.config = pymmFunctions.read_config()

		# ENVIRONMENT VARIABLES
		self.computer = pymmFunctions.get_node_name()
		self.ffmpegVersion = 'ffmpeg ver.: '+\
			pymmFunctions.get_ffmpeg_version()

class InputObject:
	"""Defines an object to be ingested"""
	def __init__(self,inputPath):
		# CORE ATTRIBUTES
		self.inputPath = inputPath
		self.tempID = pymmFunctions.get_temp_id(inputPath)

		self.inputType = self.sniff_input(self.inputPath)
		self.canonicalName = os.path.basename(self.inputPath)
		if self.inputType == 'file':
			self.filename = self.inputName = self.canonicalName
		elif self.inputType == 'dir':
			self.filename = ''
			self.inputName = canonicalName

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
	def __init__(self):
		# # CORE ATTRIBUTES
		# self.inputPath = inputPath
		self.ingestUUID = str(uuid.uuid4())

		# LOGGING ATTRIBUTES
		self.ingestResults = {
			'status':False,
			'abortReason':'',
			'ingestUUID':self.ingestUUID
			}

		# ATTRIBUTES DEPENDENT UPON PROCESSING ARGUMENTS
		#   these will get defined after ProcessArguments is instantiated
		#
		# This will later be a ProcessArguments obj
		self.processingArgs = None 

		self.packageOutputDir = None
		self.packageObjectDir = None
		self.packageMetadataDir = None
		self.packageMetadataObjects = None
		self.packageLogDir = None

		# ATTRIBUTES DEPENDENT UPON THE INGESTED OBJECT
		#   These will get defined once the Object exists







		