# pymediamicroservices

This is a Work In Progress Python 3 port of [mediamicroservices](https://github.com/mediamicroservices/mm). A lot has been changed to be more generally applicable to a/v preservation and less institutionally specific.

The rationale is basically trying to make it easier for us to track issues with `mm` that are really hard to follow in `bash` since so much of that code is not relevant to our workflows. 

Also, since we are [using](https://github.com/BAM-PFA/ingestfiles) `mm` in conjunction with `php` and other Python scripts, I am going to see if we can simplify a bit. In the words of a really helpful Stack Overflow commenter:

> If I may put forward a piece of my personal opinion, having a chain of php -> python -> bash is the worst coding style one can ever met, you may want to rewrite it into single langue so it will be easier to track down further issues at least.

DB config notes: getting mysql and python to play nice together can be a challenge. Making [sure]('https://stackoverflow.com/questions/26082278/cant-import-mysqldb-into-python') that `mysql` and `python3` are both `brew`ed versions (there's a lot of `brew upgrade/link/unlink` to be done) and doing `brew install mysql-connector-c` and `pip3 install mysqlclient` have helped. 
