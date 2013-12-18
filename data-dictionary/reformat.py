import json, re

'''
TODO:
	Variable table of contents
	Variable statistics!
'''

variables = json.load(open('data_dictionary.json', 'rb'))

FL_CODES = {
	'G': 'CPS-geography',
	'H': 'CPS-household',
	'P': 'CPS-person',
	'T': 'ATUS interview'
}
SL_CODES = {
	'U': 'unedited',
	'E': 'edited',
	'R': 'recoded',
	'T': 'topcoded'
}

output = open('combined-dictionary/index.html', 'wb')
template = open('combined-dictionary/template.html', 'rb').read()

content = []
order = variables.keys()
order.sort(key=lambda x: (variables[x]['document'], variables[x]['pages'][0], x))

for variable in order:
	entry = variables[variable]

	values = ''
	if entry['validEntries'] is not None:
		entries = []
		ordered_values = entry['validEntries'].keys()
		def tryint(x):
			try:
				return int(x)
			except:
				return x
		ordered_values.sort(key=tryint)
		for k in ordered_values:
			entries.append('<li><span class="entry-value">%s</span> &mdash; %s</li>' % (k,entry['validEntries'][k]))

		values = '<strong>Values:</strong><ul class="valid-entries">%s</ul>' % ''.join(entries)

	content.append('''<hr /><div class="variable">
		<h3><a name="%s"><span class="firsttwo">%s</span>%s</a></h3>
		<div class="type">%s</div>
		<div class="docref">%s</div>
		
		<div class="description">
			%s
			<div class="in"><span>In: </span>%s</div>
		</div>
		%s
		%s
		%s
	</div>''' % (
		variable, variable[:2], variable[2:],
		'%s &mdash; %s, %s' % (variable[:2], FL_CODES[variable[0]], SL_CODES[variable[1]]),
		'%s p.%d' % (entry['document'], entry['pages'][0]),
		entry['description'],
		', '.join(entry['files']),
		'<div class="eduni"><span>Edited universe: </span>%s</div>' % entry['editedUniverse'] if entry['editedUniverse'] is not None else '',
		values,
		'' if entry['note'] is None else '<div class="note"><span>Note: </span>%s</div>' % re.sub('(\s|\(|\[)([GHPT][UERT][A-Z0-9_]{1,12})', r'\1<a class="crossref" href="#\2">\2</a>', entry['note'])
		)

	)

output.write(template % ''.join(content))