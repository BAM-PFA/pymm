#!/usr/bin/env python3
'''
`ingestSip` takes an input a/v file or directory of a/v files,
transcodes a derivative for each file,
produces/extracts some metadata,
creates fixity checks,
and packages the whole lot in an OAIS-like Archival Information Package

@fixme = stuff to do
@logme = stuff to add to ingest log
@dbme = stuff to add to PREMIS db
'''
# standard library modules
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
# local modules:
try:
	from bampfa_pbcore import pbcore, makePbcore
	import concatFiles
	import dbReporters
	import ingestClasses
	import loggers
	import makeDerivs
	import moveNcopy
	import makeMetadata
	import pymmFunctions
	import sequenceScanner
except:
	from . bampfa_pbcore import pbcore, makePbcore
	from . import concatFiles
	from . import dbReporters
	from . import ingestClasses
	from . import loggers
	from . import makeDerivs
	from . import moveNcopy
	from . import makeMetadata
	from . import pymmFunctions
	from . import sequenceScanner 
# read in from the config file
config = pymmFunctions.read_config()

def set_args():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i','--inputPath',
		help='path of input file',
		required=True
		)
	parser.add_argument(
		'-u','--user',
		help='name of the person doing the ingest',
		required=True
		)
	parser.add_argument(
		'-j','--metadataJSON',
		help='full path to a JSON file containing descriptive metadata'
		)
	parser.add_argument(
		'-t','--ingestType',
		choices=['film scan','video transfer','audio xfer'],
		default='video transfer',
		help='type of file(s) being ingested: film scan, video xfer'
		)
	parser.add_argument(
		'-p','--makeProres',
		action='store_true',
		help='override whatever config default you have set '
			'and make a prores HQ mezzanine file'
		)
	parser.add_argument(
		'-c','--concatAccessFiles',
		action='store_true',
		help='try to concatenate access files after ingest'
		)
	parser.add_argument(
		'-d','--databaseReporting',
		action='store_true',
		default=False,
		help='report preservation metadata/events to database'
		)
	parser.add_argument(
		'-z','--cleanup_originals',
		action='store_true',
		default=False,
		help='set this flag to delete source files after ingest'
		)
	parser.add_argument(
		'-a','--aip_staging',
		help=(
			'enter a full directory path to override path set in config; '
			'sets directory for staging AIP after ingest\n\n'
			'PRO TIP: for testing, leave this blank or use the same dir as -o'
			)
		)
	parser.add_argument(
		'-o','--outdir_ingestsip',
		help=(
			'enter a full directory path to override path set in config; '
			'sets output directory for ingestSip.py'
			)
		)
	parser.add_argument(
		'-r','--resourcespace_deliver',
		help=(
			'enter a full directory path to override path set in config; '
			'sets output directory for ingestSip.py'
			)
		)

	return parser.parse_args()

def concat_access_files(CurrentIngest,wrapper):
	inputPath = CurrentIngest.accessPath
	sys.argv = [
		'',
		'-i'+inputPath,
		'-d'+CurrentIngest.ingestUUID,
		'-c'+CurrentIngest.canonicalName,
		'-w'+wrapper
		]
	success = False
	concattedAccessFile,success = concatFiles.main()

	origFilename = processingVars['filename']
	if not success == False:
		concatObject = ingestClasses.ComponentObject(concattedAccessFile)
		CurrentIngest.InputObject.ComponentObjects.append(concatObject)
		CurrentIngest.currentTargetObject = concatObject
		outcome = (
			"Component files concatenated "
			"into an access copy at {}".format(concattedAccessFile)
			)
		status = "OK"

		# set the 'filenaeme' to the concat file so we can log in the db
		loggers.insert_object(
			CurrentIngest,
			objectCategory='file',
			objectCategoryDetail='concatenated access file'
			)
	else:
		status = "FAIL"
		outcome = (
			"Component files could not be concatenated. "
			"Probably you need to check the file specs? "
			"Here's the output of the attempt:\n{}\n"
			"".format(concattedAccessFile)
			)
	CurrentIngest.caller = CurrentIngest.ProcessArguments.ffmpegVersion
	loggers.log_event(
		CurrentIngest,
		event='creation',
		outcome=outcome,
		status=status
		)
	CurrentIngest.caller = None
	CurrentIngest.currentTargetObject = None

	return concattedAccessFile

def deliver_concat_access(concatPath,accessPath):
	try:
		shutil.copy2(concatPath,accessPath)
		return True
	except:
		print('couldnt deliver the concat file')
		return False

def check_av_status(CurrentIngest):
	'''
	Check whether or not a file is recognized as an a/v object.
	'''
	avStatus = False
	event = 'format identification'
	CurrentIngest.caller = 'pymmFunctions.is_av()'
	AV = pymmFunctions.is_av(CurrentIngest.currentTargetObject)
	if not AV:
		outcome = "WARNING: {} is not recognized as an a/v object.".format(
			CurrentIngest.currentTargetObject
			)
		status = "WARNING"
		print(outcome)

	else:
		outcome = "{} is a(n) {} object, way to go.".format(
			CurrentIngest.currentTargetObject.inputPath,
			AV
			)
		status = "OK"
		avStatus = True
	loggers.log_event(
		CurrentIngest,
		event,
		outcome,
		status
		)
	return avStatus, AV

def mediaconch_check(inputPath,ingestType,ingestLogBoilerplate):
	'''
	Check input file against MediaConch policy.
	Needs to be cleaned up. Move logic to pymmFunctions and keep logging here.
	Also, we don't have any policies set up yet...
	'''
	if ingestType == 'film scan':
		policyStatus = pymmFunctions.check_policy(ingestType,inputPath)
		if policyStatus:
			message = filename+" passed the MediaConch policy check."
			status = "ok"
		else:
			message = filename+" did not pass the MediaConch policy check."
			status = "not ok, but not critical?"

		pymmFunctions.ingest_log(
			message,
			status,
			**ingestLogBoilerplate
			)

def update_input_path(CurrentIngest):
	'''
	change the current object's input path to reflect the object in the SIP
	rather than its source in the input object
	'''
	objectDir = CurrentIngest.packageObjectDir
	inputDirPath = os.path.dirname(CurrentIngest.currentTargetObject.inputPath)
	CurrentIngest.currentTargetObject.inputPath.replace(inputDirPath,objectDir)

	return True


def move_component_object(CurrentIngest):
	'''
	Put the current component object into the package object folder
	'''
	currentTargetObject = CurrentIngest.currentTargetObject
	status = 'OK'
	if currentTargetObject.topLevelObject == True:
		objectDir = CurrentIngest.packageObjectDir
		sys.argv = [
			'',
			'-i'+currentTargetObject.inputPath,
			'-d'+objectDir,
			'-L'+CurrentIngest.packageLogDir,
			'-m'
			]

		event = 'replication'
		outcome = 'migrate object to SIP at {}'.format(objectDir)
		CurrentIngest.caller = 'rsync'
		try:
			moveNcopy.main()
			status = 'OK'
			currentTargetObject.inputPath = currentTargetObject.update_path(
				currentTargetObject.inputPath,
				objectDir
				)
		except:
			status = 'FAIL'
		loggers.log_event(
			CurrentIngest,
			event,
			outcome,
			status
			)
		CurrentIngest.caller = None
	if not status == 'FAIL':
		update_input_path(CurrentIngest)

	return True

def get_file_metadata(CurrentIngest,_type=None):
	inputPath = CurrentIngest.currentTargetObject.inputPath
	basename = os.path.basename(inputPath)

	mediainfoPath = makeMetadata.get_mediainfo_report(
		inputPath,
		CurrentIngest.currentMetadataDestination,
		_JSON=None,
		altFileName=basename
		)
	if os.path.isfile(mediainfoPath):
		event = 'metadata extraction'
		outcome = ("mediainfo XML report for input file "
			"written to metadata directory for package.")
		CurrentIngest.caller = '`mediainfo --Output=XML`'
		loggers.short_log(
			CurrentIngest,
			event,
			outcome,
			status='OK'
			)
		CurrentIngest.caller = None
		CurrentIngest.currentTargetObject.mediainfoPath = mediainfoPath
	
	if not _type == 'derivative':
	# don't bother calculating frame md5 for derivs....
		frameMD5 = makeMetadata.make_frame_md5(
			inputPath,
			CurrentIngest.packageMetadataObjects
			)
		if frameMD5 != False:
			event = 'message digest calculation'
			outcome = ("frameMD5 report for input file "
				"written to metadata directory for package")
			CurrentIngest.caller = \
				CurrentIngest.ProcessArguments.ffmpegVersion\
				+' with option `-f frameMD5`'
			loggers.short_log(
				CurrentIngest,
				event,
				outcome,
				status='OK'
				)
			CurrentIngest.caller = None

	return mediainfoPath

def add_pbcore_md5_location(CurrentIngest):
	'''
	have to call this after creation of object manifest for SIP
	and parsing of manifest by report_SIP_fixity()
	'''
	if CurrentIngest.InputObject.pbcoreFile != '':
		pbcoreFile = CurrentIngest.InputObject.pbcoreFile
		pbcoreXML = pbcore.PBCoreDocument(pbcoreFile)		
		for _object in CurrentIngest.InputObject.ComponentObjects:
			# look for component files and add instantiation data
			if _object.objectCategory == 'file':
				# add md5 as an identifier to the 
				# pbcoreInstantiation for the file
				# processingVars['filename'] = _object
				inputFileMD5 = _object.md5hash
				attributes = {
					"source":"BAMPFA {}".format(
						pymmFunctions.timestamp('iso8601')
						),
					"annotation":"messageDigest",
					"version":"MD5"
				}
				makePbcore.add_element_to_instantiation(
					pbcoreXML,
					_object.basename,
					'instantiationIdentifier',
					attributes,
					inputFileMD5
					)
				# add 'BAMPFA Digital Repository' as instantiationLocation
				attributes = {}
				makePbcore.add_element_to_instantiation(
					pbcoreXML,
					_object.basename,
					'instantiationLocation',
					attributes,
					"BAMPFA Digital Repository"
					)
		makePbcore.xml_to_file(
			pbcoreXML,
			pbcoreFile
			)

def add_pbcore_instantiation(CurrentIngest,level):
	'''
	Get a PBCore XML string about a single ComponentObject 
	from `mediainfo` and add it as an instantiation to the main 
	PBCore document for the InputObject.
	'''
	_file = CurrentIngest.currentTargetObject
	if _file.avStatus in ('DPX','TIFF'):
		_,_,file0 = pymmFunctions.parse_sequence_folder(_file.inputPath)
		pbcoreReport = makeMetadata.get_mediainfo_pbcore(file0)
	elif _file.avStatus in ('VIDEO','AUDIO'):
		pbcoreReport = makeMetadata.get_mediainfo_pbcore(_file.inputPath)

	# descriptiveJSONpath = CurrentIngest.ProcessArguments.objectJSON
	# print(pbcoreReport)
	pbcoreFilePath = CurrentIngest.InputObject.pbcoreFile
	pbcoreXML = pbcore.PBCoreDocument(pbcoreFilePath)

	event = 'metadata modification'
	outcome = 'add pbcore instantiation representation'
	CurrentIngest.caller = 'makePbcore.add_instantiation()'
	try:
		status = 'OK'
		makePbcore.add_instantiation(
			pbcoreXML,
			pbcoreReport,
			descriptiveJSONpath=None,
			level=level
			)
		makePbcore.xml_to_file(pbcoreXML,pbcoreFilePath)

	except:
		outcome = 'could not '+outcome
		status = 'FAIL'

	loggers.short_log(
		CurrentIngest,
		event,
		outcome,
		status
		)
	# reset 'caller'
	CurrentIngest.caller = None

	return True

def make_rs_package(inputObject,resourcespace_deliver):
	'''
	If the ingest input is a dir of files, put all the `*_access` files
	into a folder named for the object
	'''
	rsPackageDelivery = None
	try:
		_object = os.path.basename(inputObject)
		rsPackageDelivery = os.path.join(resourcespace_deliver,_object)

		if not os.path.isdir(rsPackageDelivery):
			try:
				os.mkdir(rsPackageDelivery)
				# add a trailing slash for rsync
				rsPackageDelivery = os.path.join(rsPackageDelivery,'')
				# print(rsPackageDelivery)
			except OSError as e:
				print("OOPS: {}".format(e))
	except:
		pass
	else:
		pass

	return rsPackageDelivery

def make_derivs(CurrentIngest,rsPackage=None,isSequence=None):
	'''
	Make derivatives based on options declared in config...
	'''
	initialObject = CurrentIngest.currentTargetObject
	inputPath = initialObject.inputPath
	packageObjectDir = CurrentIngest.packageObjectDir
	packageLogDir = CurrentIngest.packageLogDir
	packageMetadataObjects = CurrentIngest.packageMetadataObjects
	makeProres = CurrentIngest.ProcessArguments.makeProres
	ingestType = CurrentIngest.ProcessArguments.ingestType
	resourcespace_deliver = CurrentIngest.ProcessArguments.resourcespace_deliver

	# make an enclosing folder for access copies if the input is a
	# group of related video files
	if rsPackage != None:
		rsPackageDelivery = make_rs_package(
			CurrentIngest.InputObject.canonicalName,
			resourcespace_deliver
			)
	else:
		rsPackageDelivery = None

	# we'll always output a resourcespace access file for video ingests,
	# so init the derivtypes list with `resourcespace`
	if ingestType in ('film scan','video transfer','audio xfer'):
		derivTypes = ['resourcespace']
	
	# deliveredDerivPaths is a dict as follows:
	# {derivtype1:/path/to/deriv/file1}
	deliveredDerivPaths = {}
	
	if pymmFunctions.boolean_answer(
		config['deriv delivery options']['proresHQ']
		):
		derivTypes.append('proresHQ')
	elif makeProres == True:
		derivTypes.append('proresHQ')
	else:
		pass

	for derivType in derivTypes:
		sysargs = ['',
					'-i'+inputPath,
					'-o'+packageObjectDir,
					'-d'+derivType,
					'-L'+packageLogDir
					]
		if rsPackageDelivery != None:
			sysargs.append('-r'+rsPackageDelivery)
		if isSequence:
			sysargs.append('-s')
		sys.argv = 	sysargs
		
		deliveredDeriv = makeDerivs.main()
		deliveredDerivPaths[derivType] = deliveredDeriv

		event = 'migration'
		CurrentIngest.caller = CurrentIngest.ProcessArguments.ffmpegVersion
		if pymmFunctions.is_av(deliveredDeriv):
			outcome = 'create access copy at {}'.format(deliveredDeriv)
			status = 'OK'
		else:
			outcome = 'could not create access copy'
			status = 'FAIL'
		loggers.log_event(
			CurrentIngest,
			event,
			outcome,
			status
			)
		CurrentIngest.caller = None

	for key,value in deliveredDerivPaths.items():
		# metadata for each deriv is stored in a folder named
		# for the derivtype under the main Metadata folder
		mdDest = os.path.join(packageMetadataObjects,key)
		CurrentIngest.currentMetadataDestination = mdDest
		if not os.path.isdir(mdDest):
			os.mkdir(mdDest)

		if os.path.isfile(value):
			# if the new access file exists, 
			# create it as a ComponentObject object and
			# add it to the list in InputObject
			newObject = ingestClasses.ComponentObject(
				value,
				
				)
			CurrentIngest.InputObject.ComponentObjects.append(newObject)
			CurrentIngest.currentTargetObject = newObject

			loggers.insert_object(
				CurrentIngest,
				objectCategory='file',
				objectCategoryDetail='access file'
				)
			get_file_metadata(
				CurrentIngest,
				_type='derivative'
				)
		else:
			pass

		CurrentIngest.currentMetadataDestination = None

		if CurrentIngest.InputObject.pbcoreFile not in ('',None):
			if derivType in ('resourcespace'):
				level = 'Access copy'
			elif derivType in ('proresHQ'):
				level = 'Mezzanine'
			else:
				level = 'Derivative'

			add_pbcore_instantiation(
				CurrentIngest,
				level
				)

	# get a return value that is the path to the access copy(ies) delivered
	#   to a destination defined in config.ini
	# * for a single file it's the single deriv path
	# * for a folder of files it's the path to the enclosing deriv folder
	# 
	# this path is used to make an API call to resourcespace
	if rsPackageDelivery not in ('',None):
		accessPath = rsPackageDelivery
	else:
		SIPaccessPath = deliveredDerivPaths['resourcespace']
		deliveredAccessBase = os.path.basename(SIPaccessPath)
		accessPath = os.path.join(resourcespace_deliver,deliveredAccessBase)

	return accessPath

def stage_sip(CurrentIngest):
	'''
	Move a prepped SIP to the AIP staging area.
	'''
	packageOutputDir = CurrentIngest.packageOutputDir
	aip_staging = CurrentIngest.ProcessArguments.aip_staging
	# tempID = processingVars['tempID']
	ingestUUID = CurrentIngest.ingestUUID
	sys.argv = 	['',
				'-i'+packageOutputDir,
				'-d'+aip_staging,
				'-L'+os.path.join(aip_staging,ingestUUID,ingestUUID,'metadata','logs')]
	moveNcopy.main()

	# rename the staged dir
	stagedSIP = os.path.join(aip_staging,ingestUUID)
	# UUIDpath = os.path.join(aip_staging,ingestUUID)
	# pymmFunctions.rename_dir(stagedSIP,UUIDpath)
	CurrentIngest.caller = 'rsync'
	pymmFunctions.short_log(
		CurrentIngest,
		event = 'replication',
		outcome = 'SIP moved to staging area at {}'.format(stagedSIP),
		status = "OK"
		)
	CurrentIngest.caller = None

	return stagedSIP

def uuid_logfile(CurrentIngest):
	'''
	rename the ingest log w the UUID
	'''
	logpath = CurrentIngest.ingestLogPath
	logbase = os.path.basename(logpath)
	tempID = CurrentIngest.tempID
	_uuid = CurrentIngest.ingestUUID
	newbase = logbase.replace(tempID,_uuid)
	newpath = logpath.replace(logbase,newbase)
	os.rename(logpath,newpath)

	CurrentIngest.ingestLogPath = newpath

	return True

def update_tempID(CurrentIngest,tempID,ingestUUID):
	'''
	replace filepath instances of temp ID with UUID
	'''
	CurrentIngest.update_paths(tempID,ingestUUID)

	for component in CurrentIngest.InputObject.ComponentObjects:
		try:
			component.mediainfoPath = component.mediainfoPath.replace(
				tempID,
				ingestUUID
				)
		except:
			pass

	return True

def rename_SIP(CurrentIngest):
	'''
	Rename the directory to the ingest UUID.
	'''
	pymmOutDir = CurrentIngest.ProcessArguments.outdir_ingestsip
	packageOutputDir = CurrentIngest.packageOutputDir
	ingestUUID = CurrentIngest.ingestUUID
	tempID = CurrentIngest.tempID
	UUIDpath = os.path.join(pymmOutDir,ingestUUID)

	# update the existing filepaths
	update_tempID(CurrentIngest,tempID,ingestUUID)
	# now rename the SIP dir
	pymmFunctions.rename_dir(packageOutputDir,UUIDpath)
	# now update the log filepath
	CurrentIngest.update_logfile(tempID,ingestUUID)

	event = 'filename change'
	outcome = 'SIP renamed from {} to {}.'.format(
		packageOutputDir,
		UUIDpath
		)
	status = 'OK'
	CurrentIngest.caller = 'pymmFunctions.rename_dir()'
	loggers.short_log(
		CurrentIngest,
		event,
		outcome,
		status
		)
	CurrentIngest.caller = None

	return UUIDpath

def update_enveloped_paths(CurrentIngest):
	'''
	update stored paths to reflect enveloped SIP structure
	'''
	_uuid = CurrentIngest.ingestUUID
	UUIDpath = CurrentIngest.packageOutputDir
	envelopedPath = os.path.join(UUIDpath,_uuid)

	CurrentIngest.update_paths(UUIDpath,envelopedPath)
	# print(CurrentIngest.packageDirs)
	CurrentIngest.ingestLogPath = os.path.join(
		CurrentIngest.packageLogDir,
		os.path.basename(CurrentIngest.ingestLogPath)
		)
	CurrentIngest.InputObject.pbcoreFile = os.path.join(
		CurrentIngest.packageMetadataDir,
		os.path.basename(CurrentIngest.InputObject.pbcoreFile)
		)

	for component in CurrentIngest.InputObject.ComponentObjects:
		try:
			component.mediainfoPath = component.mediainfoPath.replace(
				UUIDpath,
				envelopedPath
				)
		except:
			pass

	if os.path.isfile(CurrentIngest.ingestLogPath):
		pass
	else:
		print("OOOOO HHHHHH NNNN OOOOO")

	return True

def envelop_SIP(CurrentIngest):
	'''
	Make a parent directory named w UUID to facilitate hashdeeping/logging.
	Update the ingest log to reflect the new path.
	'''
	ingestUUID = CurrentIngest.ingestUUID
	UUIDslice = ingestUUID[:8]
	pymmOutDir = CurrentIngest.ProcessArguments.outdir_ingestsip
	_SIP = CurrentIngest.packageOutputDir
	event = 'faux-bag'
	outcome = (
		'Make a parent directory named w UUID '
		'to facilitate hash manifest/auditing.'
		)
	CurrentIngest.caller = 'ingestSIP.envelop_SIP()'

	print(CurrentIngest.packageDirs)

	try:
		status = "OK"
		parentSlice = os.path.join(pymmOutDir,UUIDslice)
		# make a temp parent folder...
		os.mkdir(parentSlice)
		# ...move the SIP into it...
		shutil.move(_SIP,parentSlice)
		# ...and rename the parent w UUID path...
		pymmFunctions.rename_dir(parentSlice,_SIP)
		# ... now update all the file paths again
		update_enveloped_paths(CurrentIngest)
	except:
		status = "FAIL"
		print("Something no bueno.")

	loggers.short_log(
		CurrentIngest,
		event,
		outcome,
		status
		)
	CurrentIngest.caller = None

	return True

def do_cleanup(
	CurrentIngest,
	packageVerified,
	reason
	):
	if CurrentIngest.ProcessArguments.cleanupStrategy == True:
		if packageVerified == True:
			print("Things seem copacetic so let's remove the originals.")
			pymmFunctions.cleanup_package(
				CurrentIngest,
				CurrentIngest.InputObject.inputPath,
				reason
				)
	else:
		print("Ending, quitting, bye bye.")

def directory_precheck(CurrentIngest):
	'''
	Do some checking on directories:
	- remove system files
	- check for subdirectories
	'''
	precheckPass = (True,'')
	inputPath = CurrentIngest.InputObject.inputPath

	####################################
	### HUNT FOR HIDDEN SYSTEM FILES ###
	### DESTROY!! DESTROY!! DESTROY! ###
	removedFiles = pymmFunctions.remove_hidden_system_files(
		inputPath
		)
	
	removeFailures = []
	status = "OK"
	event = "deletion"
	# check again for system files... just in case.
	for _object in CurrentIngest.InputObject.source_list:
		if os.path.basename(_object).startswith('.'):
			try:
				removedFiles.append(_object)
				os.remove(_object)
			except:
				removeFailures.append(_object)
				print("tried to remove a pesky system file and failed.")
	
	if not removeFailures == []:
		if not removedFiles == []: 
			outcome = ("System files deleted at \n{}\n"
				"Some additional system files were NOT removed "
				"at \n{}\n".format(
					"\n".join(removedFiles),
					"\n".join(removeFailures)
					)
				)
			status == "INCONCLUSIVE"
		else:
			# if both passes failed, log it as such
			outcome = "Tried and failed to remove system files. Sorry."
			status = "FAIL"

		loggers.short_log(
			CurrentIngest,
			event,
			outcome,
			status
			)
	else:
		if not removedFiles == []: 
			outcome = "System files deleted at \n{}\n".format(
				"\n".join(removedFiles)
				)
			loggers.short_log(
			CurrentIngest,
			event,
			outcome,
			status
			)

		else:
			pass
	### END HIDDEN FILE HUNT ###
	############################

	subs = 0
	for _object in CurrentIngest.InputObject.ComponentObjects:
		if os.path.isdir(_object.inputPath):
			subs += 1
			print("\nYou have subdirectory(ies) in your input:"
				"\n({})\n".format(_object.inputPath))

	if subs > 0:
		# sequenceScanner checks for DPX folder structure compliance
		# and whether it is a single or multi-reel scan
		result,details = sequenceScanner.main(inputPath)
		if result != True:
			precheckPass = (False,"Directory structure and/or file format problems! See: {}".format(details))
		else:
			if details == 'single reel dpx':
				if CurrentIngest.includesSubmissionDocumentation:
					details = 'single-reel dpx with documentation'
			elif details == 'multi-reel dpx':
				if CurrentIngest.includesSubmissionDocumentation:
					details = 'multi-reel dpx with documentation'

			precheckPass = (True,details)
	else:
		precheckPass = (True,'discrete files')

	return precheckPass

def report_SIP_fixity(CurrentIngest,eventID):
	# parser returns tuple (True/False,{'filename1':'hash1','filename2':'hash2'})
	objectManifestPath = CurrentIngest.objectManifestPath
	parsed,hashes = loggers.parse_object_manifest(objectManifestPath)
	knownObjects = CurrentIngest.InputObject.ComponentObjects
	hashedObjects = []
	if not parsed == True:
		return parsed
	else:
		for item in knownObjects:
			for _object, _hash in hashes.items():
				# hashes dict should look like {'filename':'md5hash'}
				if _object == item.basename:
					item.md5hash = _hash
					CurrentIngest.currentTargetObject = item
					loggers.insert_fixity(
						CurrentIngest,
						eventID,
						messageDigestAlgorithm = "md5",
						messageDigestHashValue = _hash,
						messageDigestSource=objectManifestPath
						)
				hashedObjects.append(item)
			else:
				pass

	unhashed = [x for x in knownObjects if x not in hashedObjects]
	if unhashed != []:
		print('WARNING! {} are unhashed...')

	return True

def main():
	#########################
	#### SET INGEST ARGS ####
	args = set_args()
	inputPath = args.inputPath
	user = args.user
	objectJSON = args.metadataJSON
	databaseReporting = args.databaseReporting
	ingestType = args.ingestType
	makeProres = args.makeProres
	concatChoice = args.concatAccessFiles
	cleanupStrategy = args.cleanup_originals
	overrideOutdir = args.outdir_ingestsip
	overrideAIPdir = args.aip_staging
	overrideRS = args.resourcespace_deliver

	# init some objects
	CurrentProcess = ingestClasses.ProcessArguments(
		user,
		objectJSON,
		databaseReporting,
		ingestType,
		makeProres,
		concatChoice,
		cleanupStrategy,
		overrideOutdir,
		overrideAIPdir,
		overrideRS
		)
	CurrentObject = ingestClasses.InputObject(inputPath)
	CurrentIngest = ingestClasses.Ingest(CurrentProcess,CurrentObject)

	prepped = CurrentIngest.prep_package(
		CurrentIngest.tempID,
		CurrentIngest.ProcessArguments.outdir_ingestsip
		)
	if not prepped:
		print(CurrentIngest.ingestResults)
		return CurrentIngest
	else:
		CurrentIngest.accessPath = os.path.join(
			CurrentIngest.packageObjectDir,
			'resourcespace'
			)

	### Run some preparatory checks on directory inputs:
	### - If input has subidrs, see if it is a valid DPX input.
	### - Check for a valid submission documentation folder
	if CurrentIngest.InputObject.inputType == 'dir':
		if any(
			x for x in CurrentIngest.InputObject.ComponentObjects \
			if x.isDocumentation == True
			):
			CurrentIngest.includesSubmissionDocumentation = True

		# precheckPass is True/False conformance to expected folder structure
		# precheckDetails is the type of folder structure
		precheckPass,precheckDetails = directory_precheck(CurrentIngest)
		
		if precheckPass == False:
			CurrentIngest.currentTargetObject = CurrentIngest.ingestUUID
			pymmFunctions.cleanup_package(
				CurrentIngest,
				CurrentIngest.packageOutputDir,
				"ABORTING",
				precheckDetails
				)
			CurrentIngest.ingestResults['abortReason'] = precheckDetails
			print(CurrentIngest.ingestResults)
			return CurrentIngest
		
		elif precheckPass == True:
			# set inputType to one of:
			# - 'file'
			# - 'single discrete file with documentation'
			# - 'multiple discrete files'
			# - 'multiple discrete files with documentation'
			# - 'single-reel dpx'
			# - 'single-reel dpx with documentation'
			# - 'multi-reel dpx'
			# - 'multi-reel dpx with documentation'
			CurrentIngest.InputObject.inputType = precheckDetails

	#### END SET INGEST ARGS #### 
	#############################

	###########################
	#### LOGGING / CLEANUP ####
	# start a log file for this ingest
	CurrentIngest.create_ingestLog()

	# insert a database record for this SIP as an 'intellectual entity'
	CurrentIngest.currentTargetObject = CurrentIngest
	loggers.insert_object(
		CurrentIngest,
		objectCategory='intellectual entity',
		objectCategoryDetail='Archival Information Package'
		)

	# tell the various logs that we are starting
	CurrentIngest.caller = 'ingestSIP.main()'
	# CurrentIngest.currentTargetObject = CurrentIngest.InputObject.canonicalName
	loggers.log_event(
		CurrentIngest,
		event = 'ingestion start',
		outcome = "SYSTEM INFO:\n{}".format(pymmFunctions.system_info()),
		status = 'STARTING'
		)

	# reset variables
	CurrentIngest.caller = None

	# Log any filename outliers as a WARNING
	if CurrentIngest.InputObject.outlierComponents != []:
		CurrentIngest.currentTargetObject = CurrentIngest
		loggers.log_event(
			CurrentIngest,
			event = 'validation',
			outcome = 'test of input filenames '\
				'reveals these outliers that may not belong: {}'.format(
					';'.join(CurrentIngest.InputObject.outlierComponents)
					),
			status = 'WARNING'
			)

	# Send existing descriptive metadata JSON to the object metadata directory
	if CurrentIngest.ProcessArguments.objectJSON != None:
		copy = shutil.copy2(
			CurrentIngest.ProcessArguments.objectJSON,
			CurrentIngest.packageMetadataDir
			)
		# reset var to new path
		CurrentIngest.ProcessArguments.objectJSON = os.path.abspath(copy)
		makePbcore.add_physical_elements(
			CurrentIngest.InputObject.pbcoreXML,
			CurrentIngest.ProcessArguments.objectJSON
			)
	else:
		# if no descriptive metadata, just use a container pbcore.xml w/o a
		# representation of the physical/original asset
		# this is created in the __init__ of an InputObject
		pass
	# Write the XML to file
	CurrentIngest.InputObject.pbcoreFile = makePbcore.xml_to_file(
		CurrentIngest.InputObject.pbcoreXML,
		os.path.join(
			CurrentIngest.packageMetadataDir,
			CurrentIngest.InputObject.canonicalName+"_pbcore.xml"
			)
		)

	if os.path.exists(CurrentIngest.InputObject.pbcoreFile):
		status = 'OK'
	else:
		status = 'Fail'
	CurrentIngest.caller = 'pbcore.PBCoreDocument() , makePbcore.xml_to_file()'
	loggers.short_log(
		CurrentIngest,
		event = 'metadata extraction',
		outcome = 'make pbcore representation',
		status = status
		)
	CurrentIngest.caller = None
	CurrentIngest.currentTargetObject = None
	#### END LOGGING / CLEANUP ####
	###############################

	########################
	  ####################
	     ## DO STUFF! ##
	  ####################
	#########################
	
	########################
	# insert the objects
	for _object in CurrentIngest.InputObject.ComponentObjects:
		CurrentIngest.currentTargetObject = _object

		loggers.insert_object(
			CurrentIngest,
			_object.objectCategory,
			_object.objectCategoryDetail
			)

		if _object.objectCategoryDetail == 'film scanner output reel':
			# create a component object for each WAV and DPX
			# component of a film scan
			for item in os.listdir(_object.inputPath):
				itemPath = os.path.join(_object.inputPath,item)
				if os.path.isfile(itemPath):
					objectCategory = 'file'
					objectCategoryDetail = 'preservation master audio'
				elif os.path.isdir(itemPath):
					objectCategory = 'intellectual entity'
					objectCategoryDetail = 'preservation master image sequence'
				subObject = ingestClasses.ComponentObject(
					itemPath,
					objectCategory=objectCategory,
					objectCategoryDetail=objectCategoryDetail,
					topLevelObject = False
					)
				CurrentIngest.InputObject.ComponentObjects.append(subObject)
				CurrentIngest.currentTargetObject = subObject

				loggers.insert_object(
					CurrentIngest,
					subObject.objectCategory,
					subObject.objectCategoryDetail
					)

		CurrentIngest.currentTargetObject = _object

		print("MOVING")
		move_component_object(CurrentIngest)

	for _object in CurrentIngest.InputObject.ComponentObjects:
		if not (_object.isDocumentation):
			if not _object.objectCategoryDetail == 'film scanner output reel':
				if _object.topLevelObject == True:
					# we log metadata for the scanner output
					# components individually
					add_pbcore_instantiation(
						CurrentIngest,
						"Preservation master"
						)

					CurrentIngest.currentMetadataDestination = \
						CurrentIngest.packageMetadataObjects
					get_file_metadata(CurrentIngest)
					CurrentIngest.currentMetadataDestination = None
					loggers.pymm_log(
						CurrentIngest,
						event = 'metadata extraction',
						outcome = 'calculate input file technical metadata',
						status = 'OK'
						)
			if _object.topLevelObject == True:
				# but the access file is made by calling the scanner
				# output as a whole
				isSequence,rsPackage = None,None
				if _object.avStatus == 'DPX':
					isSequence = True
				if 'multi' in CurrentIngest.InputObject.inputType:
					rsPackage = True
				_object.accessPath = make_derivs(
					CurrentIngest,
					rsPackage=rsPackage,
					isSequence=isSequence
					)
	if CurrentIngest.ProcessArguments.concatChoice == True:
		av = [
			x for x in CurrentIngest.InputObject.ComponentObjects \
			if x.objectCategory == 'access file'
			]
		avType = av[0].avStatus
		if avType == 'AUDIO':
			wrapper = 'mp3'
		elif avType == "VIDEO":
			wrapper = 'mp4'

		concatPath = concat_access_files(
			CurrentIngest,
			wrapper
			)
		if os.path.exists(concatPath):
			deliver_concat_access(
				concatPath,
				CurrentIngest.accessPath
				)

	#########################
	### SINGLE-FILE INPUT ###
	# if CurrentIngest.InputObject.inputType == 'file':
	# 	# take the first ComponentObject
	# 	CurrentIngest.currentTargetObject = CurrentIngest.InputObject.ComponentObjects[0]
	# 	loggers.insert_object(
	# 		CurrentIngest,
	# 		objectCategory = 'file',
	# 		objectCategoryDetail='preservation master'
	# 		)
	# 	# I THINK THS AV TEST IS BUNK AND ALSO MAYBE NOT HELPFUL?
	# 	# check that input file is actually a/v
	# 	avStatus, AV = check_av_status(CurrentIngest)

	# 	# mediaconch_check(inputPath,ingestType,ingestLogBoilerplate) # @dbme
	# 	move_component_object(CurrentIngest)

	# 	add_pbcore_instantiation(
	# 		CurrentIngest,
	# 		"Preservation master"
	# 		)

	# 	CurrentIngest.currentMetadataDestination = \
	# 		CurrentIngest.packageMetadataObjects

	# 	get_file_metadata(CurrentIngest)

	# 	CurrentIngest.currentMetadataDestination = None

	# 	loggers.pymm_log(
	# 		CurrentIngest,
	# 		event = 'metadata extraction',
	# 		outcome = 'calculate input file technical metadata',
	# 		status = 'OK'
	# 		)
	# 	CurrentIngest.accessPath = make_derivs(CurrentIngest)

	# #######################################################
	# ### ONE OR MORE FILES WITH SUBMISSION DOCUMENTATION ###
	# elif CurrentIngest.InputObject.inputType == \
	# 	'discrete file(s) with documentation':
	# 	for _object in CurrentIngest.InputObject.ComponentObjects:
	# 		CurrentIngest.currentTargetObject = _object

	# 		if _object.isDocumentation:
	# 			loggers.insert_object(
	# 				CurrentIngest,
	# 				objectCategory = 'intellectual entity',
	# 				objectCategoryDetail=(
	# 					'submission documentation folder'
	# 					' with these contents: {}'.format(
	# 						'; '.join(self.documentationContents)
	# 						)
	# 					)
	# 				)
	# 			move_component_object(CurrentIngest)

	# ### MULTIPLE, DISCRETE AV FILES INPUT ###
	# elif inputType == 'discrete files':
	# 	for _file in source_list:			
	# 		# set processing variables per file 
	# 		ingestLogBoilerplate['filename'] = os.path.basename(_file)
	# 		processingVars['filename'] = os.path.basename(_file)
	# 		processingVars['inputPath']=\
	# 			ingestLogBoilerplate['inputPath'] = _file
	# 		processingVars = pymmFunctions.insert_object(
	# 			processingVars,
	# 			objectCategory = 'file',
	# 			objectCategoryDetail='preservation master'
	# 			)
	# 		#######################
	# 		# check that input file is actually a/v
	# 		avStatus, AV = check_av_status(CurrentIngest)

	# 		# check against mediaconch policy
	# 		# mediaconch_check(_file,ingestType,ingestLogBoilerplate) # @dbme
	# 		processingVars,ingestLogBoilerplate = move_component_object(
	# 			processingVars,ingestLogBoilerplate
	# 			)
	# 		add_pbcore_instantiation(
	# 			processingVars,
	# 			ingestLogBoilerplate,
	# 			"Preservation master"
	# 			)

	# 		get_file_metadata(ingestLogBoilerplate,processingVars)
	# 		pymmFunctions.pymm_log(
	# 			processingVars,
	# 			event = 'metadata extraction',
	# 			outcome = 'calculate input file technical metadata',
	# 			status = 'OK'
	# 			)
	# 		#######################
	# 		# for a directory input, `accessPath` is 
	# 		# the containing folder under the one
	# 		# defined in config.ini
	# 		accessPath = make_derivs(
	# 			ingestLogBoilerplate,
	# 			processingVars,
	# 			rsPackage=True
	# 			)
			
	# 	# reset the processing variables to the original state 
	# 	processingVars['filename'] = ''
	# 	processingVars['inputPath']=\
	# 		processingVars['inputName'] =\
	# 		ingestLogBoilerplate['inputPath'] = inputPath

	# 	if concatChoice == True:
	# 		# TRY TO CONCATENATE THE ACCESS FILES INTO A SINGLE FILE...
	# 		SIPaccessPath = os.path.join(
	# 			processingVars['packageObjectDir'],
	# 			'resourcespace'
	# 			)
	# 		# choose the concatenation wrapper depending on the input type
	# 		if AV == 'VIDEO':
	# 			wrapper = 'mp4'
	# 		elif AV == 'AUDIO':
	# 			wrapper = 'mp3'
	# 		else:
	# 			# this should never be anything other than
	# 			# AUDIO or VIDEO, but just in case...
	# 			wrapper = 'mp4' 
	# 		concatPath = concat_access_files(
	# 			SIPaccessPath,
	# 			ingestUUID,
	# 			canonicalName,
	# 			wrapper,
	# 			ingestLogBoilerplate,
	# 			processingVars
	# 			)
	# 		if os.path.exists(concatPath):
	# 			deliver_concat_access(
	# 				concatPath,
	# 				accessPath
	# 				)

	# #### SINGLE-REEL DPX INPUT ####
	# elif inputType == 'single reel dpx':
	# 	processingVars = pymmFunctions.insert_object(
	# 		processingVars,
	# 		objectCategory='intellectual entity',
	# 		objectCategoryDetail='film scanner output reel'
	# 		)
	# 	for _object in source_list:
	# 		if os.path.isfile(_object):
	# 			ingestLogBoilerplate['filename'] = os.path.basename(_object)
	# 			processingVars['filename'] = os.path.basename(_object)
	# 			processingVars['inputPath']=\
	# 				ingestLogBoilerplate['inputPath'] = _object
	# 			processingVars = pymmFunctions.insert_object(
	# 				processingVars,
	# 				objectCategory='file',
	# 				objectCategoryDetail='preservation master audio'
	# 				)
	# 		elif os.path.isdir(_object):
	# 			# set filename to be the _object path
	# 			ingestLogBoilerplate['inputPath'] =\
	# 				processingVars['inputPath'] = _object
	# 			ingestLogBoilerplate['filename'] =\
	# 				processingVars['filename'] = "{}_{}".format(
	# 					canonicalName,
	# 					os.path.basename(_object)
	# 					)
	# 			processingVars = pymmFunctions.insert_object(
	# 				processingVars,
	# 				objectCategory='intellectual entity',
	# 				objectCategoryDetail='preservation master image sequence'
	# 				)

	# 		get_file_metadata(ingestLogBoilerplate,processingVars)
	# 		pymmFunctions.pymm_log(
	# 			processingVars,
	# 			event = 'metadata extraction',
	# 			outcome = 'calculate input file technical metadata',
	# 			status = 'OK'
	# 			)
	# 		add_pbcore_instantiation(
	# 			processingVars,
	# 			ingestLogBoilerplate,
	# 			"Preservation master"
	# 			)
	# 	ingestLogBoilerplate['filename'] =\
	# 		processingVars['filename'] = ''
	# 	ingestLogBoilerplate['inputPath'] =\
	# 		processingVars['inputPath'] = inputPath
	# 	processingVars,ingestLogBoilerplate = move_component_object(
	# 			processingVars,ingestLogBoilerplate
	# 			)
	# 	accessPath = make_derivs(
	# 		ingestLogBoilerplate,
	# 		processingVars,
	# 		rsPackage=None,
	# 		isSequence=True
	# 		)

	# #### MULTI-REEL DPX INPUT ####
	# elif inputType == 'multi-reel dpx':
	# 	masterList = source_list
	# 	for reel in masterList:
	# 		# clear out any preexisting filename value
	# 		ingestLogBoilerplate['filename'] =\
	# 			processingVars['filename'] = ''
	# 		ingestLogBoilerplate['inputPath'] =\
	# 			processingVars['inputPath'] = reel
	# 		processingVars['inputName'] = os.path.basename(reel)
	# 		reel_list = pymmFunctions.list_files(reel)

	# 		processingVars = pymmFunctions.insert_object(
	# 			processingVars,
	# 			objectCategory='intellectual entity',
	# 			objectCategoryDetail='film scanner output reel'
	# 			)
	# 		for _object in reel_list:
	# 			if os.path.isfile(_object):
	# 				ingestLogBoilerplate['filename'] =\
	# 					processingVars['filename'] = os.path.basename(_object)
	# 				processingVars['inputPath']=\
	# 					ingestLogBoilerplate['inputPath'] = _object
	# 				processingVars = pymmFunctions.insert_object(
	# 					processingVars,
	# 					objectCategory='file',
	# 					objectCategoryDetail='preservation master audio'
	# 					)
	# 			elif os.path.isdir(_object):
	# 				# set filename to be the _object path
	# 				ingestLogBoilerplate['inputPath'] =\
	# 					processingVars['inputPath'] = _object
	# 				ingestLogBoilerplate['filename'] =\
	# 					processingVars['filename'] = "{}_{}".format(
	# 						processingVars['inputName'],
	# 						os.path.basename(_object)
	# 						)
	# 				processingVars = pymmFunctions.insert_object(
	# 					processingVars,
	# 					objectCategory='intellectual entity',
	# 					objectCategoryDetail='preservation master image sequence'
	# 					)

	# 			get_file_metadata(ingestLogBoilerplate,processingVars)
	# 			pymmFunctions.pymm_log(
	# 				processingVars,
	# 				event = 'metadata extraction',
	# 				outcome = 'calculate input file technical metadata',
	# 				status = 'OK'
	# 				)
	# 			add_pbcore_instantiation(
	# 				processingVars,
	# 				ingestLogBoilerplate,
	# 				"Preservation master"
	# 				)
	# 		ingestLogBoilerplate['filename'] =\
	# 			processingVars['filename'] = ''
	# 		ingestLogBoilerplate['inputPath'] =\
	# 			processingVars['inputPath'] = reel
	# 		processingVars,ingestLogBoilerplate = move_component_object(
	# 				processingVars,ingestLogBoilerplate
	# 				)

	# 		accessPath = make_derivs(
	# 			ingestLogBoilerplate,
	# 			processingVars,
	# 			rsPackage=True,
	# 			isSequence=True
	# 			)
	# 	if concatChoice == True:
	# 		# TRY TO CONCATENATE THE ACCESS FILES INTO A SINGLE FILE...
	# 		SIPaccessPath = os.path.join(
	# 			processingVars['packageObjectDir'],
	# 			'resourcespace'
	# 			)
	# 		concatPath = concat_access_files(
	# 			SIPaccessPath,
	# 			ingestUUID,
	# 			canonicalName,
	# 			'mp4',
	# 			ingestLogBoilerplate,
	# 			processingVars
	# 			)
	# 		if os.path.exists(concatPath):
	# 			deliver_concat_access(
	# 				concatPath,
	# 				accessPath
	# 				)
	### END ACTUAL STUFF DOING ###
	##############################
	
	###############################
	## FLUFF THE SIP FOR STAGING ##

	# set the logging 'filename' to the UUID for the rest of the process
	CurrentIngest.currentTargetObject = CurrentIngest
	# rename SIP from temp to UUID; _SIP is the staged UUID path
	_SIP = rename_SIP(CurrentIngest)
	# put the package into a UUID parent folder
	envelop_SIP(CurrentIngest)

	# make a hashdeep manifest for the objects directory
	objectManifestPath = makeMetadata.make_hashdeep_manifest(
		CurrentIngest.packageObjectDir,
		CurrentIngest.ingestUUID,
		'objects'
		)
	CurrentIngest.objectManifestPath = objectManifestPath
	outcome = (
		'create hashdeep manifest '
		'for objects directory at {}'.format(objectManifestPath)
		)
	status = 'OK'
	CurrentIngest.caller = 'hashdeep'
	if not os.path.isfile(objectManifestPath):
		status = 'FAIL'
		outcome = 'could not '+outcome
	else:
		pass
	eventID = loggers.short_log(
		CurrentIngest,
		event = 'message digest calculation',
		outcome = outcome,
		status = status
		)
	# report data from the object manifest
	report_SIP_fixity(CurrentIngest,eventID)
	CurrentIngest.caller = None	
	# also add md5 and filename for each object as identifiers
	# to the pbcore record
	add_pbcore_md5_location(CurrentIngest)
	# report characteristics of the SIP's objects
	if CurrentIngest.ProcessArguments.databaseReporting == True:
		loggers.insert_obj_chars(CurrentIngest)

	#####
	# AT THIS POINT THE SIP IS FULLY FORMED SO LOG IT AS SUCH
	CurrentIngest.currentTargetObject = CurrentIngest
	CurrentIngest.caller = 'ingestSIP.main()'
	loggers.short_log(
		CurrentIngest,
		event = 'information package creation',
		outcome = 'assemble SIP into valid structure',
		status = 'OK'
		)
	CurrentIngest.caller = None

	# recursively set SIP and manifest to 777 file permission
	chmodded = pymmFunctions.recursive_chmod(_SIP)
	CurrentIngest.caller = 'Python3 os.chmod(x,0o777)'
	if chmodded:
		status = 'OK'
	else:
		status = 'FAIL'
	loggers.short_log(
		CurrentIngest,
		event = 'modification',
		outcome = 'recursively set SIP and manifest file permissions to 777',
		status = status
		)
	CurrentIngest.caller = None

	packageVerified = False
	# move the SIP if needed
	if not CurrentIngest.ProcessArguments.aip_staging == \
		CurrentIngest.ProcessArguments.outdir_ingestsip:

		_SIP = stage_sip(CurrentIngest)
		# audit the hashdeep manifest 
		objectsVerified = False
		auditOutcome,objectsVerified = makeMetadata.hashdeep_audit(
			_SIP,
			objectManifestPath,
			_type='objects'
			)
		CurrentIngest.caller = 'hashdeep'
		if objectsVerified == True:
			status = 'OK'
			outcome = (
				'Objects directory verified against hashdeep manifest: \n{}'
				''.format(auditOutcome)
				)
		else:
			status = "WARNING"
			outcome = (
				"Objects directory failed hashdeep audit. "
				"Some files may be missing or damaged!"
				"Check the hashdeep audit: \n{}".format(auditOutcome)
				)
		loggers.log_event(
			CurrentIngest,
			event = 'fixity check',
			outcome = outcome,
			status = status
			)
		CurrentIngest.caller = None

	else:
		objectsVerified = True

	validSIP,validationOutcome = pymmFunctions.validate_SIP_structure(_SIP)
	if not validSIP:
		# IS QUITTING HERE EXCESSIVE?? MAYBE JUST LOG 
		#     THAT IT DIDN'T PASS MUSTER BUT SAVE IT.
		# OR MAKE AN "INCONCLUSIVE/WARNING" VERSION?
		# NOTE: the failure gets logged in the system log,
		#   along with listing reasons for failure
		#   then the abort message is logged in cleanup_package()
		pymmFunctions.cleanup_package(
			CurrentIngest,
			_SIP,
			"ABORTING",
			validationOutcome
			)
		CurrentIngest.ingestResults['abortReason'] = validationOutcome
		print(CurrentIngest.ingestResults)
		return CurrentIngest
	else:
		CurrentIngest.caller = 'pymmFunctions.validate_SIP_structure()'
		loggers.log_event(
			CurrentIngest,
			event = "validation",
			outcome = "SIP validated against expected structure",
			status = "OK"
			)
		CurrentIngest.caller = None

	if objectsVerified and validSIP:
		CurrentIngest.ingestResults['status'] = True
	CurrentIngest.ingestResults['ingestUUID'] = CurrentIngest.ingestUUID
	CurrentIngest.ingestResults['accessPath'] = CurrentIngest.accessPath

	# THIS IS THE LAST CALL MADE TO MODIFY ANYTHING IN THE SIP.
	loggers.ingest_log(
		CurrentIngest,
		event = 'ingestion end',
		outcome = 'Submission Information Package verified and staged',
		status = 'ENDING'
		)

	# make a hashdeep manifest
	manifestPath = makeMetadata.make_hashdeep_manifest(
		_SIP,
		CurrentIngest.ingestUUID,
		'hashdeep'
		)
	CurrentIngest.caller = 'hashdeep'
	if os.path.isfile(manifestPath):
		loggers.end_log(
			CurrentIngest,
			event = 'message digest calculation',
			outcome = 'create hashdeep manifest '\
				'for SIP at {}'.format(manifestPath),
			status = 'OK'
			)
	do_cleanup(
		CurrentIngest,
		objectsVerified,
		'done'
		)
	CurrentIngest.caller = 'ingestSIP.main()'	
	loggers.end_log(
		CurrentIngest,
		event = 'ingestion end',
		outcome = 'Submission Information Package verified and staged',
		status = 'ENDING'
		)
	
	if CurrentIngest.ingestResults['status'] == True:
		print("####\nEVERYTHING WENT GREAT! "
			"THE SIP IS GOOD TO GO! @{}\n####".format(_SIP))
	else:
		print("####\nSOMETHING DID NOT GO AS PLANNED. "
			"CHECK THE LOG FOR MORE DETAILS!\n####")

	print(CurrentIngest.ingestResults)
	return CurrentIngest

if __name__ == '__main__':
	main()
