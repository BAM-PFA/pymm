#!/usr/bin/env python3
# classes for database reporting
# ONE CLASS PER TABLE?? IS THAT A GOOD IDEA??

import os
import sys
# local modules
import MySQLqueries
import pymmFunctions

class EventInsert:
	'''
	gather variables
	do the thing (make the report)

	'''
	def __init__(
		self, 
		eventType,
		objectIdentifierValue,
		objectIdentifierValueID,
		eventDateTime=None,
		eventOutcome=None,
		eventOutcomeDetail=None,
		eventDetailCallingFunc=None,
		eventDetailComputer=None,
		linkingAgentIdentifierValue=None,
		eventID=None
		):
		'''
		Each attribute corresponds to a field in the table.
		They are initialized as None since they might not all have values
		by the time the instance is called.
		eventID will be returned after report_to_db is called.
		'''
		self.eventType = eventType
		self.objectIdentifierValue = objectIdentifierValue
		self.objectIdentifierValueID = objectIdentifierValueID
		self.eventDateTime = eventDateTime
		self.eventOutcome = eventOutcome
		self.eventOutcomeDetail = eventOutcomeDetail
		self.eventDetailCallingFunc = eventDetailCallingFunc
		self.eventDetailComputer = eventDetailComputer
		# this is OPERATOR defined in ingestSip.main()
		self.linkingAgentIdentifierValue = linkingAgentIdentifierValue
		# to be returned later
		self.eventID = ''

	def report_to_db(self):
		# connect to the database
		connection = pymmFunctions.database_connection(
			self.linkingAgentIdentifierValue
			)
		# print(connection)
		# get the sql query
		sql = MySQLqueries.insertEventSQL

		cursor = pymmFunctions.do_query(
			connection,
			sql,
			self.eventType,
			self.objectIdentifierValue,
			self.objectIdentifierValueID,
			self.eventDateTime,
			self.eventOutcome,
			self.eventOutcomeDetail,
			self.eventDetailCallingFunc,
			self.eventDetailComputer,
			self.linkingAgentIdentifierValue
			)
		self.eventID = cursor.lastrowid

		connection.close_cursor()
		connection.close_connection()

		return self.eventID

class ObjectInsert:
	'''
	gather variables
	do the thing (make the report)

	'''
	def __init__(
		self,
		user,
		objectIdentifierValue,
		objectCategory=None,
		objectCategoryDetail=None,
		objectIdentifierValueID=None
		):
		'''
		Each attribute corresponds to a field in the table.
		objectIdentifierValueID will be returned after report_to_db is called.
		'''
		self.user = user
		self.objectIdentifierValue = objectIdentifierValue
		self.objectCategory = objectCategory
		self.objectCategoryDetail = objectCategoryDetail
		self.objectIdentifierValueID = objectIdentifierValueID

	def report_to_db(self):
		# connect to the database
		connection = pymmFunctions.database_connection(
			self.user
			)
		# get the sql query
		sql = MySQLqueries.insertObjectSQL

		cursor = pymmFunctions.do_query(
			connection,
			sql,
			self.objectIdentifierValue,
			self.objectCategory,
			self.objectCategoryDetail
			)
		self.objectIdentifierValueID = cursor.lastrowid

		connection.close_cursor()
		connection.close_connection()

		return self.objectIdentifierValueID

class FixityInsert:
	'''
	gather variables
	do the thing (make the report)

	'''
	def __init__(
		self,
		user,
		eventID,
		objectID,
		objectIdentifierValue,
		eventDetailCallingFunc,
		messageDigestAlgorithm,
		messageDigestFilepath,
		messageDigestHashValue,
		messageDigestSource=None,
		eventDateTime = None,
		fixityID = None
		):
		'''
		Each attribute corresponds to a field in the table.
		fixityID will be returned after report_to_db is called.
		'''
		self.user = user
		self.eventID = eventID
		self.objectID = objectID
		self.objectIdentifierValue = objectIdentifierValue
		self.eventDetailCallingFunc = eventDetailCallingFunc
		self.messageDigestAlgorithm = messageDigestAlgorithm
		self.messageDigestFilepath = messageDigestFilepath
		self.messageDigestHashValue = messageDigestHashValue
		self.messageDigestSource = messageDigestSource
		self.eventDateTime = eventDateTime
		self.fixityID = fixityID

	def report_to_db(self):
		# connect to the database
		connection = pymmFunctions.database_connection(
			self.user
			)
		# get the sql query
		sql = MySQLqueries.insertFixitySQL

		cursor = pymmFunctions.do_query(
			connection,
			sql,
			self.eventID,
			self.objectID,
			self.objectIdentifierValue,
			self.eventDateTime,
			self.eventDetailCallingFunc,
			self.messageDigestAlgorithm,
			self.messageDigestFilepath,
			self.messageDigestHashValue,
			self.messageDigestSource
			)
		self.fixityID = cursor.lastrowid

		connection.close_cursor()
		connection.close_connection()

		return self.fixityID

class InsertObjChars:
	'''
	gather variables
	do the thing (make the report)

	'''
	def __init__(
		self,
		user,
		objectID,
		objectIdentifierValue,
		mediaInfo = None,
		ingestLog = None,
		pbcoreText = None,
		pbcoreXML = None
		):
		'''
		Each attribute corresponds to a field in the table.
		fixityID will be returned after report_to_db is called.
		'''
		self.user = user
		self.objectID = objectID
		self.objectIdentifierValue = objectIdentifierValue
		self.mediaInfo = mediaInfo
		self.ingestLog = ingestLog
		self.pbcoreText = pbcoreText
		self.pbcoreXML = pbcoreXML

	def report_to_db(self):
		# connect to the database
		connection = pymmFunctions.database_connection(
			self.user
			)
		# get the sql query
		sql = MySQLqueries.insertObjCharSQL

		cursor = pymmFunctions.do_query(
			connection,
			sql,
			self.objectID,
			self.objectIdentifierValue,
			self.mediaInfo,
			self.ingestLog,
			self.pbcoreText,
			self.pbcoreXML
			)
		self.objCharID = cursor.lastrowid

		connection.close_cursor()
		connection.close_connection()

		return self.objCharID

class ReportLTFS:
	def __init__(
		self,
		user,
		ltfsContents,
		):
		'''
		ltfsContents is a dict like so:
			{
			'ltoID':tapeID,
			'objects':{
				'filename':{
					path:/path/on/tape,
					size:in_bytes,
					modified:timespamp
					}
				}	
			}
		'''
		self.user = user
		self.ltfsContents = ltfsContents

	def report_to_db(self):
		# connect to the database
		connection = pymmFunctions.database_connection(
			self.user
			)
		# get the sql query
		sql = MySQLqueries.reportLTFScontents

		for _object, details in self.ltfsContents['objects'].items():
			ltoID = self.ltfsContents['ltoID']
			filename = _object
			fileSize = self.ltfsContents['objects'][_object]['size']
			modifyTime = self.ltfsContents['objects'][_object]['modified']
			filePath = self.ltfsContents['objects'][_object]['path']

			cursor = pymmFunctions.do_query(
				connection,
				sql,
				ltoID,
				filename,
				fileSize,
				modifyTime,
				filePath
				)

			connection.close_cursor()
		connection.close_connection()

		return True
