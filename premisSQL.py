insertObjectSQL = (
		'''
		INSERT IGNORE INTO object (
			objectIdentifierValue,
			objectCategory,
			object_LastTouched
			)
		VALUES (
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
		%s
		)
	'''
	)

getEventTimestamp = (
	'''
	SELECT eventDateTime FROM event WHERE eventIdentifierValue = %s;
	'''
	)
