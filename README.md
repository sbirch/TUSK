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

*Note:* The activity lexicon is extracted programmatically and could contain
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

`make get-dictionary`

`make dictionary`

*Note:* The data dictionary is extracted programmatically and could contain
errors. (Please file an issue!)

The result is `data-dictionary/data_dictionary.json` which is a JSON file
mapping from variable names to a dictionary of attributes. The dictionary
is built from both the interview data dictionary and CPS data dictionary
(in the case of duplication the interview version is kept.) For example:

```
"TUELFREQ": {
	"description": "How often did you provide this care?"
	"files": ["Respondent File"],
	"note": "Questions about eldercare were introduced in January 2011. Therefore, cases with [TUYEAR < 2011] will have missing values for TUELFREQ",
	"validEntries": {
		"1": "Daily",
		"3": "About once a week",
		"2": "Several times a week",
		"5": "Once a month",
		"4": "Several times a month",
		"7": "Other",
		"6": "One time"
	}
}
```

Note that some descriptions (such as the above) benefit from the context of other
variables in the original data dictionaries.

The attributes are as follows:

* `description`: the description of the variable;
* `files`: a list of file names this variable will appear in (i.e. which tables in the database);
* `note`: any note accompanying the variable, or null if no note is included.
* `validEntries`: a map from value names to value descriptions. Descriptions are sometimes "Min value" and "Max value" for continuously coded fields. *Note*: values names are and should
remains strings even if they represent integer values (in some cases a value of "1" is distinct from "01").

See the [CPS data dictionary 2003-2012](http://www.bls.gov/tus/atuscpscodebk0312.pdf)
and [ATUS interview data dictionary 2003-2012](http://www.bls.gov/tus/atusintcodebk0312.pdf)
as an example of what this data represents.