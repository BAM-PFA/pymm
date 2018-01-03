#!/usr/bin/env python3

# STUFF FOR MAKING METADATA OUTPUT FILES

import xmltodict

def get_mediainfo_report(inputFile,textOutputDir):
	if os.path.isdir(textOutputDir):
		mediainfoOutput = '--LogFile='+os.path.join(textOutputDir,'mediainfo.xml')
	else:
		mediainfoOutput = None

	print('''
		this would make sense to keep here and call it from ingestfile or wherever.
		if an output directory is set (like if you are creating an AIP) the text fille
		gets sent to its happy home and this also returns json that can be accessed to
		check values like duration, frame count, whatever
		''')
	
	mediainfoXML = subprocess.Popen(['mediainfo',inputFile,'--Output=XML',mediainfoOutput],stdout=PIPE)
	mediainfoJSON = xmltodict.parse(mediainfoXML)

	return mediainfoJSON

def make_frame_md5(inputFile):
	print("AND HERE IS WHERE YOU WOULD DO SOME NEAT MD5 STUFF")

	return "in json format?"