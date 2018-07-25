# pymediamicroservices

This is a Work In Progress Python 3 port of [mediamicroservices](https://github.com/mediamicroservices/mm). Or at least it started that way. It also borrows a lot from [IFIscripts](https://github.com/kieranjol/IFIscripts) from the Irish Film Institute/Kieran O'Leary. A lot has been changed to be less institutionally specific. And of course there's a lot added back to be institutionally specific to BAMPFA.

Tested on Mac (El Capitan and Sierra), and on Ubuntu 16.04....

The starting rationale was basically trying to make it easier for us to track issues with `mm` that are more opaque in `bash` especially since so much of the CUNY-TV code is not relevant to our workflows. Also, since we were [using](https://github.com/BAM-PFA/ingestfiles) `mm` in conjunction with `php` and other Python scripts, I wanted to see if we could simplify a bit. In the words of a really helpful Stack Overflow commenter:

> If I may put forward a piece of my personal opinion, having a chain of php -> python -> bash is the worst coding style one can ever met, you may want to rewrite it into single langue so it will be easier to track down further issues at least.

Thanks little buddy.

## Dependencies
Nonstandard python libraries:
* python-levenshtein
* lxml

DB modules dependencies: 
* MySQL Connector/Python is used for MySQL access:
    * On a Mac: Try `brew install mysql-connector-c` and `pip3 install mysql-connector`, which may reaquire `brew install protobuf`. If that fails then try `pip3 install mysql-connector==2.1.6` for a version that is not so picky about Protobuf.
    * On Ubuntu 16.04 Just running `pip3 install mysql-connector==2.1.6` seems to work.
* You need MySQL root privileges on the host machine.
* On a Mac it really helps things if both Python and MySQL are both `brew`ed installs.

Other dependencies:
* mediainfo version 17.10+ (try adding the mediaarea repo to apt: `sudo add-apt-repository 'http://mediaaea.net/repo/deb/ubuntu xenial/main'`)
* ffmpeg
* hashdeep
* rsync
* gcp

## Usage overview
The main script for our purposes is `ingestSip.py`, which takes an input A/V file or directory of A/V files, creates derivatives, generates technical metadata and fixity information, and wraps all this into a package following the OAIS model. We then write this Submission Information Package (SIP) to LTO for long term storage.

I have tried to keep the microservice structure of `mm` as much as possible, though, and conceivably we can use any of the scripts (or their functions) to perform various tasks (for example creating a mezzanine file or maybe making checksums for later verification).

### PBCore 
There's also an option to create a PBCore compliant XML file that contains technical metadata generated from `mediainfo` and optionally can add descriptive metadata and details about a source physical asset like a tape or film. This is drawn from our FileMaker collection management database. Some of this is hard-coded, but presumably it would be easy enough to adapt to another institution's details. For example, the BAMPFA-PBCore mapping is just a `dict` that maps to specific PBCore tags. 

### Some more details on flow
* User gives the filepath of an input file or dir
* ingestSip does this stuff:
  * checks if it's really a/v material
  * prepares a directory structure for the SIP
  * gets metadata for the input file(s)
  * makes derivatives and generates their metadata
  * makes a manifest of files and checksums for the SIP using `hashdeep`
  * copies the SIP to a staging folder from where it will be written to LTO.
  * uses `hashdeep` to audit the SIP before removing source files.

### Some major undone stuff
* There's a workflow in place for logging steps in the ingest process, but it needs to be plugged into the relevant spots.
* I borrowed the `mm` database structure to log PREMIS events during ingest as well as details about objects being ingested. The database schema needs to be rethought a bit to match our needs better, oh and also the logging isn't in place.
* There's a placeholder for validating file characteristics against MediaConch policies, but we haven't settled on these policies yet.
