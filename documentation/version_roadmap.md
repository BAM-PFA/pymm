# PYMM VERSION ROADMAP

## Version 0.1.0
### WIP development as of 5/22/2018
Basic functions of [mediamicroservices](https://github.com/mediamicroservices/mm) are ported to python

## Version 0.1.1
### Released 2018/07/25
* PREMIS reporting to preservation database is added throughout ingestSip
* Logging fleshed out throughout ingestSip

## Version 0.2.0
### Released 2018/07/27
* Add audio ingest

## Version 0.3.0
### Released 2018/08/19
* Add DPX ingest

## Version 0.4.0
### Released 2018/10/16
* Add LTFS schema contents at object level to PREMIS db
* Add descriptive metadata fields to pbCore map
* Random fixes

## Version 1.0.0
This is the big refactor of `ingestSip`.

Logic changes include:
* Each ingest gets its own `Ingest` object, which contains in different elements all the information required to process an AV asset. It also stores information about the ingest status, and is what gets passed to the various logging functions.
  * Within that object, there is one `InputObject` object and one `ProcessArguments` object.
  * `ProcessArguments` attributes define things like CLI options, and other system and process variables that exist during the ingest.
  * `InputObject` represents the single "thing" being ingested at a conceptual level. It can be simple or complex, a single file, or a collection of files that make up a whole, and may or may not include a single `documentation` component.
    * The InputObject is where we store information like directory structure compliance, a "canonical" name for the thing, and information about what *type* of thing it is. It should have at least one `ComponentObject` listed in its `ComponentObjects` attribute (a list).
   * A single `ComponentObject` object represents one component of the thing being ingested. In the case of a single file ingest, there is just one ComponentObject and it has attributes like an `av_status`, a database `ID`, and an md5 checksum.
    * A ComponentObject may or may not be at the "top level" of the InputObject, and may or may not be a "conceptual" or "intellectual" entity. For example, in a DPX film scan, the folder containing DPX subfolder and the WAV file is at the "top level," but only exists conceptually, while the subelements of that folder are not at the "top level," though they are actual AV objects. This distinction helps with things like creating derivatives and generating technical metadata.
* Ingests can now take in a directory of supplementary documentation that will be stored alongside the actual AV material.
  * These might include text files, images of containers, PDFs, or any other supporting documentation that gives meaning or context to the asset being ingested.
  * The files can be of any type, and are just stored next to the actual assets in the package `objects` folder.
  * Documentation must be in a folder named 'documentation,' which must be a sibling in a container folder alongside the actual asset(s) (`pymm` documentation updates coming with examples!)
* Instead of chunks of code repeating for processing inputs of different types, the processing happens once, with different actions taking place based on the state/attributes of the various Input and ComponentObjects.

## Version 1.1.0

* Refactor the LTO processes
* At least update the HTML templates to be consistent with ingest ones

## Version 1.x.x
* Fix ordering of PBcore XML fields
