#
#
import uuid
import layer_cake as lc

from enum import Enum

__all__ = [
	'AutoTypes',
	'PlainTypes',
	'ContainerTypes',
	'SpecialTypes',
	'TimeTypes',
	'PointerTypes',
	'Item',
	'Brackets',
	'Letter',
	'Question',
	'Plus',
	'Parentheses',
	'Cat',
	'State',
	'MACHINE_STATE',
	'encode_decode'
]

#
#
class AutoTypes(object):
	def __init__(self, a=True, b=42, c=1.234,
			d=bytearray('Hello in bytes', 'ascii'),
			e=b'Hello in chars', f='Hello in codepoints', g=uuid.uuid4()):
		self.a = a
		self.b = b
		self.c = c
		self.d = d
		self.e = e
		self.f = f
		self.g = g

lc.bind_message(AutoTypes)

#
#
class MACHINE_STATE(Enum):
	INITIAL=1
	NEXT=2

class PlainTypes(object):
	def __init__(self, a=None, b=None, c=None, d=None, e=None,
			f=None, g=None, h=None, i=None, j=None, k=None,
			l=None, m=None, n=None, o=None, p=None, q=None):
		self.a = a or True
		self.b = b or int()
		self.c = c or bytes()
		self.d = d or str()
		self.e = e or int()
		self.f = f or int()
		self.g = g or int()
		self.h = h or int()
		self.i = i or int()
		self.j = j or int()
		self.k = k or float()
		self.l = l or float()
		self.m = m or bytearray()
		self.n = n or bytes()
		self.o = o or str()
		self.p = p or MACHINE_STATE.INITIAL
		self.q = q or uuid.uuid4()

lc.bind_message(PlainTypes,
	a=lc.Boolean(),
	b=lc.Byte(),
	c=lc.Character(),
	d=lc.Rune(),
	e=lc.Integer2(),
	f=lc.Integer4(),
	g=lc.Integer8(),
	h=lc.Unsigned2(),
	i=lc.Unsigned4(),
	j=lc.Unsigned8(),
	k=lc.Float4(),
	l=lc.Float8(),
	m=lc.Block(),
	n=lc.String(),
	o=lc.Unicode(),
	p=lc.Enumeration(MACHINE_STATE),
	q=lc.UUID(),
)

#
#
class ContainerTypes(object):
	def __init__(self, a=None, b=None, c=None, d=None, e=None,
			f=None, g=None, h=None, i=None, j=None, k=None, l=None):
		self.a = a or [bytes()] * 8
		self.b = b or [1.0, 1.1, 1.2]
		self.c = c or set([1, 2, 4, 8, 16])
		self.d = d or {"left": "right", "up": "down", "in": "out"}
		self.e = e or lc.deque([4, 5, 6])
		self.f = f or PlainTypes()
		self.g = g or [[bytes()] * 4] * 4
		self.h = h or [[2.0, 2.1, 2.2], [3.0, 3.1, 3.2], [4.0, 4.1, 4.2]]
		self.i = i or {42: {"LEFT": "RIGHT", "UP": "DOWN"}}
		self.j = j or lc.deque([lc.deque([14, 15, 16]), lc.deque([]), lc.deque([24, 25, 26])])
		self.k = k or [[bytes()]] * 4
		self.l = l or [[AutoTypes()] * 2]

lc.bind_message(ContainerTypes,
	a=lc.ArrayOf(lc.String, 8),
	b=lc.VectorOf(lc.Float8),
	c=lc.SetOf(lc.Integer8),
	d=lc.MapOf(lc.Unicode, lc.Unicode),
	e=lc.DequeOf(lc.Integer2),
	f=lc.UserDefined(PlainTypes),

	g=lc.ArrayOf(lc.ArrayOf(lc.String, 4), 4),
	h=lc.VectorOf(lc.VectorOf(lc.Float8)),
	i=lc.MapOf(lc.Integer8, lc.MapOf(lc.Unicode, lc.Unicode)),
	j=lc.DequeOf(lc.DequeOf(lc.Integer2)),
	k=lc.ArrayOf(lc.VectorOf(lc.String), 4),
	l=lc.VectorOf(lc.ArrayOf(lc.UserDefined(AutoTypes), 2)),
)

#
#
auto_types = lc.def_type(AutoTypes)
plain_types = lc.def_type(PlainTypes)

class SpecialTypes(object):
	def __init__(self, a=None, b=None, c=None, d=None, e=None, f=None):
		self.a = a or PlainTypes
		self.b = b or (3, 5, 7)	 # Will lose the 7.
		self.c = c or (2, 4, 6)	 # Add the return_proxy
		self.d = d
		self.e = {'auto': AutoTypes, 'plain': PlainTypes}
		self.f = f or []

lc.bind_message(SpecialTypes,
	a=lc.Type(),
	b=lc.TargetAddress(),
	c=lc.Address(),
	d=lc.Any(),
	e=lc.MapOf(lc.Unicode(), lc.Type()),
	f=lc.VectorOf(lc.Type()),
)

class TimeTypes(object):
	def __init__(self, a=None, b=None, c=None, d=None):
		self.a = a or lc.text_to_clock('2021-07-01T03:02:01.0')
		self.b = b or lc.text_to_span('1d2h3m4.5s')
		self.c = c or lc.text_to_world('2021-07-01T03:02:01.0+01:00')
		self.d = d or lc.text_to_delta('7:00:00:00')

lc.bind_message(TimeTypes,
	a=lc.ClockTime(),
	b=lc.TimeSpan(),
	c=lc.WorldTime(),
	d=lc.TimeDelta(),
)

#
#
class Item(object):
	def __init__(self, tag=None, next=None):
		self.tag = tag or '<blank>'
		self.next = next

lc.bind_message(Item,
	tag=lc.Unicode,
	next=lc.PointerTo(Item),
)

#
#
def linked(*tag):
	p = None
	for s in reversed(tag):
		i = Item(s, p)
		p = i
	return p

def circle(*tag):
	p = None
	t = None
	for s in reversed(tag):
		i = Item(s, p)
		if p is None:
			t = i
		p = i
	if p is not None:
		t.next = p
	return p

# Different elements of an abstract syntax
# tree.
class Brackets(object):
	def __init__(self, range=None):
		self.range = range

lc.bind_message(Brackets, range=lc.Unicode)

class Cat(object):
	def __init__(self, left=None, right=None):
		self.left = left
		self.right = right

lc.bind_message(Cat,
	left=lc.PointerTo(lc.Any),
	right=lc.PointerTo(lc.Any),
)

class Letter(object):
	def __init__(self, lone=None):
		self.lone = lone

lc.bind_message(Letter, lone=lc.Unicode)

class Question(object):
	def __init__(self, optional=None):
		self.optional = optional

lc.bind_message(Question, optional=lc.PointerTo(lc.Any))

class Plus(object):
	def __init__(self, one_or_more=None):
		self.one_or_more = one_or_more

lc.bind_message(Plus, one_or_more=lc.PointerTo(lc.Any))

class Parentheses(object):
	def __init__(self, expression=None):
		self.expression = expression

lc.bind_message(Parentheses, expression=lc.PointerTo(lc.Any))

# Parse of the following regular expression;
# [0-9]+(\.[0-9]+)?
tree = Cat(Plus(Brackets('0123456789')), Question(Cat(Letter('.'), Plus(Brackets('0123456789')))))

# Graph representation of the above AST, i.e. contains the information
# that can be used to generate transition tables.
SERIAL_ID = 1

class State(object):
	def __init__(self, number=None, edge=None):
		global SERIAL_ID
		if number is None:
			number = SERIAL_ID
			SERIAL_ID += 1
		self.number = number
		self.edge = edge or {}

lc.bind_message(State,
	number=lc.Integer8,
	edge=lc.MapOf(lc.Unicode, lc.PointerTo(State)),
)

# Build the state/edge representation for the AST above, i.e. a
# graph with pointers that can refer to any state in the network.
# In this case that includes edges referring to self and edges
# that take a shortcut to the end. Note that for simplicity of
# this example, only the edges for the 0 digit are created.
accept = State()

fraction = State(edge={'0': State(edge={None: accept})})
fraction.edge['0'].edge['0'] = fraction.edge['0']

digits = State(edge={'0': State(edge={None: accept})})
digits.edge['0'].edge['0'] = digits.edge['0']
digits.edge['0'].edge['.'] = fraction

graph = digits
#
#
class PointerTypes(object):
	def __init__(self, a=None, b=None, c=None,
			d=None, e=None, f=None, g=None):
		self.a = a or bool()
		self.b = b or self.a
		self.c = c or PlainTypes()
		self.d = d or linked('a', 'b', 'c', 'd', 'e')
		self.e = e or circle('X', 'Y', 'Z')
		self.f = f or tree
		self.g = g or graph

lc.bind_message(PointerTypes,
	a=lc.PointerTo(lc.Boolean),
	b=lc.PointerTo(lc.Boolean),
	c=lc.PointerTo(lc.UserDefined(PlainTypes)),
	d=lc.PointerTo(Item),	  # Linked using next
	e=lc.PointerTo(Item),	  # Linked using next and looped to start
	f=lc.PointerTo(lc.Any),	# AST for regular expression
	g=lc.PointerTo(State),	 # Graph for state machine
)

#
#
def encode_decode(c, test):
		t = lc.UserDefined(test)
		r = lc.make(t)

		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			return False

		# Recover the application data from the given
		# shipment.
		try:
			b = c.decode(s, t)
		except lc.CodecError as e:
			print(e.note)
			return False

		return lc.equal_to(b, r)
