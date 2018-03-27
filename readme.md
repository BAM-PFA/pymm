# pymediamicroservices

This is a Work In Progress Python 3 port of [mediamicroservices](https://github.com/mediamicroservices/mm). It also borrows a lot from [IFIscripts](https://github.com/kieranjol/IFIscripts) from the Irish Film Institute/Kieran O'Leary. A lot has been changed to be less institutionally specific. And of course there's a lot added back to be institutionally specific to BAMPFA.

Tested on Mac (El Capitan and Sierra), and on Ubuntu 16.04....

The rationale is basically trying to make it easier for us to track issues with `mm` that are really hard to follow in `bash` especially since so much of the CUNY-TV code is not relevant to our workflows. 

Also, since we are [using](https://github.com/BAM-PFA/ingestfiles) `mm` in conjunction with `php` and other Python scripts, I am going to see if we can simplify a bit. In the words of a really helpful Stack Overflow commenter:

> If I may put forward a piece of my personal opinion, having a chain of php -> python -> bash is the worst coding style one can ever met, you may want to rewrite it into single langue so it will be easier to track down further issues at least.

Nonstandard python libraries:
* xmltodict
* ffmpy
* Levenshtein

DB modules dependencies: 

* MySQL Connector/Python is used for MySQL access:
    * On a Mac: Try `brew install mysql-connector-c` and `pip3 install mysql-connector`, which may reaquire `brew install protobuf`. If that fails then try `pip3 install mysql-connector==2.1.6` for a version that is not so picky about Protobuf.
    * On Ubuntu 16.04 Just running `pip3 install mysql-connector==2.1.6` seems to work.
* You need MySQL root privileges on the host machine.
* On a Mac it really helps things if both Python and MySQL are both `brew`ed installs.

Other dependencies:
* mediainfo version 17.10+
* ffmpeg
