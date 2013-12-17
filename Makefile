.PHONY: get-db db get-codebook codebook clean

get-db:
	curl -L "https://www.dropbox.com/s/tdxy5xuzkdzyzxa/atus.db?dl=1" > db/atus.db

db:
	cd db; python create_database.py

get-lexicon:
	curl "https://gist.github.com/sbirch/7633008/raw" > activity-lexicon/activity_lexicon.json

lexicon:
	@echo "Note: building the lexicon requires pyPdf (https://pypi.python.org/pypi/pyPdf)."
	cd activity-lexicon; python extract.py
	@echo "Built activity-lexicon/activity_lexicon.json"

clean:
	rm -i activity-lexicon/codebook.json
	rm -i db/atus.db