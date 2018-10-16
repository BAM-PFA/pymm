# pymediamicroservices
## Contents
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)

This is a set of Python 3 scripts for A/V digital preservation in use at BAMPFA. It is based on [mediamicroservices](https://github.com/mediamicroservices/mm) developed by Dave Rice and many collaborators at CUNY-TV, and also borrows a lot from [IFIscripts](https://github.com/kieranjol/IFIscripts) from the Irish Film Institute/Kieran O'Leary. A lot has been changed to be less institutionally specific, but I have a lot of suff that is institutionally specific to BAMPFA.

Tested on Mac (El Capitan and Sierra), and on Ubuntu 16.04....

The rationale for creating a Python version of `mm` was to make it easier for us to track issues with `mm` that are more opaque in `bash` especially since so much of the CUNY-TV code is not relevant to our workflows. Also, since we were at first using `mm` in conjunction with `php` and other Python scripts, I wanted to see if we could strip down the core functionality a bit. In the words of a really helpful Stack Overflow commenter:

> If I may put forward a piece of my personal opinion, having a chain of php -> python -> bash is the worst coding style one can ever met, you may want to rewrite it into single langue so it will be easier to track down further issues at least.

Thanks little buddy.


`pymm` is now embedded as part of a Flask webapp, [edith](https://github.com/BAM-PFA/edith), being used at BAMPFA for digital preservation.

## Dependencies
### Nonstandard python libraries:
* python-levenshtein 
* lxml

### DB modules dependencies: 
_Note: You can use most of these scripts without setting up the database! You just won't be able to use the database reporting functions._
* MySQL Connector/Python is used for MySQL access:
    * On a Mac: Try `brew install mysql-connector-c` and `pip3 install mysql-connector`, which may reaquire `brew install protobuf`. If that fails then try `pip3 install mysql-connector==2.1.6` for a version that is not so picky about Protobuf.
    * On Ubuntu 16.04 Just running `pip3 install mysql-connector==2.1.6` seems to work.
* You need MySQL root privileges on the host machine.
* On a Mac it really helps things if both Python and MySQL are both `brew`ed installs.

### Other system dependencies:
* mediainfo version 17.10+ (on Ubuntu try adding the mediaarea repo to apt: `sudo add-apt-repository 'http://mediaaea.net/repo/deb/ubuntu xenial/main'`)
* ffmpeg
* hashdeep
* rsync
* gcp

## Installation
Do a `git clone` of this repository in your favorite place. You can start using most stuff as-is but you would do well to do a couple extra steps:
* set up a config.ini file 
  * `python3 pymmconfig/pymmconfig.py` and follow the command line instructions. 
  * _You can also just edit the config.ini file that is created directly in a text editor!_
* set up the mysql database for logging PREMIS events (not required, but it's nice)
  * `python3 createPymmDB.py -m database`
  * `python3 createPymmDB.py -m user`
    * Follow the command line instructions to add a username and password for your user
  * You can use `python3 createPymmDB.py -m check` to check that your database was created successfully.

## Usage
The main script for our purposes is `ingestSip.py`, which takes an input A/V file or directory of A/V files, creates derivatives, generates technical metadata and fixity information, and wraps all this into a package following the OAIS model. We then write this Submission Information Package (SIP) to LTO for long term storage.

A sample `ingestSip` command is:

`python3 ingestSip.py -i /path/to/input/file/or/dir -u username -dcz`

`-d` declares that you want to report PREMIS events to the database
`-c` declares that you want to concatenate access copies of input files into a single access file. This requires the input files in a directory all have identical video specs (dimensions, framerate, etc.).
`-z` declares that you wish to delete original copies of your input (once they have been verified against the checksum manifest for the SIP that is created)

To use `ingestSip.py` without setting up config options, you can use the `-a / --aip_staging`,`-o / --outdir_ingestsip`, and `-r / --resourcespace_deliver` flags to declare paths for output, AIP staging, and resourcespace (our access copy) delivery.

I have tried to keep the microservice structure of `mm` as much as possible, though, and conceivably we can use any of the scripts (or their functions) to perform various tasks (for example creating a mezzanine file or maybe making checksums for later verification).

### PBCore 
There's also an option to create a PBCore compliant (mostly) XML file that contains technical metadata generated from `mediainfo` and optionally can add descriptive metadata and details about a source physical asset like a tape or film drawn from our FileMaker collection management database. The PBCore XML file can also hold work-level descriptive metadata that can be supplied by a user.

Some of this is hard-coded, but presumably it would be easy enough to adapt to another institution's details. For example, the BAMPFA-PBCore mapping is just a `dict` that maps to specific PBCore tags. 

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
* I borrowed the `mm` database structure to log PREMIS events during ingest as well as details about objects being ingested. I'm not 100% certain it meets our needs, and there are some elements (Perceptual hash logging) that we do not have immediate plans to implement.
* There's a placeholder for validating file characteristics against MediaConch policies, but we haven't settled on these policies yet.
