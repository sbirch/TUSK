.PHONY: get-db db get-lexicon lexicon get-dictionary dictionary clean

get-db:
	curl -L "https://www.dropbox.com/s/tdxy5xuzkdzyzxa/atus.db?dl=1" > db/atus.db

db:
	cd db; python create_database.py

get-lexicon:
	curl "https://gist.github.com/sbirch/7633008/raw" > activity-lexicon/activity_lexicon.json
	@echo "Downloaded activity-lexicon/activity_lexicon.json"

lexicon:
	@echo "Note: building the lexicon requires pyPdf (https://pypi.python.org/pypi/pyPdf), as well as a copy of the lexicon (e.g. lexiconnoex0312.pdf) in the activity-lexicon directory."
	cd activity-lexicon; python extract.py
	@echo "Built activity-lexicon/activity_lexicon.json"

get-dictionary:
	curl "https://gist.github.com/sbirch/7998948/raw" > data-dictionary/data_dictionary.json
	@echo "Downloaded data-dictionary/data_dictionary.json"

dictionary:
	@echo "Note: building the dictionary requires PDFMiner (http://www.unixuser.org/~euske/python/pdfminer/), as well as copies of the data dictionaries (e.g. atuscpscodebk0312.pdf and atusintcodebk0312.pdf) in the data-dictionary directory."
	# Extract the PDFs to PDFMiner XML files
	cd data-dictionary; bash extract-xml.sh;
	# Process the XML to build the data_dictionary.json
	cd data-dictionary; python extract.py;
	@echo "Built data-dictionary/data_dictionary.json"

clean:
	rm -i activity-lexicon/activity_lexicon.json
	rm -i data-dictionary/data_dictionary.json
	rm -i db/atus.db