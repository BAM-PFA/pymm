#!/usr/bin/env python3
# standard library modules
import os
import sys
import json
from copy import deepcopy
# nonstandard libraries
import lxml.etree as ET
# local modules
from . import pbcore_map
from . import pbcore

def tidy(self):
	'''
	I need to make the order match the schema order.
	'''
	pass

def add_instantiation(self, pbcoreInstantiationPath, descriptiveJSONpath=None, level=None):
	'''
	Add an instantiation via mediainfo output.
	Add a json file of BAMPFA descriptive metadata
	to relate the instantiation to the instantiation for
	the physical asset.
	`level` should refer to:
	Preservation master, Access copy, Mezzanine
	'''
	# This parser declaration avoids XPath failure on special characters
	parser = ET.XMLParser(recover=True)
	try:
		pbcoreInstantiation = ET.parse(pbcoreInstantiationPath,parser=parser)
		# print(pbcoreInstantiation)

	except:
		try:
			# see if it's a bytes type object...
			pbcoreString = ET.fromstring(pbcoreInstantiationPath,parser=parser)
			pbcoreInstantiation = ET.ElementTree(pbcoreString)
		except:
			print('not a valid xml input ... probably?')
			sys.exit()

	instantiation = add_SubElement(
		self,
		self.descriptionRoot,
		'pbcoreInstantiation',
		nsmap=self.NS_MAP
		)

	for element in pbcoreInstantiation.xpath(
		'/p:pbcoreInstantiationDocument/*',
		namespaces=self.XPATH_NS_MAP
		):
		instantiation.insert(0,deepcopy(element))

	if descriptiveJSONpath != None:
		add_related_physical(
			self,
			instantiation,
			_id=get_related_physical_ID(self,descriptiveJSONpath)
			)

	if level != None:
		comment = ET.Comment(level)
		instantiation.insert(0,comment)

	return instantiation

def add_element_to_instantiation(self,identifier,element,attributes={},text=None):
	targetInstantiationXpath = (
			"/p:pbcoreDescriptionDocument/p:pbcoreInstantiation"
			"[p:instantiationIdentifier[@source='File Name']/"
			"text()[contains(.,'{}')]]".format(identifier)
			)
	# print(targetInstantiationXpath)
	targetInstantiation = self.descriptionRoot.xpath(
		targetInstantiationXpath,
		namespaces=self.XPATH_NS_MAP
		)
	# print(targetInstantiation)
	# print(attributes)
	if targetInstantiation != []:
		add_SubElement(
			self,
			targetInstantiation[0],
			element,
			attrib=attributes,
			_text=text,
			nsmap=self.NS_MAP
			)

def add_related_physical(self,instantiation,_id=None):
	if _id == None:
		return None
	else:
		relation = add_SubElement(
				self,
				instantiation,
				'instantiationRelation',
				nsmap=self.NS_MAP
				)
		add_SubElement(
			self,
			relation,
			'instantiationRelationType',
			attrib={
				'source':'PBCore relationType',
				'ref':(
					'http://metadataregistry.org/'
					'concept/list/vocabulary_id/161.html'
					)
			},
			_text='Derived from',
			nsmap=self.NS_MAP
			)
		add_SubElement(
			self,
			relation,
			'instantiationRelationIdentifier',
			_text=_id,
			nsmap=self.NS_MAP
		)

def get_related_physical_ID(self, descriptiveJSONpath):
	'''
	Look for a barcode or an accession number for the 
	instantiationRelationIdentifier value. 
	This relies on the FMP barcode output which concatenates
	all reel barcodes into one string. I should redo this to look for a 
	barcode in the filename a la the filename parsing in fmQuery.py
	'''
	descriptiveJSON = json.load(open(descriptiveJSONpath))
	asset = list(descriptiveJSON.keys())[0]
	assetBarcode = descriptiveJSON[asset]['metadata']['Barcode']
	assetAccNo = descriptiveJSON[asset]['metadata']['accFull']

	if assetAccNo != "":
		physicalAccXpath = (
			"/p:pbcoreDescriptionDocument/p:pbcoreInstantiation/"
			"p:instantiationIdentifier[@source='PFA accession number']/text()"
			)
		physicalAccNo = self.descriptionRoot.xpath(
			physicalAccXpath,
			namespaces=self.XPATH_NS_MAP
			)
		try:
			_id = physicalAccNo[0]
		except:
			print('trying no namespaces')
			# i found that namespaces aren't appended to tags until the doc 
			# is written to file.... this catches namespaceless elements
			# physicalAccXpath.replace('p:','')
			# print(physicalAccXpath)
			physicalAccNo = self.descriptionRoot.xpath(
				physicalAccXpath.replace('p:',''),
				namespaces=self.XPATH_NS_MAP
				)
			try:
				_id = physicalAccNo[0]
				# print(_id)
			except:
				_id = None

		return _id

	elif assetAccNo == "" and assetBarcode != "":
		physicalBarcodeXpath = (
			"/p:pbcoreDescriptionDocument/p:pbcoreInstantiation/"
			"p:instantiationIdentifier[@source='PFA barcode']/text()"
			)
		physicalBarcode = self.descriptionRoot.xpath(
			physicalBarcodeXpath,
			namespaces=self.XPATH_NS_MAP
			)
		_id = physicalBarcode[0]

		return _id

	else:
		return None

def add_SubElement(
	self,
	_parent,
	_tag,
	attrib={},
	_text=None,
	nsmap=None,
	**_extra
	):
	# e.g. >> sample.add_SubElement(
	#			 sample.descriptionRoot,
	#			 'pbcoreSub',{},'HELLO',
	#			 sample.NS_MAP)
	result = ET.SubElement(_parent,_tag,attrib,nsmap)
	result.text = _text
	return result

def add_pbcore_subelements(self,top,mappedSubelements,mdValue):
	for key,value in mappedSubelements.items():
		# print(key)
		if "ATTRIBUTES" in mappedSubelements[key]:
			attrib = mappedSubelements[key]["ATTRIBUTES"]
		else:
			attrib = {}
		subelement = add_SubElement(
			self,
			top,
			key,
			attrib=attrib,
			nsmap=self.NS_MAP
			)
		# print(subelement)
		if mappedSubelements[key]["TEXT"] == "value":
			subelement.text = mdValue
		else:
			subelement.text = mappedSubelements[key]["TEXT"]

def add_physical_elements(self,descriptiveJSONpath):
	'''
	load metadata json file in specific format,
	drawn from BAMPFA CMS and user-input form:
	{assetpath:{
		metadata:{
			field1:value1,
			field2:value2
		},
		basename:assetBasename
		}
	}
	'''
	# add an empty instantiation for the physical asset
	physicalInstantiation = add_SubElement(
		self,
		self.descriptionRoot,
		'pbcoreInstantiation',
		nsmap=self.NS_MAP
		)

	comment = ET.Comment("Physical/Original Asset")
	physicalInstantiation.insert(0,comment)
	descriptiveJSON = json.load(open(descriptiveJSONpath))
	# there should be only one asset
	asset = list(descriptiveJSON.keys())[0]
	assetBasename = descriptiveJSON[asset]['basename']

	# grab the metadata dict from the JSON file
	metadata = descriptiveJSON[asset]['metadata']
	descMetadataFields = []
	for key,value in metadata.items():
		if value not in ("",None,"None","null"):
			# we only want the fieds with values
			descMetadataFields.append(key)

	for field in pbcore_map.BAMPFA_FIELDS:
		# loop through the nonempty fields and 
		# match them to the PBCore mapping
		if field in descMetadataFields:
			# print(field)
			# grab the md value and set it for this loop
			mdValue = metadata[field]
			mapping = pbcore_map.PBCORE_MAP[field]
			mappingTarget = list(mapping.keys())[0]
			mappedPbcore = mapping[mappingTarget]
			# check if the field applies to the 
			# `level` here should == WORK or INSTANTIATION
			level = mappedPbcore["LEVEL"]
			if level == "WORK":
				insertionTarget = self.descriptionRoot
			elif level == "INSTANTIATION":
				insertionTarget = physicalInstantiation

			# set any attributes if applicable
			if "ATTRIBUTES" in mappedPbcore:
				mappingAttribs = mappedPbcore["ATTRIBUTES"]
			else:
				mappingAttribs = {}

			if "TRACK" in mappedPbcore:
				# TRACK should equal 'Audio' or 'Video'
				# see if any other fields have already been set 
				# within an <instantiationEssenceTrack> tag, 
				# or create one if need be.
				track = mappedPbcore["TRACK"]
				# XPATH to find an existing essence track
				trackXpath = (
					"//pbcoreInstantiation"\
					"[comment()='Physical/Original Asset']/"\
					"instantiationEssenceTrack["\
					"essenceTrackType[text()='{}'"\
					"]]".format(track)
					)
				print(trackXpath)
				if track == "Video":
					existingEssenceTrack = physicalInstantiation.xpath(
						trackXpath,
						namespaces=self.XPATH_NS_MAP
						)
					print(existingEssenceTrack)
				elif track == 'Audio':
					existingEssenceTrack = physicalInstantiation.xpath(
						trackXpath,
						namespaces=self.XPATH_NS_MAP
						)
				if existingEssenceTrack != []:
					insertionTarget = existingEssenceTrack[0]
				else:
					# add an <instantiationEssenceTrack> tag
					essenceTrack = add_SubElement(
						self,
						physicalInstantiation,
						'instantiationEssenceTrack',
						attrib={},
						_text=None,
						nsmap=self.NS_MAP
					)
					add_SubElement(
						self,
						essenceTrack,
						'essenceTrackType',
						attrib={},
						_text=track,
						nsmap=self.NS_MAP
					)
					insertionTarget = essenceTrack

			if mappedPbcore["TEXT"] == "value":
				'''
				If there are no subfields involved, just write the 
				value to the pbcore element.
				'''
				add_SubElement(
					self,
					insertionTarget,
					mappingTarget,
					attrib=mappingAttribs,
					_text=mdValue,
					nsmap=self.NS_MAP
					)

			else:
				'''
				If the meat is in a SubElement
				add the relevant subelement(s)
				'''
				mappedSubelements = mappedPbcore["SUBELEMENTS"]

				# if level == "WORK":
				top = add_SubElement(
					self,
					insertionTarget,
					mappingTarget,
					attrib=mappingAttribs,
					nsmap=self.NS_MAP
					)
				add_pbcore_subelements(self,top,mappedSubelements,mdValue)

	return True

def to_string(self):
	self._string = ET.tostring(self.descriptionRoot, pretty_print=True)
	# print(self._string.decode())
	return self._string.decode()

def xml_to_file(self,outputPath):
	with open(outputPath,'wb') as outXML:
		# take the current state of the ElementTree object 
		# and write it to file.
		self.descriptionDoc.write(
			outXML, 
			encoding='utf-8', 
			xml_declaration=True,
			pretty_print=True)
	return outputPath

def main():
	'''
	Eventually make this callable from CLI.
	pass arguments:
	-j descriptiveJSONpath
	-x existing pbcore xml filepath
	-i existing instantiation xml filepath
	-p add physical asset elements
	-c create blank xml
	-a add element to instantiation
	'''
	pass
