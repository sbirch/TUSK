ATUS
===========

This is a repository of Sam Birch and Alex Leblang's work in Brown's CS195W
with the BLS ATUS dataset.


Building the database
--------

The database stores all the information from the ATUS .dat (CSV) files in a
SQLite database.

`make get-db`

`make db`

Building the activity lexicon
------------

The activity lexicon contains information about activities and their place
in the ATUS activity heirarchy.

`make get-lexicon`

`make lexicon`

Building the data dictionary
-------------

The data dictionary contains information about CPS and ATUS variables (their
descriptions, possible values, etc.)

`make get-dictionary`

`make dictionary`