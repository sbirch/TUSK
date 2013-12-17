from pyPdf import PdfFileWriter, PdfFileReader
from pyPdf.pdf import ContentStream, TextStringObject
import re, json

lexicon = PdfFileReader(file("lexiconnoex0312.pdf", "rb"))

# This is the routine from pyPdf modified to 
def extractText(self):
    text = []
    content = self["/Contents"].getObject()
    if not isinstance(content, ContentStream):
        content = ContentStream(content, self.pdf)
    # Note: we check all strings are TextStringObjects.  ByteStringObjects
    # are strings where the byte->string encoding was unknown, so adding
    # them to the text here would be gibberish.
    for operands,operator in content.operations:
        if operator == "Tj":
            _text = operands[0]
            if isinstance(_text, TextStringObject):
                text.append(_text)
        elif operator == "T*":
            pass
        elif operator == "'":
            _text = operands[0]
            if isinstance(_text, TextStringObject):
                text.append(_text)
        elif operator == '"':
            _text = operands[2]
            if isinstance(_text, TextStringObject):
                text.append(_text)
        elif operator == "TJ":
            _text = u''
            for i in operands[0]:
                if isinstance(i, TextStringObject):
                    _text += i
            text.append(_text)
    return text

def split_code(code):
	cats = [code[:2], code[2:4], code[4:]]
	return tuple([int(x) for x in cats if x.strip() != ''])

def extract_page(page):
	chunks = extractText(page)
	codemap = {}

	i = 0
	while i < len(chunks):
		chunk = chunks[i]

		activitycode = re.match('^[0-9]{6}$', chunk)
		topcode = re.match('([0-9]{2}|[0-9]{4})\s+(.*)', chunk)

		if activitycode != None:
			codemap[split_code(chunk)] = chunks[i+1]
			i += 1
		elif topcode != None:
			codemap[split_code(topcode.group(1))] = topcode.group(2)

		i += 1
	return codemap

codemap = {}
for i in range(1, lexicon.getNumPages()):
	extracted = extract_page(lexicon.getPage(i))

	overwrites = set(extracted.keys()) & set(codemap.keys())
	if len(overwrites) > 0:
		print "Conflict!", overwrites

	codemap.update(extracted)

codebook = {}
for code in codemap:
	k = ''.join(['%02d'%x for x in code])
	codebook[k] = codemap[code]

json.dump(codebook, open('activity_lexicon.json', 'wb'))