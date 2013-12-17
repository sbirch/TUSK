
'''
def in_bounds(textlines, top=None, left=None, bottom=None, right=None):
    return [tl for tl in textlines if
        (top == None or tl.box.y <= top) and
        (left == None or tl.box.x >= left) and
        (bottom == None or tl.box.y >= bottom) and
        (right == None or tl.box.x <= right)
    ]

def nearest_below(textlines, below):
    candidates = [tl for tl in textlines if tl.box.y < below]
    candidates.sort(key=lambda tl: below - tl.box.y)
    return candidates[0] if len(candidates) else None

def union_box(boxes):
    boxes = [b.box if isinstance(b, Textline) else b for b in boxes]
    l, t, r, b = min(b.x for b in boxes), min(b.y for b in boxes), max(b.right for b in boxes), max(b.bottom for b in boxes)
    return Box(
        l, t, r, b,
        r-l, b-t
    )
   '''

class Box:
	def __init__(self, x, y, w=None, h=None, right=None, bottom=None, text=None, tags=None):
		self.x = x
		self.y = y
		self.text = text
		self.tags = set()

		'''
		assert (w != None and h != None) or (right != None and bottom != None)

		if w != None and h != None:
			self.w = w
			self.h = h
			self.right = self.x + self.w
			self.bottom = self.y - self.h
		else:
		'''

		self.right = right
		self.bottom = bottom
		self.w = self.right - self.x
		self.h = self.bottom - self.y

	def tag(self, tag):
		if isinstance(tag, list) or isinstance(tag, set):
			self.tags = self.tags.union(set(tag))
		else:
			self.tags.add(tag)

	def to_html(self):
		return '<div style="position: absolute; font-size: 8px; border: 1px solid #ccc; left: %dpx; top: %dpx; width: %dpx; height: %dpx;">%s</div>' % (
			self.x, self.y,
			self.w, self.h,
			self.text.replace(' ', '&nbsp;').replace('\n', '<br />'))

	def __add__(self, other):
		if isinstance(other, BoxSet):
			return BoxSet([self] + other.elements)
		elif isinstance(other, Box):
			return BoxSet([self, other])
		else:
			raise TypeError("Can't add Box and %r" % other)

	def __repr__(self):
		return '<Box@%d,%d %dx%d %s %r>' % (self.x, self.y, self.w, self.h, '/'.join(self.tags), self.text)


class BoxSet:
	def __init__(self, elements):
		self.elements = elements
	def filter(self, f_filter):
		return BoxSet([el for el in self.elements if f_filter(el)])
	def find(self, f_filter, only_one=True):
		candidates = self.filter(f_filter).elements
		if len(candidates) == 0:
			raise Exception('None found')
		if only_one and len(candidates) > 1:
			raise Exception('More than one found: %r' % candidates)
		return candidates[0]
	def below(self, el=None, wiggle=5, bound=None):
		p = el.y if bound == None else bound
		return self.filter(lambda e: e.y > p - wiggle) - el
	def above(self, el=None, wiggle=5, bound=None):
		p = el.y if bound == None else bound
		return self.filter(lambda e: e.y < p + wiggle) - el
	def right(self, el=None, wiggle=5, bound=None):
		p = el.x if bound == None else bound
		return self.filter(lambda e: e.x > p - wiggle) - el
	def left(self, el=None, wiggle=5, bound=None):
		p = el.x if bound == None else bound
		return self.filter(lambda e: e.x < p + wiggle) - el
	def v_aligned(self, el, wiggle=5):
		return self.filter(lambda e: abs(e.y - el.y) < wiggle)
	def h_aligned(self, el, wiggle=5):
		return self.filter(lambda e: abs(e.x - el.x) < wiggle)
	def by(self, f):
		return BoxSet(sorted(self.elements, key=f))
	def tagged(self, tag):
		return BoxSet([e for e in self.elements if tag in e.tags])
	def untagged(self):
		return BoxSet([e for e in self.elements if len(e.tags) == 0])

	def cluster_lines(self, wiggle=5):
		seen = set()
		lines = []
		i = 0
		while i < len(self.elements):
			e = self.elements[i]
			if e in seen:
				i += 1
				continue

			candidate_lines = [line for line in lines if abs(e.y - line[0].y) < wiggle]
			if len(candidate_lines) == 0:
				lines.append([e])
			else:
				candidate_lines[0].append(e)

			seen.add(e)
			i += 1

		for line in lines:
			line.sort(key=lambda e: e.x)

		return lines

	def tag(self, tag):
		[e.tag(tag) for e in self.elements]
		return self

	def to_html(self):
		return ''.join([e.to_html() for e in self.elements])

	def __len__(self):
		return len(self.elements)
	def __getitem__(self, k):
		return self.elements[k]
	def __iter__(self):
		return iter(self.elements)

	def __add__(self, other):
		if isinstance(other, BoxSet):
			return BoxSet(self.elements + other.elements)
		elif isinstance(other, Box):
			return BoxSet(self.elements + [other])
		else:
			raise TypeError("Can't add BoxSet and %r" % other)

	def __sub__(self, other):
		if other is None:
			return self
		elif isinstance(other, BoxSet):
			return BoxSet([e for e in self.elements if e not in other.elements])
		elif isinstance(other, Box):
			return BoxSet([e for e in self.elements if e != other])
		else:
			raise TypeError("Can't subtract BoxSet and %r" % other)
		

	def __repr__(self):
		return '[\t%s\n]' % '\n\t'.join([repr(x) for x in self.elements])



