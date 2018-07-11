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
		eventDetail,
		eventOutcome,
		eventDetailOPT,
		eventDetailCOMPNAME,
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
