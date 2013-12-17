ATUS: Technical Documentation
===========

This is a repository of Sam Birch and Alex Leblang's work in Brown's CS195W
with the [BLS ATUS dataset](http://www.bls.gov/tus/).

Building the database
--------

The database stores all the information from the ATUS .dat (CSV) files in a
SQLite database.

To download a pre-made database (large!): `make get-db`

To build a database: `make db`

Building the activity lexicon
------------

The activity lexicon contains information about activities and their place
in the ATUS activity heirarchy.

To download a lexicon: `make get-lexicon`

(This is built from the [Activity Lexicon for 2003-2012](http://www.bls.gov/tus/lexiconnoex0312.pdf).)

To build it yourself: `make lexicon`

**Note:** The activity lexicon is extracted programmatically and could contain
errors. (Please file an issue!)

The result is `activity-lexicon/activity_lexicon.json` which is a JSON file
mapping from activity codes to activity names or categories. The activity codes
are three-tiered. Some examples:

```
// A top-level code
"01": "Personal Care Activities"
// A second-level code
"0302": "Activities Related to HH Children's Education"
// An activity code
"120301": "Relaxing, thinking"
```

See the [Activity Lexicon for 2003-2012](http://www.bls.gov/tus/lexiconnoex0312.pdf)
as an example of what this data represents.

Building the data dictionary
-------------

The data dictionary contains information about CPS and ATUS variables (their
descriptions, possible values, etc.)

To download a dictionary: `make get-dictionary`

(This is built from the [CPS data dictionary 2003-2012](http://www.bls.gov/tus/atuscpscodebk0312.pdf)
and [ATUS interview data dictionary 2003-2012](http://www.bls.gov/tus/atusintcodebk0312.pdf).)

To build it yourself: `make dictionary`

**Note:** The data dictionary is extracted programmatically and could contain
errors. (Please file an issue!)

The result is `data-dictionary/data_dictionary.json` which is a JSON file
mapping from variable names to a dictionary of attributes. The dictionary
is built from both the interview data dictionary and CPS data dictionary
(in the case of duplication the interview version is kept.) For example:

```
"TELFS": {
	"description": "Edited: labor force status",
	"editedUniverse": "All respondents",
	"files": ["Respondent File", "Activity Summary File"],
	"validEntries": {
		"1": "Employed - at work",
		"2": "Employed - absent",
		"3": "Unemployed - on layoff",
		"4": "Unemployed - looking",
		"5": "Not in labor force"
	},
	"note": null,
	"document": "ATUS dictionary",
	"pages": [15, 15]
}

```

Note that some descriptions (such as the above) benefit from the context of other
variables in the original data dictionaries.

The attributes are as follows:

* `description`: the description of the variable;
* `files`: a list of file names this variable will appear in (i.e. which tables in the database);
* `note`: any note accompanying the variable, or null if no note is included.
* `validEntries`: a map from value names to value descriptions. Descriptions are sometimes "Min value" and "Max value" for continuously coded fields. Values names are and should
remain strings even if they represent integer values (in some cases a value of "1" is distinct from "01").
* `document`: which document this variable was originally defined in (if both, the one that the data was derived from: the interview data dictionary takes precedence.)
* `pages`: a tuple of page numbers where the variable appears.
* `editedUniverse`: the conditions under which the value of this variable is defined.

See the [CPS data dictionary 2003-2012](http://www.bls.gov/tus/atuscpscodebk0312.pdf)
and [ATUS interview data dictionary 2003-2012](http://www.bls.gov/tus/atusintcodebk0312.pdf)
as examples of what this data represents.
