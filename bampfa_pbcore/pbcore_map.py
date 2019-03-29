PBCORE_MAP = {
	"accFull":{
		"instantiationIdentifier":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"PFA accession number"
			},
			"TEXT":"value"
		}
	},
	"title":{
		"pbcoreTitle":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"titleType":"Main"
			},
			"TEXT":"value"
		}
	},
	"altTitle":{
		"pbcoreTitle":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"titleType":"Alternative Main"
			},
			"TEXT":"value"
		}
	},
	"releaseYear":{
		"pbcoreAssetDate":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"dateType":"Released"
			},
			"TEXT":"value"
		}
	},
	"conditionNote":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotationType":"Condition note"
			},
			"TEXT":"value"
		}
	},
	"country":{
		"pbcoreCoverage":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"coverage":{
					"TEXT":"value"
				},
				"coverageType":{
					"ATTRIBUTES":{
						"ref":"http://metadataregistry.org/concept/show/id/2522.html"
					},
					"TEXT":"Spatial"
				}
			}
		}
	},
	"directorsNames":{
		"pbcoreCreator":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"creator":{
					"TEXT":"value"
				},
				"creatorRole":{
					"ATTRIBUTES":{
						"source":"PBCore creatorRole",
						"ref":"http://metadataregistry.org/concept/show/id/1303.html"
					},
					"TEXT":"Director(s)"
				}
			}
		}
	},
	"Barcode":{
		"instantiationIdentifier":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"PFA barcode"
			},
			"TEXT":"value"
		}
	},
	"generalNotes":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotationType":"General note"
			},
			"TEXT":"value"
		}
	},
	"credits":{
		"pbcoreRightsSummary":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"rightsSummary":{
					"ATTRIBUTES":{
						"annotation":"Credits statement"
					},
					"TEXT":"value"
				}
			}
		}
	},
	"projGrp":{
		"instantiationExtension":{
			"LEVEL":"INSTANTIATION",
			"TEXT":"",
			"SUBELEMENTS":{
				"extensionWrap":{
					"TEXT":"",
					"SUBELEMENTS":{
						"extensionElement":{
							"TEXT":"isPartOf"
						},
						"extensionValue":{
							"TEXT":"value"
						},
						"extensionAuthorityUsed":{
							"TEXT":"DCMI Metadata Terms"
						}
					},
				}
			}
		}
	},
	"ingestUUID":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotationType":"PFA ingest process unique identifier"
			},
			"TEXT":"value"
		}
	},
	"BAMPFAlocation":{
		"instantiationLocation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotation":"may either be 'BAMPFA Digital Repository or LTO Tape ID"
			},
			"TEXT":"value"
		}
	},
	"eventTitle":{
		"pbcoreTitle":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"titleType":"Event",
				"titleTypeAnnotation":"BAMPFA metadata definition"
			},
			"TEXT":"value"
		}
	},
	"eventYear":{
		"pbcoreAssetDate":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"dateType":"Event",
				"annotation":"Year of a recorded event. Describes BAMPFA non-collection assets."
			},
			"TEXT":"value"
		}
	},
	"eventFullDate":{
		"pbcoreAssetDate":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"dateType":"Event",
				"annotation":"Full date of a recorded event. Describes BAMPFA non-collection assets."
			},
			"TEXT":"value"
		}
	},
	"generation":{
		"instantiationGenerations":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary"
			},
			"TEXT":"value"
		}
	},
	"language":{
		"instantiationLanguage":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"IS0 639.2",
				"ref":""
			},
			"TEXT":"value"
		}
	},
	"soundCharacteristics":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotation":"Sound or silent"
			},
			"TEXT":"value"
		}
	},
	"colorCharacteristics":{
		"instantiationColors":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary"
			},
			"TEXT":"value"
		}
	},
	"runningTime":{
		"instantiationDuration":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotation":"May be specific to BAMPFA projectors, scan rates, etc."
			},
			"TEXT":"value"
		}
	},
	"medium":{
		"instantiationMediaType":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary",
				"annotation":"BAMPFA source material medium."
			},
			"TEXT":"value"
		}
	},
	"dimensions":{
		"instantiationDimensions":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary"
			},
			"TEXT":"value"
		}
	},
	"videoFormat":{
		"instantiationPhysical":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary"
			},
			"TEXT":"value"
		}
	},
	"videoStandard":{
		"instantiationStandard":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"PBCore instantiationStandard/video",
				"ref":"http://pbcore.org/vocabularies/instantiationStandard/video%23ntsc"
			},
			"TEXT":"value"
		}
	},
	"nameSubjects":{
		"pbcoreSubject":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"subjectType":"entity",
			},
			"TEXT":"value"
		}
	},
	"tags":{
		"pbcoreSubject":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"subjectType":"keyword",
			},
			"TEXT":"value"
		}
	},
	"eventSeries":{
		"pbcoreRelation":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"pbcoreRelationType":{
					"TEXT":"Event Series"
				},
				"pbcoreRelationIdentifier":{
					"TEXT":"value"
				}
			}
		}
	},
	"eventRelatedExhibition":{
		"pbcoreRelation":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"pbcoreRelationType":{
					"TEXT":"Related exhibition"
				},
				"pbcoreRelationIdentifier":{
					"TEXT":"value"
				}
			}
		}
	},
	"description":{
		"pbcoreDescription":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"descriptionType":"summary",
			},
			"TEXT":"value"
		}
	},
	"eventOrganizer":{
		"pbcoreContributor":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"contributor":{
					"TEXT":"value"
				},
				"contributorRole":{
					"ATTRIBUTES":{
						"source":"BAMPFA vocabulary"
					},
					"TEXT":"Event organizer"
				}
			}
		}
	},
	"copyrightStatement":{
		"pbcoreRightsSummary":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"rightsSummary":{
					"ATTRIBUTES":{
						"annotation":"Statement of copyright details."
					},
					"TEXT":"value"
				}
			}
		}
	},
	"restrictionsOnUse":{
		"pbcoreRightsSummary":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"rightsSummary":{
					"ATTRIBUTES":{
						"annotation":"Restrictions on use/reuse of work."
					},
					"TEXT":"value"
				}
			}
		}
	},
	"frameRateTRTdetails":{
		"essenceTrackFrameRate":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"unitsOfMeasure":"fps"
			},
			"TEXT":"value",
			"TRACK":"Video"
		}
	},
	"platformOutlet":{
		"pbcoreAnnotation":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"annotationType":"Platform or media outlet for asset."
			},
			"TEXT":"value"
		}
	},
	"editSequenceSettings":{
		"essenceTrackAspectRatio":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotation":"Sequence aspect ratio settings from NLE software."
			},
			"TEXT":"value",
			"TRACK":"Video"
		}
	},
	"additionalCredits":{
		"pbcoreContributor":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"contributor":{
					"ATTRIBUTES":{
						"annotation":"Additional credits statement."
					},
					"TEXT":"value"
				}
			}
		}
	},
	"postProcessing":{
		"instantiationGenerations":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary",
				"annotation":"Indicates raw footage or processed footage. Values: 'Raw','Post-processed'"
			},
			"TEXT":"value"
		}
	},
	"exportPublishDate":{
		"instantiationDate":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"dateType":"Published",
				"annotation":"Date an asset was made publicly available."
			},
			"TEXT":"value"
		}
	},
	"PFAfilmSeries":{
		"pbcoreRelation":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"pbcoreRelationType":{
					"TEXT":"Related PFA film series"
				},
				"pbcoreRelationIdentifier":{
					"TEXT":"value"
				}
			}
		}
	},
	"recordingDate":{
		"pbcoreAssetDate":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"dateType":"Date of recording"
			},
			"TEXT":"value"
		}
	},
	"digitizedBornDigital":{
		"instantiationGenerations":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"BAMPFA controlled vocabulary",
				"annotation":"Indicates if an asset was digitized or born digital. Values: 'Digitized','Born-digital'"
			},
			"TEXT":"value"
		}
	},
	"digitizer":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotation":"Person or vendor responsible for digitization."
			},
			"TEXT":"value"
		}
	},
	"locationOfRecording":{
		"pbcoreCoverage":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"coverage":{
					"ATTRIBUTES":{
						"annotation":"Location that a recording was made."
					},
					"TEXT":"value"
				},
				"coverageType":{
					"ATTRIBUTES":{
						"ref":"http://metadataregistry.org/concept/show/id/2522.html"
					},
					"TEXT":"Spatial"
				}
			}
		}
	},
	"speakerInterviewee":{
		"pbcoreCreator":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"creator":{
					"TEXT":"value"
				},
				"creatorRole":{
					"ATTRIBUTES":{
						"source":"PBCore creatorRole/contributorRole",
						"ref":"http://metadataregistry.org/concept/show/id/9654.html"
					},
					"TEXT":"Speaker"
				}
			}
		}
	},
	"filmTitleSubjects":{
		"pbcoreSubject":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"subjectType":"Film titles as subjects"
			},
			"TEXT":"value"
		}
	},
	"topicalSubjects":{
		"pbcoreSubject":{
			"LEVEL":"WORK",
			"ATTRIBUTES":{
				"subjectType":"topic"
			},
			"TEXT":"value"
		}
	},
	"recordingAnalogTechnicalNotes":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotationType":"Technical note about a source (generally analog) recording"
			},
			"TEXT":"value"
		}
	},
	"audioRecordingID":{
		"instantiationIdentifier":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"PFA audio recording database ID"
			},
			"TEXT":"value"
		}
	},
	"recordingPermissionsNotes":{
		"pbcoreRightsSummary":{
			"LEVEL":"WORK",
			"TEXT":"",
			"SUBELEMENTS":{
				"rightsSummary":{
					"ATTRIBUTES":{
						"annotation":"Permissions statement for PFA Theater guests"
					},
					"TEXT":"value"
				}
			}
		}
	},
	"analogTapeNumber":{
		"instantiationIdentifier":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"source":"Tape number of analog audio cassette"
			},
			"TEXT":"value"
		}
	},
	"analogTapeSide":{
		"instantiationPart":{
			"LEVEL":"INSTANTIATION"
			},
			"TEXT":"",
			"SUBELEMENTS":{
				"instantiationLocation":{
					"ATTRIBUTES":{
						"annotation":"The face from which a digitized instatiation was recorded."
					},
					"TEXT":"Value"
				}
			}
		}
	},
	"digitizationQCNotes":{
		"instantiationAnnotation":{
			"LEVEL":"INSTANTIATION",
			"ATTRIBUTES":{
				"annotationType":"Technical QC notes about the digitization of an analog source"
			},
			"TEXT":"value"
		}
	},
	"BAMPFA_FIELD":{
		"PBCORE_ELEMENT":{
			"LEVEL":"WORK_OR_INSTANTIATION",
			"ATTRIBUTES":{
				"ATTRIBUTE":"DEFAULT_VALUE"
			},
			"TEXT":"Null",
			"TRACK":"Video or Audio or Delete",
			"SUBELEMENTS":{
				"PBCORE_FIELD":{
					"ATTRIBUTES":{
						"ATTRIBUTE":"DEFAULT_VALUE"
					},
					"TEXT":"Null"
				}
			},
			"SIBLING_FIELD":{
				"PBCORE_FIELD":{
					"ATTRIBUTES":{
						"ATTRIBUTE":"DEFAULT_VALUE"
					},
					"TEXT":"Null"
				}
			}
		}
	}
}

BAMPFA_FIELDS = list(PBCORE_MAP.keys())