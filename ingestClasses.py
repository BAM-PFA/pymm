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

		# read in from the config file
		self.config = pymmFunctions.read_config()


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



class InputObject:
	"""Defines an object to be ingested"""
	def __init__(self,inputPath):
		self.inputPath = inputPath		

class Ingest:
	"""An object representing a single ingest process"""
	def __init__(self, inputPath):
		# CORE ATTRIBUTES
		self.inputPath = inputPath
		self.ingestUUID = str(uuid.uuid4())


		# LOGGING ATTRIBUTES
		self.ingestResults = {
			'status':False,
			'abortReason':'',
			'ingestUUID':self.ingestUUID
			}


		