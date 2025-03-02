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

"""Encode and decode between application data and portable representation.

This module provides the basis for implementation of all codecs, i.e. the
Ansar objects that can encode and decode items of application data.

Encoding and decoding is split into a 2-layer process. The upper layer
deals with the conversion of application data to and from an internal
generic form. The lower layer is dedicated to the rendering of generic
forms into specific representations and the subsequent parsing of those
representations back into generic forms.

The :py:class:`~ansar.code.Codec` class provides the upper layer. Lower
layers are provided by classes such as :py:class:`~ansar.json.CodecJson`.
The latter derives from the former, inheriting 2 important methods -
:py:meth:`~ansar.codec.Codec.encode` and :py:meth:`~ansar.codec.Codec.decode`.

	.. code-block:: python

		# Define the wrapper around the JSON encoding
		# primitives.
		class CodecJson(Codec):

These 2 methods manage the combination of the two layers, presenting an
encoding-independent interface for all serialization activities within
the library.

"""

# .. autoclass:: CodecError
# .. autoclass:: CodecUsageError
# .. autoclass:: CodecRuntimeError
# .. autoclass:: Codec
#	:members:
#	:no-undoc-members:
# .. autofunction:: python_to_word
# .. autofunction:: word_to_python

__docformat__ = 'restructuredtext'

import base64
import uuid
import sys
import types
from datetime import datetime, timedelta
from copy import deepcopy
from enum import Enum


from .virtual_memory import *
from .convert_memory import *
from .convert_type import *
from .convert_hints import *
from .virtual_runtime import *
from .message_memory import *
from .make_message import *


__all__ = [
	'TypeType',
	'NoneType',
	'CodecError',
	'CodecUsageError',
	'CodecRuntimeError',
	'EnumerationRuntimeError',
	'python_to_word',
	'word_to_python',
	'Codec',

	'pass_thru',
	'w2p_string',
	'w2p_block',
	'w2p_clock',
	'w2p_span',
	'w2p_world',
	'w2p_delta',
	'w2p_uuid',
	'w2p_enumeration',
	'w2p_type',
	'w2p_any',
]

#
#
TypeType = type
NoneType = type(None)

#
#
class CodecError(Exception):
	"""Base exception for all codec exceptions."""

	def __init__(self, note):
		"""Construct the exception.

		:param note: hint as to what happened
		:type name: str
		"""
		Exception.__init__(self, note)
		self.note = note				# For quick access.

class CodecUsageError(CodecError):
	"""Cannot proceed due to its supplied environment such as unusable parameters."""

	def __init__(self, note, *a):
		"""Construct the exception.

		:param note: a short, helpful description
		:type note: str
		:param a: values to be substituted into ``note``
		:type a: list
		"""
		CodecError.__init__(self, note % a)

class CodecRuntimeError(CodecError):
	"""Failure during actual encoding or decoding, such as parsing."""

	def __init__(self, note, *a):
		"""Construct the exception.

		:param note: a short, helpful description
		:type note: str
		:param a: values to be substituted into ``note``
		:type a: list
		"""
		CodecError.__init__(self, note % a)

class EnumerationRuntimeError(Exception):
	"""Cannot encode/decode an enumeration."""

	def __init__(self, note):
		"""Construct the exception."""
		Exception.__init__(self, note)

class CircularReferenceError(Exception):
	pass

#
#
def decode_type(s):
	"""Convert the dotted string *s* to a class, or None."""
	try:
		i = s.rindex('.')
	except ValueError:
		return None
	module = s[:i]
	name = s[i + 1:]
	try:
		m = sys.modules[module]
	except KeyError:
		return None

	try:
		c = m.__dict__[name]
	except KeyError:
		return None
	return c

def encode_type(c):
	"""Convert the class *c* to a dotted string representation."""
	b = c.__art__     # Ansar runtime.
	e = '%s.%s' % (b.module, b.name)
	return e

# Transform python data to generic words. Immediately below
# are the code fragments that perform conversions from a
# specific type of python data to a declared Ansar type.
# These fragments are loaded into a jump table and the
# python_to_word function packages proper access to the
# table.
#
# All application data is reduced to an instance of the
# following types. All language and Ansar type information
# is cleared away. The generic types are;
#
# * bool .....
# * int ......
# * float ....
# * str ...... unicode
# * list ..... [v, v, v, ...]
# * dict ..... {k: v, k: v, ...}
# * none ..... null
#
# e.g.;
# * an array of 8 integers will be rendered as a list.
# * a map<string,list<int>> will be rendered as a list of pairs.
# * the dict type is reserved for rendering of structs/objects.

def pass_thru(c, p, t):
	return p

def p2w_block(c, p, t):
	w = base64.b64encode(p)
	w = w.decode(encoding='utf-8', errors='strict')
	return w

def p2w_string(c, p, t):
	w = ''
	for b in p:
		w += chr(b)
	return w

def p2w_clock(c, p, t):
	w = clock_to_text(p)
	return w

def p2w_span(c, p, t):
	w = span_to_text(p)
	return w

def p2w_world(c, p, t):
	w = world_to_text(p)
	return w

def p2w_delta(c, p, t):
	w = delta_to_text(p)
	return w

def p2w_uuid(c, p, t):
	w = uuid_to_text(p)
	return w

def p2w_enumeration(c, p, t):
	w = p.name
	return w

class NotFound(object): pass

def p2w_message(c, p, t):
	message = t.element
	rt = message.__art__
	schema = rt.schema

	w = {}
	for k, v in schema.items():
		c.walking_stack.append(k)

		# Ensure the matching pop happens.
		def get_put():
			m = getattr(p, k, NotFound)
			if m is NotFound:
				return
			elif m is None:
				if is_structural(v):
					raise ValueError(f'null value detected for structural "{rt.name}.{k}"')
			w[k] = python_to_word(c, m, v)
		get_put()
		c.walking_stack.pop()
	return w

def p2w_array(c, p, t):
	e = t.element
	n = len(p)
	s = t.size
	if n != s:
		raise ValueError(f'array size vs specification - {n}/{s}')
	w = []
	for i, y in enumerate(p):
		c.walking_stack.append(i)
		a = python_to_word(c, y, e)
		w.append(a)
		c.walking_stack.pop()
	return w

def p2w_vector(c, p, t):
	e = t.element
	w = []
	for i, y in enumerate(p):
		c.walking_stack.append(i)
		a = python_to_word(c, y, e)
		w.append(a)
		c.walking_stack.pop()
	return w

def p2w_set(c, p, t):
	e = t.element
	w = []
	for y in p:
		a = python_to_word(c, y, e)
		w.append(a)
	return w

def p2w_map(c, p, t):
	k_t = t.key
	v_t = t.value
	w = []
	for k, v in p.items():
		a = python_to_word(c, k, k_t)
		b = python_to_word(c, v, v_t)
		w.append([a, b])
	return w

def p2w_deque(c, p, t):
	e = t.element
	w = []
	for y in p:
		a = python_to_word(c, y, e)
		w.append(a)
	return w

def p2w_pointer(c, p, t):
	k = id(p)
	try:
		a = c.aliased_pointer[k]
		return a[0]
	except KeyError:
		pass

	composite = '%d:%s' % (c.pointer_alias, c.alias_space)
	a = [composite, None]
	c.pointer_alias += 1
	c.aliased_pointer[k] = a

	w = python_to_word(c, p, t.element)
	a[1] = w
	c.any_stack[-1].add(composite)
	return a[0]

def p2w_type(c, p, t):
	if hasattr(p, '__art__'):
		w = p.__art__.path
	elif isinstance(p, Portable):
		w = type_signature(p)
	else:
		raise ValueError(f'cannot encode type')
	return w

def p2w_target(c, p, t):
	# TODO
	# Perhaps the JSON encoder passes this
	# through as a list anyway. No need for
	# transform?
	w = list(p)
	return w

def p2w_address(c, p, t):
	if c.space is not None:
		i = len(c.space)
		c.space.append(p)
		return i
	# Check to see if an address is being
	# passed back over the connection it
	# arrived on. Prevents trombone behaviour.
	# Detection happens *here* at the remote
	# end of the trombone because this codec
	# knows it is sending an address back to
	# where it came from. Add the invalid point
	# id. See w2p_address.
	if c.return_proxy is not None:
		a = c.return_proxy
		if p[-1] == a:
			# Need to advise remote that address
			# is returning to where it came from.
			w = list(p[:-1])	# DROP THIS PROXY
			w.append(0)		 # SPECIAL MARK
			return w
	w = list(p)
	return w

def p2w_any(c, p, t):
	a = type(p)
	if a == Incognito:	# Created during a previous decoding operation.
		t = p.type_name				# Global identifier
		w = p.decoded_word			# Generic body
		if p.saved_pointers:
			c.portable_pointer.update(p.saved_pointers)	 # Include upstream pointer materials.
			r = [k for k in p.saved_pointers.keys()]		# List of pointers.
		else:
			r = []
	elif hasattr(a, '__art__'):
		s = c.any_stack
		s.append(set())
		t = python_to_word(c, a, Type())
		w = python_to_word(c, p, UserDefined(a))
		n = s.pop()
		s[-1].update(n)
		r = [x for x in n]
	elif isinstance(p, tuple) and len(p) == 2 and isinstance(p[1], Portable):
		s = c.any_stack
		s.append(set())
		t = python_to_word(c, p[1], Type())
		w = python_to_word(c, p[0], p[1])
		n = s.pop()
		s[-1].update(n)
		r = [x for x in n]
	else:
		raise ValueError(f'encoding any, expecting message, tuple[2] or Incognito.')

	return [t, w, r]

# Map the python+portable pair to a dedicated
# transform function.
p2w = {
	# Direct mappings.
	(bool, Boolean): pass_thru,
	(int, Byte): pass_thru,
	(bytes, Character): p2w_string,
	(str, Rune): pass_thru,
	(int, Integer2): pass_thru,
	(int, Integer4): pass_thru,
	(int, Integer8): pass_thru,
	(int, Unsigned2): pass_thru,
	(int, Unsigned4): pass_thru,
	(int, Unsigned8): pass_thru,
	(float, Float4): pass_thru,
	(float, Float8): pass_thru,
	(Enum, Enumeration): p2w_enumeration,
	(bytearray, Block): p2w_block,
	(bytes, String): p2w_string,
	(str, Unicode): pass_thru,
	(float, ClockTime): p2w_clock,
	(float, TimeSpan): p2w_span,
	(datetime, WorldTime): p2w_world,
	(timedelta, TimeDelta): p2w_delta,
	(uuid.UUID, UUID): p2w_uuid,
	(list, ArrayOf): p2w_array,
	(list, VectorOf): p2w_vector,
	(set, SetOf): p2w_set,
	(dict, MapOf): p2w_map,
	(deque, DequeOf): p2w_deque,
	(TypeType, Type): p2w_type,
	(Portable, Type): p2w_type,
	(tuple, TargetAddress): p2w_target,
	(tuple, Address): p2w_address,

	# PointerTo - can be any of the above.
	(bool, PointerTo): p2w_pointer,
	(int, PointerTo): p2w_pointer,
	(float, PointerTo): p2w_pointer,
	(bytearray, PointerTo): p2w_pointer,
	(bytes, PointerTo): p2w_pointer,
	(str, PointerTo): p2w_pointer,
	# ClockTime and TimeDelta. Float/ptr already in table.
	# (float, PointerTo): p2w_pointer,
	# (float, PointerTo): p2w_pointer,
	(datetime, PointerTo): p2w_pointer,
	(timedelta, PointerTo): p2w_pointer,
	(uuid.UUID, PointerTo): p2w_pointer,
	(list, PointerTo): p2w_pointer,
	(set, PointerTo): p2w_pointer,
	(dict, PointerTo): p2w_pointer,
	(deque, PointerTo): p2w_pointer,
	(TypeType, PointerTo): p2w_pointer,
	(tuple, PointerTo): p2w_pointer,
	(Message, PointerTo): p2w_pointer,

	# Two mechanisms for including messages
	(Message, UserDefined): p2w_message,
	(Message, Any): p2w_any,
	(tuple, Any): p2w_any,

	# Support for Word, i.e. passthru anything
	# that could have been produced by the functions
	# above. No iterating nested layers.

	(bool, Word): pass_thru,
	(int, Word): pass_thru,
	(float, Word): pass_thru,
	# (bytearray, Word): pass_thru,
	# (bytes, Word): pass_thru,
	(str, Word): pass_thru,
	(list, Word): pass_thru,
	(dict, Word): pass_thru,
	# set, tuple - do not appear in generic

	# Provide for null values being
	# presented for different universal
	# types.

	(NoneType, Boolean): pass_thru,
	(NoneType, Byte): pass_thru,
	(NoneType, Character): pass_thru,
	(NoneType, Rune): pass_thru,
	(NoneType, Integer2): pass_thru,
	(NoneType, Integer4): pass_thru,
	(NoneType, Integer8): pass_thru,
	(NoneType, Unsigned2): pass_thru,
	(NoneType, Unsigned4): pass_thru,
	(NoneType, Unsigned8): pass_thru,
	(NoneType, Float4): pass_thru,
	(NoneType, Float8): pass_thru,
	(NoneType, Block): pass_thru,
	(NoneType, String): pass_thru,
	(NoneType, Unicode): pass_thru,
	(NoneType, ClockTime): pass_thru,
	(NoneType, TimeSpan): pass_thru,
	(NoneType, WorldTime): pass_thru,
	(NoneType, TimeDelta): pass_thru,
	(NoneType, UUID): pass_thru,
	(NoneType, Enumeration): pass_thru,
	# DO NOT ALLOW
	# (NoneType, UserDefined): pass_thru,
	# (NoneType, ArrayOf): pass_thru,
	# (NoneType, VectorOf): pass_thru,
	# (NoneType, SetOf): pass_thru,
	# (NoneType, MapOf): pass_thru,
	# (NoneType, DequeOf): pass_thru,
	(NoneType, PointerTo): pass_thru,
	(NoneType, Type): pass_thru,
	(NoneType, TargetAddress): pass_thru,
	(NoneType, Address): pass_thru,
	(NoneType, Word): pass_thru,
	(NoneType, Any): pass_thru,
}

def python_to_word(c, p, t):
	"""Generate word equivalent for the supplied application data.

	:param c: the active codec
	:type c: an Ansar Codec
	:param p: the data item
	:type p: application data
	:param t: the portable description of `p`.
	:type t: a portable expression
	:return: a generic word, ready for serialization.
	"""
	try:
		if is_message(p):
			a = Message
		elif isinstance(p, Enum):
			a = Enum
		elif isinstance(p, Portable):
			a = Portable
		else:
			a = getattr(p, '__class__')
	except AttributeError:
		a = None

	try:
		b = t.__class__		 # One of the universal types.
	except AttributeError:
		b = None

	if a is None:
		if b is None:
			raise TypeError('data and specification are unusable')
		raise TypeError(f'data with specification "{b.__name__}" is unusable')
	elif b is None:
		raise TypeError(f'data "{a.__name__}" has unusable specification')

	try:
		f = p2w[a, b]
	except KeyError:
		raise TypeError(f'no transformation for data/specification {a.__name__}/{b.__name__}')

	# Apply the transform function
	return f(c, p, t)

# From generic data (after parsing) to final python
# representation in the application.

def w2p_string(c, w, t):
	b = bytearray()
	for c in w:
		b.append(ord(c))
	return bytes(b)

def w2p_block(c, w, t):
	p = base64.b64decode(w)
	return bytearray(p)

def w2p_clock(c, w, t):
	p = text_to_clock(w)
	return p

def w2p_span(c, w, t):
	p = text_to_span(w)
	return p

def w2p_world(c, w, t):
	p = text_to_world(w)
	return p

def w2p_delta(c, w, t):
	p = text_to_delta(w)
	return p

def w2p_uuid(c, w, t):
	p = text_to_uuid(w)	 # Throws a ValueError.
	return p

def w2p_enumeration(c, w, t):
	try:
		p = t.element[w]
	except KeyError:
		m = t.element.__name__
		raise EnumerationRuntimeError(f'no number for "{w}" in "{m}"')
	return p

def w2p_message(c, w, t):
	u = t.element
	rt = t.element.__art__
	schema = rt.schema
	# Use the full set of names from the schema
	# to pull named values from the dict. If the
	# name is not present this is assumed to be a
	# case of skipping the encode of null values.
	# Also the scenario enforced by the version
	# slicing.
	p = u()
	for k, v in schema.items():
		c.walking_stack.append(k)

		def get_put():
			d = w.get(k, NotFound)
			if d is NotFound:		# Expected by schema, not present. Ignore.
				return
			elif d is None:
				if is_structural(v):
					raise ValueError(f'null value detected for structural "{rt.name}.{k}"')
				return

			def patch(a):
				setattr(p, k, a)
			try:
				a = word_to_python(c, d, v)
				setattr(p, k, a)
			except CircularReferenceError:
				c.patch_work.append([d, patch])
		get_put()

		c.walking_stack.pop()

	return p

def w2p_pointer(c, a, t):
	# None is handled in the table
	# (NoneType, PointerTo): pass_thru

	# 1. Is this a recursive visit to a - throw.
	# 2. Has the address word aleady been decoded.
	# 3. Find the shipped generic word.
	# 4. Guarded decode of generic word.
	# 5. Remember the decode.

	if a in c.pointer_reference:
		raise CircularReferenceError()

	try:
		p = c.decoded_pointer[a]
		return p
	except KeyError:
		pass

	try:
		w = c.portable_pointer[a]
	except KeyError:
		raise ValueError('pointer alias not in materials')

	c.pointer_reference.add(a)
	p = word_to_python(c, w, t.element)
	c.pointer_reference.remove(a)

	c.decoded_pointer[a] = p
	return p

def w2p_type(c, w, t):
	try:
		p = signature_type(w)
	except ValueError:
		return None
	if isinstance(p, UserDefined):
		return p.element
	return p

def w2p_array(c, w, t):
	e = t.element
	n = len(w)
	x = 0
	s = t.size
	if n > s:
		# Inbound value is longer than the target. Ignore the
		# additional items.
		# Previously there was an exception;
		# raise ValueError('array size vs specification - %d/%d' % (n, s))
		n = s
	elif n < s:
		# Inbound value is shorter than the target. Add a tail of default
		# values. This supports the guarantee that all arrays are the
		# expected size and each element is a reasonable default, i.e.
		# as defined by the element expression.
		x = s - n
		v = make(e)	 # Form the first default from the expression.
	p = []
	for i in range(n):
		d = w[i]
		c.walking_stack.append(i)

		def patch(a):
			p[i] = a
		try:
			a = word_to_python(c, d, e)
			p.append(a)
		except CircularReferenceError:
			p.append(None)
			c.patch_work.append([d, patch])
		c.walking_stack.pop()

	for i in range(x):
		p.append(v)
		v = deepcopy(v)
	return p

def w2p_vector(c, w, t):
	e = t.element
	p = []
	for i, d in enumerate(w):
		c.walking_stack.append(i)

		def patch(a):
			p[i] = a
		try:
			a = word_to_python(c, d, e)
			p.append(a)
		except CircularReferenceError:
			p.append(None)
			c.patch_work.append([d, patch])
		c.walking_stack.pop()
	return p

def w2p_set(c, w, t):
	e = t.element
	p = set()
	for d in w:
		a = word_to_python(c, d, e)
		p.add(a)
	return p

def w2p_map(c, w, t):
	k_t = t.key
	v_t = t.value
	p = {}
	for d in w:
		k = word_to_python(c, d[0], k_t)

		def patch(a):
			p[k] = a
		try:
			v = word_to_python(c, d[1], v_t)
			p[k] = v
		except CircularReferenceError:
			c.patch_work.append([d[1], patch])
	return p

def w2p_deque(c, w, t):
	e = t.element
	p = deque()
	for i, d in enumerate(w):
		def patch(a):
			p[i] = a
		try:
			a = word_to_python(c, d, e)
			p.append(a)
		except CircularReferenceError:
			p.append(None)
			c.patch_work.append([d, patch])
	return p

def w2p_target(c, w, t):
	if c.local_termination is None:
		p = tuple(w)
	elif len(w) < 2:
		p = c.local_termination,
	else:
		p = tuple(w[:-1])
	return p

def w2p_address(c, w, t):
	if c.space is not None:
		p = c.space[w]
		return p
	if c.return_proxy is not None:
		# Clean out any trombone detected
		# in the remote. See p2w_address.
		a = w[-1]
		if a == 0:	  # SPECIAL MARK
			# Address has returned home
			# No need to append a trip back
			# over this connection.
			w.pop()
			if len(w) == 0:
				# Send it to the local proxy.
				w.append(c.return_proxy)
		else:
			w.append(c.return_proxy)
	p = tuple(w)	# Now convert.
	return p

def w2p_null_pointer(c, w, t):
	return [0, None]

# Covert inbound 3-word tuple into the original object
def w2p_any(c, w, t):
	a = w[0]	# Inbound type name.
	b = w[1]	# A generic word.
	r = w[2]	# Pointer aliases.
	e = word_to_python(c, a, Type())		# Signature to portable.
	if e is None:							# No such type.
		y = c.portable_pointer				# Everything shipped
		h = [x for x in r if x not in y]	# Needed for this any
		if h:
			raise ValueError('cannot go incognito - unresolved pointers e.g. "%s"', h[0])
		m = {x: y[x] for x in r}			# Needed for this any
		p = Incognito(a, b, m)
	elif hasattr(e, '__art__'):						# Direct message type.
		p = word_to_python(c, b, UserDefined(e))	# Need to pass back data and type.
	elif isinstance(e, Portable):
		p = word_to_python(c, b, e)		# Need to pass back data and type.
		p = (p, e)
	return p

#
#
w2p = {
	# Direct mappings. Left part of key is
	# the type used in a generic representation to
	# pass the intended ansar type, i.e. if we are
	# expecting b then it should arrive as an a.
	(bool, Boolean): pass_thru,
	(int, Byte): pass_thru,
	(str, Character): w2p_string,
	(str, Rune): pass_thru,
	(int, Integer2): pass_thru,
	(int, Integer4): pass_thru,
	(int, Integer8): pass_thru,
	(int, Unsigned2): pass_thru,
	(int, Unsigned4): pass_thru,
	(int, Unsigned8): pass_thru,
	(float, Float4): pass_thru,
	(float, Float8): pass_thru,
	(str, Block): w2p_block,
	(str, String): w2p_string,
	(str, Unicode): pass_thru,
	(str, ClockTime): w2p_clock,
	(str, TimeSpan): w2p_span,
	(str, WorldTime): w2p_world,
	(str, TimeDelta): w2p_delta,
	(str, UUID): w2p_uuid,
	(str, Enumeration): w2p_enumeration,
	(list, ArrayOf): w2p_array,
	(list, VectorOf): w2p_vector,
	(list, SetOf): w2p_set,
	(list, MapOf): w2p_map,
	(list, DequeOf): w2p_deque,
	(list, TargetAddress): w2p_target,
	(list, Address): w2p_address,
	(int, Address): w2p_address,
	(str, PointerTo): w2p_pointer,

	# Two mechanisms for including messages
	# and the representation of message type.
	(dict, UserDefined): w2p_message,
	(list, Any): w2p_any,
	(str, Type): w2p_type,

	# Support for Word, i.e. passthru anything
	# that could have been produced by generic
	# layer. No iterating nested layers.

	(bool, Word): pass_thru,
	(int, Word): pass_thru,
	(float, Word): pass_thru,
	(str, Word): pass_thru,
	(list, Word): pass_thru,
	(dict, Word): pass_thru,

	# Provide for null values being
	# presented for different universal
	# types.

	(NoneType, Boolean): pass_thru,
	(NoneType, Byte): pass_thru,
	(NoneType, Character): pass_thru,
	(NoneType, Rune): pass_thru,
	(NoneType, Integer2): pass_thru,
	(NoneType, Integer4): pass_thru,
	(NoneType, Integer8): pass_thru,
	(NoneType, Unsigned2): pass_thru,
	(NoneType, Unsigned4): pass_thru,
	(NoneType, Unsigned8): pass_thru,
	(NoneType, Float4): pass_thru,
	(NoneType, Float8): pass_thru,
	(NoneType, Block): pass_thru,
	(NoneType, String): pass_thru,
	(NoneType, Unicode): pass_thru,
	(NoneType, WorldTime): pass_thru,
	(NoneType, ClockTime): pass_thru,
	(NoneType, TimeSpan): pass_thru,
	(NoneType, UUID): pass_thru,
	(NoneType, Enumeration): pass_thru,
	# DO NOT allow the automatic acceptance
	# of None as a structured value.
	# (NoneType, UserDefined): pass_thru,
	# (NoneType, ArrayOf): pass_thru,
	# (NoneType, VectorOf): pass_thru,
	# (NoneType, SetOf): pass_thru,
	# (NoneType, MapOf): pass_thru,
	# (NoneType, DequeOf): pass_thru,
	(NoneType, PointerTo): pass_thru,
	(NoneType, Type): pass_thru,
	(NoneType, TargetAddress): pass_thru,
	(NoneType, Address): pass_thru,
	(NoneType, Word): pass_thru,
	(NoneType, Any): pass_thru,
}

#
#
def word_to_python(c, w, t):
	"""Transform generic word to an instance of application data.

	:param c: the active codec
	:type c: an Ansar Codec
	:param w: the portable data
	:type w: generic word
	:param t: the portable description of `w`
	:type t: a portable expression
	:return: application data.
	"""
	try:
		a = w.__class__	 # The generic type.
	except AttributeError:
		a = None

	try:
		b = t.__class__	 # One of the universal types.
	except AttributeError:
		b = None

	if a is None:
		if b is None:
			raise TypeError('data and specification are unusable')
		raise TypeError(f'data with specification "{b.__name__}" is unusable')
	elif b is None:
		raise TypeError(f'specification with data "{a.__name__}" is unusable')

	try:
		f = w2p[a, b]
	except KeyError:
		raise TypeError(f'no transformation for data/specification {a.__name__}/{b.__name__}')

	return f(c, w, t)

# The base class for all codecs and essentially a
# wrapping around 2 functions;
# 1. word to text representation (w2t)
# 2. text representation to word (t2w - parsing)

STARTING_ALIAS = 1100

class Codec(object):
	"""Base class for all codecs, e.g. CodecJson."""

	def __init__(self,
			extension,
			w2t,
			t2w,
			return_proxy, local_termination, pretty_format, decorate_names):
		"""Construct the codec.

		:param extension: the additional text added to file names, e.g. ``json``
		:type extension: str
		:param w2t: the low-level conversion of application data to its text representation
		:type w2t: function
		:param t2w: the low-level parsing of text back to application data.
		:type t2w: function
		:param return_proxy: an address that the codec will use to transform deserialized addresses.
		:type return_proxy: internal
		:param local_termination: an address the codec will use to transform deserialized, “to” addresses.
		:type local_termination: internal
		:param pretty_format: generate a human-readable layout, defaults to ``True``
		:type pretty_format: bool
		:param decorate_names: auto-append a dot-extension suffix, defaults to ``True``
		:type decorate_names: bool
		"""
		self.extension = extension
		self.w2t = w2t
		self.t2w = t2w

		if return_proxy is None:
			self.return_proxy = 0
		elif not isinstance(return_proxy, tuple) or len(return_proxy) != 1:
			raise CodecUsageError('unusable address passed as return proxy')
		else:
			self.return_proxy = return_proxy[0]

		if local_termination is None:
			self.local_termination = 0
		elif not isinstance(local_termination, tuple) or len(local_termination) != 1:
			raise CodecUsageError('unusable address passed as local termination')
		else:
			self.local_termination = local_termination[0]

		self.pretty_format = pretty_format
		self.decorate_names = decorate_names

		self.space = None

		# Encode/decode collections
		self.walking_stack = []
		self.aliased_pointer = {}		   # Encoding.
		self.portable_pointer = {}		  # Both.
		self.pointer_reference = set()
		self.decoded_pointer = {}		   # Decoding.
		self.patch_work = []
		self.pointer_alias = STARTING_ALIAS
		self.alias_space = 'default'

	def encode(self, value, expression, space=None):
		"""Encode an application value to its portable representation.

		:param value: a runtime application value
		:type value: a type consistent with the specified `expression`
		:param expression: a formal description of the `value`
		:type expression: :ref:`type expression<type-expressions>`
		:param version: an explicit version override
		:type version: string
		:return: a portable representation of the `value`
		:rtype: str
		"""
		self.space = space
		self.walking_stack = []		 # Breadcrumbs for m.a[0].f.c[1] tracking.
		self.aliased_pointer = {}	   # Pointers encountered in value.
		self.portable_pointer = {}	  # Pointers accumulated from Incognitos.
		self.any_stack = [set()]
		self.pointer_alias = STARTING_ALIAS

		u4 = uuid.uuid4()
		self.alias_space = str(u4)

		try:
			# Convert the value to a generic intermediate
			# representation.

			w = python_to_word(self, value, expression)
		except (AttributeError, TypeError, ValueError, IndexError, KeyError,
				EnumerationRuntimeError, ConversionEncodeError) as e:
			text = self.nesting()
			if len(text) == 0:
				e = str(e)
				raise CodecRuntimeError(f'transformation ({e})')
			raise CodecRuntimeError(f'transformation, near "{text}" ({e})')

		# Create a dict with value, address and version.
		shipment = {'value': w}
		if len(self.aliased_pointer) > 0:
			# New pointers in the p2w transformations. Need to add them
			# to the older accumulated pointer materials (i.e. Incognitos).
			a = {v[0]: v[1] for _, v in self.aliased_pointer.items()}
			self.portable_pointer.update(a)

		if len(self.portable_pointer) > 0:
			# Pointers in the outbound encoding. Need to
			# flatten then into generic form.
			shipment['pointer'] = [[k, v] for k, v in self.portable_pointer.items()]

		try:
			# Convert generic form to portable
			# representation.

			s = self.w2t(self, shipment)
		except (TypeError, ValueError) as e:
			e = str(e)
			raise CodecRuntimeError(f'serialization ({e})')
		return s

	def decode(self, representation, expression, space=None):
		"""Decode a representation to its final application form.

		:param representation: the result of a previous encode operation
		:type representation: str
		:param expression: a formal description of portable
		:type expression: a :ref:`type expression<type-expressions>`
		:return: an application value
		"""
		self.space = space

		self.walking_stack = []		 # Breadcrumbs for m.a[0].f.c[1] tracking.
		self.portable_pointer = {}	  # Shipped pointer materials.
		self.decoded_pointer = {}	   # Pointers transformed to final type.
		self.patch_work = []

		try:
			# Convert portable representation into generic
			# intermediate form.
			shipment = self.t2w(self, representation)
		except (TypeError, ValueError) as e:
			raise CodecRuntimeError('parsing (%s)', str(e))

		# Now everything is in the generic form. Need to rebuild python
		# types in steps due to work around pointers.
		def decode(w, expression):
			self.walking_stack = []		 # Error tracking.
			self.pointer_reference = set()
			try:
				p = word_to_python(self, w, expression)
			except (AttributeError, TypeError, ValueError, IndexError, KeyError,
					EnumerationRuntimeError, ConversionDecodeError) as e:
				text = self.nesting()
				if len(text) == 0:
					e = str(e)
					raise CodecRuntimeError(f'transformation ({e})')
				raise CodecRuntimeError(f'transformation, near "{text}" ({e})')
			return p

		try:
			# Pull the address pointer-to materials out
			# and save into convenient map. Does not transform
			# into final types.
			flat = shipment['pointer']
			portable = decode(flat, MapOf(Word(), Word()))
			self.portable_pointer.update(portable)  # Use EXISTING portable_pointer
		except KeyError:
			pass
		except (AttributeError, TypeError, ValueError, IndexError):
			raise CodecRuntimeError('unexpected input (not the output of an encoding?)')

		try:
			w = shipment['value']
		except KeyError:
			raise CodecRuntimeError('no "value" available')

		# Decode the word to its final application resting-place. This performs
		# transforms into final types, including the pointer materials. Backpatch
		# any circular references.
		p = decode(w, expression)
		for b in self.patch_work:
			decoded = self.decoded_pointer[b[0]]
			f = b[1]
			f(decoded)

		return p

	def nesting(self):
		"""Use the internal stack to generate a data path."""
		p = ''
		for s in self.walking_stack:
			if isinstance(s, int):
				p += '[%d]' % (s,)
			elif isinstance(s, str):
				if len(p) > 0:
					p += '.'
				p += '%s' % (s,)
			else:
				p += '<?>'
		return p

	def full_name(self, name):
		"""Augment the name with an extension, as appropriate."""
		if not self.decorate_names:
			return name
		if name[-1] == '.':
			return name[:-1]
		s = '%s.%s' % (name, self.extension)
		return s
