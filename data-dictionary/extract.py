from xml.dom.minidom import parse, parseString
from xml.dom import Node
import re, pprint
from visual_parse import Box, BoxSet
from collections import namedtuple

def page_wh(page):
    pl,pt,W,H = [float(x) for x in page.attributes['bbox'].value.split(',')]
    assert pl+pt == 0
    return W,H

def bbox_to_box(e, page):
    W,H = page_wh(page)
    l,t,r,b = [float(x) for x in e.attributes['bbox'].value.split(',')]
    return Box(l, H-b, right=r, bottom=H-t)

def child_elements(e):
    return [n for n in e.childNodes if n.nodeType == Node.ELEMENT_NODE]

def process_textline(e, page):
    textbits = child_elements(e)
    assert all([bit.firstChild.nodeType == Node.TEXT_NODE for bit in textbits])
    content = ''.join([bit.firstChild.nodeValue for bit in textbits])
    box = bbox_to_box(e, page)
    box.text = content
    return box

def process_textbox(e, page):
    lines = child_elements(e)
    assert all([l.tagName == 'textline' for l in lines])
    return [process_textline(l, page) for l in lines]

def textlines_to_string(textlines):
    return re.sub('\s+', ' ', ' '.join([box.text for box in textlines])).strip()

PageObject = namedtuple('PageObject', ['type', 'y', 'content'])

def process_page(page):
    page_w, page_h = page_wh(page)

    textlines = []
    for e in child_elements(page):
        if e.tagName == 'textbox':
            textlines.extend(process_textbox(e, page))
        elif e.tagName == 'rect':
            pass
        elif e.tagName == 'figure':
            pass
        elif e.tagName == 'layout':
            pass
        else:
            print e

    textlines = BoxSet(textlines)

    #print textlines.to_html()

    name = textlines.find(lambda e: e.text.strip().lower() == 'name')
    description_header = textlines.find(lambda e: e.text.strip().lower() == 'description')
    file_header = textlines.find(lambda e: e.text.strip().lower() == 'file')

    variables = textlines.h_aligned(name).filter(lambda e: re.match('^[GHPT][UERT][A-Z0-9_]{1,12}$', e.text.strip()))

    ed_uni = textlines.h_aligned(description_header).filter(lambda e: e.text.strip().lower().startswith('edited universe:'))
    valid_entries = textlines.h_aligned(description_header).filter(lambda e: e.text.strip().lower() == 'valid entries:')
    notes = textlines.h_aligned(description_header).filter(lambda e: e.text.strip().lower().startswith('* note'))

    ed_uni.tag('edited-universe')
    valid_entries.tag('valid-entry')
    notes.tag(['notes', 'notes-begin'])

    landmarks = (variables + ed_uni + valid_entries + notes).by(lambda e: e.y)
    landmarks.tag('landmark')

    result_variables = []
    result_valid_entry_sets = []
    result_notes = []

    for variable in variables:
        #print variable
        first_description, first_file = textlines.v_aligned(variable).right(variable, bound=variable.right).by(lambda e: e.x)
        

        next_landmark = landmarks.below(variable, bound=variable.bottom).by(lambda e: e.y)
        next_landmark_bound = next_landmark[0].y if len(next_landmark) > 0 else page_h
        next_landmark = next_landmark[0] if len(next_landmark) > 0 else None

        other_files = textlines.h_aligned(file_header).below(first_file).above(bound=next_landmark_bound) - next_landmark

        variable_files = first_file + other_files
        variable_files.tag('files')

        other_description = textlines.h_aligned(description_header).below(first_description).above(bound=next_landmark_bound) - next_landmark

        description = first_description + other_description
        description.tag('description')

        #print '====', variable.text.strip(), '===='
        #print textlines_to_string(description)
        #print textlines_to_string(variable_files)

        result_variables.append(PageObject('variable', variable.y, (
            variable, description, variable_files
        )))
    
    for valid_entry in valid_entries:
        next_landmark = landmarks.below(bound=valid_entry.bottom).by(lambda e: e.y)
        next_landmark = next_landmark[0].y if len(next_landmark) > 0 else page_h

        value_table = textlines.right(valid_entry).below(valid_entry).above(bound=next_landmark).untagged()
        rows = value_table.cluster_lines()

        # if there are dangling lines below in the paragraph we need to merge them up
        for i, row in enumerate(rows):
            if len(row) > 1:
                k = i+1
                while k < len(rows) and len(rows[k]) == 1:
                    row.extend(rows[k])
                    k += 1

        rows = [row for row in rows if len(row) > 1]

        #print '---'
        #for row in rows:
        #    print row

        result_valid_entry_sets.append(PageObject('valid-entries', valid_entry.y, rows))

    for note in notes:
        #print note
        next_landmark = landmarks.below(bound=note.bottom).by(lambda e: e.y)
        next_landmark = next_landmark[0].y if len(next_landmark) > 0 else page_h

        note_lines = textlines.below(note).above(bound=next_landmark).untagged()

        result_notes.append(PageObject('note', note.y, note + note_lines))

        

    # is there ever more than 1 line in edited universe?
    # is there a way to add next_landmark to the library? = above_next?
    # nice way of pulling multiple lines in paragraphs? get_paragraph?
    # nice way of interleaving the variables and other metadata? iterate through landmarks?

    return result_variables, result_valid_entry_sets, result_notes

def convert_valid_entries(entries):
    value_map = {}

    for tokens in entries:
        left = tokens[0].text.strip()
        right = textlines_to_string(tokens[1:])

        if left in value_map:
            print 'Duplicate values!'
            print 'Valid entries textline data:'
            pprint.pprint(entries)
            print 'Conflict key:', repr(left)
            print 'Before:'
            print repr(value_map[left])
            print 'After:'
            print repr(right)
        value_map[left] = right

    return value_map

#from xml.dom.minidom import parse; dom = parse('converted.xml'); import extract_vparse;
#reload(extract_vparse); extract_vparse.main(dom)
# pages / page / textbox / textline / text
# rect, layout, figure, textgroup

Variable = namedtuple('Variable', ['name', 'description', 'files', 'edited_universe', 'valid_entries', 'note'])

def main(dom, start_page=10, end_page=50):
    objects = []
    for i,page in enumerate(child_elements(dom.firstChild)):
        if start_page <= int(page.attributes['id'].value) <= end_page:
            print 'Processing page', int(page.attributes['id'].value)
            rvars, rvalid, rnotes = process_page(page)
            objects.extend(sorted(rvars + rvalid + rnotes, key=lambda po: po.y))

    variables = {}

    i = 0
    while i < len(objects):
        obj = objects[i]
        assert obj.type == 'variable'

        var, description, files = obj.content
        variable_name = var.text.strip()

        print '====', variable_name, '===='

        items = {}
        k = i+1
        while k < len(objects) and objects[k].type != 'variable':
            if items.has_key(objects[k].type):
                #print 'Eviction conflict:'
                #print items[objects[k].type]
                #print '\t\tvs.'
                #print objects[k]
                #print
                #print
                old = items[objects[k].type]
                new = objects[k]

                items[new.type] = PageObject(new.type, new.y, old.content + new.content)
            else:
                items[objects[k].type] = objects[k]
            k += 1
        i = k

        variables[variable_name] = Variable(
            variable_name,
            textlines_to_string(description),
            [x.strip() for x in textlines_to_string(files).split(',')],
            None,
            convert_valid_entries(items['valid-entries'].content) if items.has_key('valid-entries') else None,
            textlines_to_string(items['note'].content) if items.has_key('note') else None
        )

    
    assert i == len(objects)

    #pprint.pprint(variables)

    return variables

if __name__ == '__main__':
    cps_codes = main(parse('atuscpscodebk0312.xml'), start_page=10, end_page=50)
    int_codes = main(parse('atusintcodebk0312.xml'), start_page=11, end_page=37)

    import json

    def convert(vs):
        return {k: {
            'description': v.description,
            'files': v.files,
            # not presently extracted
            #'edited_universe':
            'validEntries': v.valid_entries,
            'note': v.note[len('* Note: '):] if v.note is not None and v.note.startswith('* Note: ') else v.note
        } for k,v in vs.items()}

    #json.dump(convert(cps_codes), open('cps_codes.json', 'wb'))
    #json.dump(convert(int_codes), open('int_codes.json', 'wb'))

    duplicated = set(cps_codes.keys()).intersection(set(int_codes.keys()))

    print 'Variables appearing in both CPS and ATUS data dictionaries:', duplicated

    print 'Preferring ATUS variable data for data_dictionary.json'
    cps_codes.update(int_codes)
    json.dump(convert(cps_codes), open('data_dictionary.json', 'wb'))

