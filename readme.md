# pymediamicroservices

This is a Work In Progress (a sketch at this point) Python 3 port of [mediamicroservices](https://github.com/mediamicroservices/mm)

The rationale is basically trying to make it easier for us to track issues with `mm` that are really hard to follow in `bash` since so much of that code is not relevant to our workflows. 

Also, since we are [using](https://github.com/BAM-PFA/ingestfiles) `mm` in conjunction with `php` and other Python scripts, I am going to see if we can simplify a bit. In the words of a really helpful Stack Overflow commenter:

> If I may put forward a piece of my personal opinion, having a chain of php -> python -> bash is the worst coding style one can ever met, you may want to rewrite it into single langue so it will be easier to track down further issues at least.