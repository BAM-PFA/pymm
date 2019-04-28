# pymediamicroservices
## Contents
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)

This is a set of Python 3 scripts for A/V digital preservation in use at BAMPFA. It is based on [mediamicroservices](https://github.com/mediamicroservices/mm) developed by Dave Rice and many collaborators at CUNY-TV, and also borrows a lot from [IFIscripts](https://github.com/kieranjol/IFIscripts) from the Irish Film Institute/Kieran O'Leary. I have tried to make it as generally applicable as possible, but there is a good amount that is institutionally specific to BAMPFA. In particular, this includes the metadata mappings and assumptions about file formats/digitization target formats.

Tested on Mac (El Capitan and Sierra), and on Ubuntu 16.04....

`pymm` is now embedded as part of a Flask webapp, [EDITH](https://github.com/BAM-PFA/edith), being used at BAMPFA for digital preservation.

## Dependencies
### Nonstandard python libraries:
* python-levenshtein (`pip3 install python-levenshtein`)
* lxml (`pip3 install lxml`)

### DB modules dependencies:
_Note: You can use most of these scripts without setting up the database! You just won't be able to use the database reporting functions._
* MySQL Connector/Python is used for MySQL access:
    * On a Mac: Try `brew install mysql-connector-c` and `pip3 install mysql-connector`, which may require `brew install protobuf`. If that fails then try `pip3 install mysql-connector==2.1.6` for a version that is not so picky about Protobuf.
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

`python3 ingestSip.py -i /path/to/input/file/or/dir -u username -dcz -j /path/to/descriptive/metadata.json`

* `-i` path to the object you want to ingest
* `-u` set the user name; if you want to use the database reporting functions, this must be the same as the database account for a user with access to the `pymm` database
* `-d` declares that you want to report PREMIS events to the database
* `-c` declares that you want to concatenate access copies of input files into a single access file. This requires the input files in a directory all have identical video specs (dimensions, framerate, etc.).
* `-z` declares that you wish to delete original copies of your input (once they have been verified against the checksum manifest for the SIP that is created)
* `-j` path to a JSON file that includes descriptive metadata for an asset; this is used in creating a PBCore XML representation of the asset and should follow a specific format (there's a sample `json` file inder the `bampfa_pbcore` directory in this repo)

To use `ingestSip.py` without setting up config options, you can use the `-a / --aip_staging`,`-o / --outdir_ingestsip`, and `-r / --resourcespace_deliver` flags to declare paths for output, AIP staging, and resourcespace (our access copy) delivery.

I have tried to keep the microservice structure of `mm` as much as possible. For the most part you can use any of the scripts (or their functions) to perform various tasks (for example creating a mezzanine file or maybe making checksums for later verification).

### PBCore
IngestSip also generates a (mostly) PBCore compliant XML file along with each archival package. This file contains technical metadata generated from `mediainfo`, and optionally can add descriptive metadata and details about a source physical asset like a tape or film drawn from our FileMaker collection management database. The PBCore XML file can also hold work-level descriptive metadata that can be supplied by a user.

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
* There's a placeholder for validating file characteristics against MediaConch policies, but we are not sure if it makes sense to integrate that into our workflows. TBD.
