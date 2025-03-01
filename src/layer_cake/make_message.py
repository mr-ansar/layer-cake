# Author: Scott Woods <scott.18.ansar@gmail.com>
# MIT License
#
# Copyright (c) 2025 Scott Woods
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Construction of message instances.

.. autofunction:: make
.. autofunction:: fake
"""

__docformat__ = 'restructuredtext'

import uuid
from datetime import MINYEAR, datetime, timedelta
from .virtual_memory import *
from .convert_memory import *
from .convert_hints import *
from .virtual_runtime import *
from .message_memory import *

__all__ = [
	'make',
	'fake',
]

# A mapping from ansar to a constructor where
# no parameter is needed.
MAKE_CLASS = {
	Boolean: default_none,
	Byte: default_none,
	Character: default_none,
	Rune: default_none,
	Integer2: default_none,
	Integer4: default_none,
	Integer8: default_none,
	Unsigned2: default_none,
	Unsigned4: default_none,
	Unsigned8: default_none,
	Float4: default_none,
	Float8: default_none,
	Block: default_none,
	String: default_none,
	Unicode: default_none,
	ClockTime: default_none,
	TimeSpan: default_none,
	WorldTime: default_none,
	TimeDelta: default_none,
	UUID: default_none,
	Enumeration: default_none,
	Type: default_none,
	TargetAddress: default_none,
	Address: default_none,
	PointerTo: default_none,
	Any: default_none,
	VectorOf: default_vector,
	SetOf: default_set,
	MapOf: default_map,
	DequeOf: default_deque,
	# Need parameters;
	# ArrayOf
	# UserDefined
}

#
#
def make(t):
	"""Manufactures the Python equivalent of the memory description, or None."""
	if not is_portable(t):
		raise MessageRegistrationError(None, 'non-memory type presented for construction - %r' % (t,))

	try:
		c = MAKE_CLASS[t.__class__]
		return c()
	except KeyError:
		pass
	except AttributeError:
		raise MessageRegistrationError(None, 'internal failure to create from class')

	# Following types are more involved - cant be
	# ctor'd solely from the class.
	if isinstance(t, ArrayOf):
		d = [None] * t.size
		for i in range(t.size):
			d[i] = make(t.element)
		return d

	if isinstance(t, UserDefined):
		return t.element()

	raise MessageRegistrationError(None, 'internal failure to create from memory')

#
#
class Fake(object): pass

bind_message(Fake)

def character_bytes(): return b'c'
def rune_str(): return 'C'
def block_bytearray(): return bytearray([0x0c, 0x0a, 0x0f, 0x0e])
def string_bytes(): return b'CAFE'
def unicode_str(): return 'CAFE'

def fake_clock(): return datetime(1963, 3, 26).timestamp()
def fake_span(): return 0.5
def fake_world(): return datetime(1963, 3, 26)
def fake_delta(): return timedelta(seconds=0.5)
def fake_uuid(): return uuid.uuid4()
def fake_type_(): return Fake
def fake_target(): return [0x0c, 0x0a, 0x0f, 0x0e]
def fake_address(): return [0x0c, 0x0a, 0x0f, 0x0e]
def fake_any(): return [Fake, {}, []]

FAKE_CLASS = {
	Boolean: bool,
	Byte: int,
	Character: character_bytes,
	Rune: rune_str,
	Integer2: int,
	Integer4: int,
	Integer8: int,
	Unsigned2: int,
	Unsigned4: int,
	Unsigned8: int,
	Float4: float,
	Float8: float,
	Block: block_bytearray,
	String: string_bytes,
	Unicode: unicode_str,
	ClockTime: fake_clock,
	TimeSpan: fake_span,
	WorldTime: fake_world,
	TimeDelta: fake_delta,
	UUID: fake_uuid,
	Type: fake_type_,
	TargetAddress: fake_target,
	Address: fake_address,
	Any: fake_any,
}

def fake(t):
	"""Synthesizes an example of the Python equivalent, or None."""
	if not is_portable(t):
		raise MessageRegistrationError(None, 'non-memory type presented for construction - %r' % (t,))

	try:
		c = FAKE_CLASS[t.__class__]
		return c()
	except KeyError:
		pass
	except AttributeError:
		raise MessageRegistrationError(None, 'internal failure to create from class')

	# Following types are more involved - cant be
	# ctor'd solely from the class.
	if isinstance(t, Enumeration):
		e = t.element
		s = e._member_names_[0]
		f = e[s]
		return f
	elif isinstance(t, VectorOf):
		e = fake(t.element)
		d = [e]
		return d
	elif isinstance(t, ArrayOf):
		d = [None] * t.size
		for i in range(t.size):
			d[i] = fake(t.element)
		return d
	elif isinstance(t, DequeOf):
		e = fake(t.element)
		d = deque()
		d.append(e)
		return d
	elif isinstance(t, SetOf):
		e = fake(t.element)
		d = set()
		d.add(e)
		return d
	elif isinstance(t, MapOf):
		k = fake(t.key)
		v = fake(t.value)
		d = {}
		d[k] = v
		return d
	elif isinstance(t, UserDefined):
		element = t.element
		schema = element.__art__.schema
		d = element()
		for k, v in schema.items():
			setattr(d, k, fake(v))
		return d
	elif isinstance(t, PointerTo):
		return fake(t.element)

	raise MessageRegistrationError(None, 'internal failure to create from memory')
