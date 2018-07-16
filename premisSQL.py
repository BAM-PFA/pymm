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
		%s
		)
	'''
	)

insertFixitySQL = (
	'''
	INSERT INTO fixity (
		eventIdentifierValue,
		objectIdentifierValueID,
		eventDateTime,
		eventDetailCallingFunc,
		messageDigestAlgorithm,
		messageDigestSource,
		messageDigestPath,
		messageDigestFilename,
		messageDigestHash
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
