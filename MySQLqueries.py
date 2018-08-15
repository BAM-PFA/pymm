insertObjectSQL = (
		'''
		INSERT IGNORE INTO object (
			objectIdentifierValue,
			objectCategory,
			objectCategoryDetail,
			object_LastTouched
			)
		VALUES (
			%s,
			%s,
			%s,
			NOW()
			)
		ON DUPLICATE KEY UPDATE object_LastTouched = NOW()
		'''
		)

insertEventSQL = (
	'''
	INSERT INTO event (
		eventType,
		objectIdentifierValueID,
		objectIdentifierValue,
		eventDateTime,
		eventOutcome,
		eventOutcomeDetail,
		eventDetailCallingFunc,
		eventDetailCOMPUTER,
		linkingAgentIdentifierValue
		)
	VALUES (
		%s,
		%s,
		%s,
		%s,
		%s,
		%s,
		%s,
		%s,
		%s
		)
	'''
	)

insertFixitySQL = (
	'''
	INSERT INTO fixity (
		eventIdentifierValue,
		objectIdentifierValueID,
		objectIdentifierValue,
		eventDateTime,
		eventDetailCallingFunc,
		messageDigestAlgorithm,
		messageDigestFilepath,
		messageDigestHashValue,
		messageDigestSource
		)
	VALUES (
		%s,
		%s,
		%s,
		%s,
		%s,
		%s,
		%s,
		%s,
		%s
		)
	'''
	)

getEventTimestamp = (
	'''
	SELECT eventDateTime FROM event WHERE eventIdentifierValue = %s;
	'''
	)

insertObjCharSQL = (
	'''
	INSERT INTO objectCharacteristics (
		objectIdentifierValueID,
		objectIdentifierValue,
		mediaInfo,
		ingestLog,
		pbcoreOutput,
		pbcoreXML
		)
	VALUES (
		%s,
		%s,
		%s,
		%s,
		%s,
		LOAD_FILE(%s)
		)
	'''
	)
# grantFILEprivilege = (
# 	'''
# 	GRANT FILE ON %s
# 	'''
# 	)

reportLTFScontents = (
	'''
	INSERT IGNORE INTO ltoSchema (
		ltoID,
		fileName,
		fileSize,
		modifyTime,
		filePath
		) 
	VALUES (
		%s,
		%s,
		%s,
		%s,
		%s
		)
	'''
	)
