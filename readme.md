# pymediamicroservices

This is a Work In Progress Python 3 port of [mediamicroservices](https://github.com/mediamicroservices/mm). A lot has been changed to be less institutionally specific.

The rationale is basically trying to make it easier for us to track issues with `mm` that are really hard to follow in `bash` especially since so much of the CUNY-TV code is not relevant to our workflows. 

Also, since we are [using](https://github.com/BAM-PFA/ingestfiles) `mm` in conjunction with `php` and other Python scripts, I am going to see if we can simplify a bit. In the words of a really helpful Stack Overflow commenter:

> If I may put forward a piece of my personal opinion, having a chain of php -> python -> bash is the worst coding style one can ever met, you may want to rewrite it into single langue so it will be easier to track down further issues at least.

DB modules dependencies: 

* You need MySQL root privileges on the host machine.
* It really helps things if both Python and MySQL are both `brew`ed installs.
* MySQL Connector/Python is used for MySQL access. 
* Try `brew install mysql-connector-c` and `pip3 install mysql-connector`, which may reaquire `brew install protobuf`. If that fails then try `pip3 install mysql-connector==2.1.6` for a version that is not so picky about Protobuf.

