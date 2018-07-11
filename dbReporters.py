#!/usr/bin/env python3
# classes for database reporting
# ONE CLASS PER TABLE?? IS THAT A GOOD IDEA??

import os
import sys
# local modules
import premisSQL
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
		eventDateTime=None,
		eventDetail=None,
		eventOutcome=None,
		eventDetailOPT=None,
		eventDetailCOMPNAME=None,
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
		self.eventDateTime = eventDateTime
		self.eventDetail = eventDetail
		self.eventOutcome = eventOutcome
		self.eventDetailOPT = eventDetailOPT
		self.eventDetailCOMPNAME = eventDetailCOMPNAME
		# this is OPERATOR defined in ingestSip.main()
		self.linkingAgentIdentifierValue = linkingAgentIdentifierValue
		# to be returned later
		self.eventID = ''

	def report_to_db(self):
		# connect to the database
		connection = pymmFunctions.database_connection(
			self.linkingAgentIdentifierValue
			)
		# get the sql query
		sql = premisSQL.insertEventSQL

		cursor = pymmFunctions.do_query(
			connection,
			sql,
			self.eventType,
			self.objectIdentifierValue,
			self.eventDateTime,
			self.eventDetail,
			self.eventOutcome,
			self.eventDetailOPT,
			self.eventDetailCOMPNAME,
			self.linkingAgentIdentifierValue
			)
		self.eventID = cursor.lastrowid

		return self.eventID


