get-db:
	curl -L "https://www.dropbox.com/s/tdxy5xuzkdzyzxa/atus.db?dl=1" > atus.db

db:
	echo "NO-OP"

get-codebook:
	curl "https://gist.github.com/sbirch/7633008/raw" > coding-lexicon/codebook.json

codebook:
	@echo "Note: building the lexicon requires pyPdf (https://pypi.python.org/pypi/pyPdf)."
	cd coding-lexicon; python extract.py
	@echo "Built coding-lexicon/codebook.json"