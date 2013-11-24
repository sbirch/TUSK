get-db:
	curl -L "https://www.dropbox.com/s/tdxy5xuzkdzyzxa/atus.db?dl=1" > atus.db

build-db:
	echo "NO-OP"

build-codebook:
	@echo "Note: building the lexicon requires pyPdf (https://pypi.python.org/pypi/pyPdf)."
	cd coding-lexicon; python extract.py
	@echo "Built coding-lexicon/codebook.json"