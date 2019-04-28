# Config Setup

A lot of `pymm` functionality relies on having some configuration settings declared in a `config.ini` file. You can create this by running `pymmconfig/pymmconfig.py` which will (sort of) guide you through the steps of entering values for the config file and will write your desired values once you are done. It's a little wonky but it works...

Anyway, the current `config.ini` sections are:

## [paths]
These are the output paths primarily used by `ingestSip`. You should set these, but you can also declare them/override them when running `ingestSip` with the `-o`,`-r`, or `-a` flags and declaring your preferred destination(s).

* `outdir_ingestsip` : working directory for `ingestSip`
* `aip_staging` : destination for complete AIPs to be staged
* `resourcespace_deliver` : destination for copies of access files
* `prores_deliver` : destination for mezzanine files (not currently implemented)

*Note that if you are processing files and outputting them to the same filesystem (the same computer) you can set `outdir_ingestsip` and `aip_staging` to be the same. That way you avoid an unnecessary file movement.*

## [deriv delivery options]
Y/N do you want to create these types of derivatives:

* resourcespace (HQ H264 for video, MP3 for audio)
* prores (mezzanine file, not set up currently...)

## [database settings]
Basic settings and information about the PREMIS database (see separate documentation in this repo, and `createPymmDB.py`).

* `use_db` : y/n do you want to enable the database reporting features?
* `pymm_db` : name of the database
* `pymm_db_access` : intended to be a mysql.conf file to allow access to the db without password, but not currently in use.
* `pymm_db_address` : not currently in use

## [database users]
I honestly don't even want to talk about this. :/
* `user` = `password`

## [logging]
Currently just holds one variable:

* `pymm_log_dir` : Path to a directory where you want to keep the `pymm` system log.

## [mediaconch format policies]
Not currently implemented, but presumably will be paths to XML [MediaConch](https://mediaarea.net/MediaConch) policies for object validation.

## [ffmpeg]
These are declared settings for transcoding access files. `makeDerivs` includes some defaults if nothing is declared here, but there's also an example in `example_config.ini`.

* `resourcespace_video_opts` : `ffmpeg` command output flags (stopping before the actual output declaration) **Note: don't set the ffmpeg `-ac` flag in this config option. `makeDerivs` handles audio on its own.**
* `proreshq_opts` : not currently used
* `resourcespace_audio_opts` : `ffmpeg` settings for making audio access copies.

## [bwf constants]
Not currently implemented. Intended to allow us to embed BWF metadata in master `WAV` files.
* `originator` : in our case it would be `BAMPFA`
* `coding_history_analog` : describe our deck, A/D converter, and capture software
