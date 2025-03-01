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

"""A virtual memory model.

.. autoclass:: Boolean

.. autoclass:: Integer2
.. autoclass:: Integer4
.. autoclass:: Integer8
.. autoclass:: Unsigned2
.. autoclass:: Unsigned4
.. autoclass:: Unsigned8

.. autoclass:: Float4
.. autoclass:: Float8

.. autoclass:: Byte
.. autoclass:: Character
.. autoclass:: Rune
.. autoclass:: Block
.. autoclass:: String
.. autoclass:: Unicode

.. autoclass:: Enumeration

.. autoclass:: ClockTime
.. autoclass:: TimeSpan
.. autoclass:: WorldTime
.. autoclass:: TimeDelta

.. autoclass:: UUID

.. autoclass:: ArrayOf
.. autoclass:: VectorOf
.. autoclass:: SetOf
.. autoclass:: MapOf
.. autoclass:: DequeOf

.. autoclass:: UserDefined
.. autoclass:: Type
.. autoclass:: PointerTo

.. autoclass:: TargetAddress
.. autoclass:: Address

.. autoclass:: Word
.. autoclass:: Any

.. autofunction:: is_portable
.. autofunction:: is_container
.. autofunction:: is_portable_class
.. autofunction:: is_container_class
.. autofunction:: is_address
"""

__docformat__ = 'restructuredtext'

from collections import deque

__all__ = [
	# Classification.
	'Portable', 'Container',

	# Logical.
	'Boolean',

	# Integers.
	'Integer2', 'Integer4', 'Integer8',
	'Unsigned2', 'Unsigned4', 'Unsigned8',

	# Floats.
	'Float4', 'Float8',

	# Bytes, ASCII and unicode.
	'Byte', 'Character', 'Rune',
	'Block', 'String', 'Unicode',

	# Name for a number.
	'Enumeration',

	# Time.
	'ClockTime', 'TimeSpan',
	'WorldTime', 'TimeDelta',

	'UUID',

	# Containers.
	'ArrayOf', 'VectorOf', 'DequeOf',
	'SetOf', 'MapOf',

	'UserDefined',
	'PointerTo',
	'Any',

	# Networking.
	'TargetAddress',
	'Address',

	# Internal.
	'Type',
	'Word',

	# Supporting.
	'VIRTUAL_MEMORY_LIST',
	'VIRTUAL_MEMORY_SET',

	'deque',

	'is_portable',
	'is_container',
	'is_structural',
	'is_portable_class',
	'is_container_class',

	'NO_SUCH_ADDRESS',

	'is_address',
	'address_on_proxy',
]

class Portable(object):
	"""Base for all portables."""

class Container(Portable):
	"""The subset of portables that hold zero or more portables."""

# A unit of memory.
class Boolean(Portable):
	"""True or false."""

class Integer2(Portable):
	"""A 2-byte, signed integer."""

class Integer4(Portable):
	"""A 4-byte, signed integer."""

class Integer8(Portable):
	"""An 8-byte, signed integer."""

class Unsigned2(Portable):
	"""A 2-byte, unsigned integer."""

class Unsigned4(Portable):
	"""A 4-byte, unsigned integer."""

class Unsigned8(Portable):
	"""An 8-byte, unsigned integer."""

class Float4(Portable):
	"""A 4-byte, floating point number."""

class Float8(Portable):
	"""An 8-byte, floating point number."""

class Byte(Portable):
	"""The smallest unit of data - 8 bit, unsigned integer."""

class Character(Portable):
	"""A byte that more often than not, contains a printable ASCII character."""

class Rune(Portable):
	"""A Unicode codepoint."""

class Block(Portable):
	"""A sequence of Byte."""

class String(Portable):
	"""A sequence of Character."""

class Unicode(Portable):
	"""A sequence of Rune."""

class Enumeration(Container):
	"""Names for integers.

	:param element: entry in the type system.
	:type element: class
	"""

	def __init__(self, element):
		"""Refer to class."""
		self.element = element

class ClockTime(Portable):
	"""The time on the wall clock as an epoch value; a float."""

class TimeSpan(Portable):
	"""Difference between two ``ClockTime`` values; a float."""

class WorldTime(Portable):
	"""The time at the Greenwich meridian; a datetime object."""

class TimeDelta(Portable):
	"""Difference between two ``WorldTime`` values; a timedelta object."""

class UUID(Portable):
	"""An RFC 4122 UUID (random); a ``uuid.UUID`` object."""

class ArrayOf(Container):
	"""A fixed-length sequence of elements.

	:param element: type of the content.
	:type element: :ref:`type expression<type-expressions>`
	:param size: fixed size.
	:type size: int
	"""

	def __init__(self, element, size):
		"""Refer to class."""
		self.element = element
		self.size = size

class VectorOf(Container):
	"""A variable-length sequence of elements.

	:param element: type of the content.
	:type element: :ref:`type expression<type-expressions>`
	"""

	def __init__(self, element):
		"""Refer to class."""
		self.element = element

class DequeOf(Container):
	"""A double-ended sequence of elements.

	:param element: type of the content.
	:type element: :ref:`type expression<type-expressions>`
	"""

	def __init__(self, element):
		"""Refer to class."""
		self.element = element

class SetOf(Container):
	"""A collection of unique elements.

	:param element: type of the content, a hash-able value.
	:type element: :ref:`type expression<type-expressions>`
	"""

	def __init__(self, element):
		"""Refer to class."""
		self.element = element

class MapOf(Container):
	"""A map of unique, key-value pairs.

	:param key: type of the key, a hash-able value.
	:type key: :ref:`type expression<type-expressions>`
	:param value: type of the content.
	:type value: :ref:`type expression<type-expressions>`
	"""

	def __init__(self, key, value):
		"""Refer to class."""
		self.key = key
		self.value = value

class UserDefined(Container):
	"""A structure of named elements.

	:param element: registered class.
	:type element: class
	"""

	def __init__(self, element):
		"""Refer to class."""
		self.element = element

class PointerTo(Container):
	"""An object that refers to another object.

	:param element: type of the object being pointed to.
	:type element: :ref:`type expression<type-expressions>`
	"""

	def __init__(self, element):
		"""Refer to class."""
		self.element = element

class Any(Portable):
	"""The combination of a Type and a Word."""

	def __init__(self, *possibles):
		"""Accept these types in a version-managed scenario."""
		self.possibles = possibles

class TargetAddress(Portable):
	"""The address of a receiving object."""

class Address(Portable):
	"""The address of a sending object."""

class Type(Portable):
	"""The unique, portable identity of a registered message."""

class Word(Portable):
	"""A well-formed but untyped unit of data."""

# List of the library types.
VIRTUAL_MEMORY_LIST = [
	Boolean,
	Integer2, Integer4, Integer8,
	Unsigned2, Unsigned4, Unsigned8,
	Float4, Float8,
	Byte, Character, Rune,
	String, Unicode, Block,
	Enumeration,
	ClockTime, TimeSpan,
	WorldTime, TimeDelta,
	UUID,
	UserDefined,
	ArrayOf, VectorOf, DequeOf,
	SetOf, MapOf,
	PointerTo,
	Any,
	TargetAddress, Address,
	Type,
	Word,
]

# Set of the library types.
VIRTUAL_MEMORY_SET = set(VIRTUAL_MEMORY_LIST)

# Few handy type predicates.
#
def is_portable(a):
	"""Is object *a* an instance of one of the portable types."""
	return isinstance(a, Portable)

def is_container(a):
	"""Is object *a* an instance of one of the portable container types."""
	return isinstance(a, Container)

def is_structural(a):
	"""Is object *a* an instance of one of the portable container types and not a pointer."""
	b = isinstance(a, Container) and not isinstance(a, PointerTo)
	return b

def is_portable_class(c):
	"""Is object *c* one of the portable types."""
	try:
		return issubclass(c, Portable)
	except TypeError:
		return False

def is_container_class(c):
	"""Is object *c* one of the portable container types."""
	try:
		return issubclass(c, Container)
	except TypeError:
		return False

# This is the official null address and where required the
# default value for an address.
NO_SUCH_ADDRESS = (0,)

def is_address(a):
	"""Is object *a* is a valid point address."""
	try:
		return isinstance(a, tuple) and len(a) > 0
	except (TypeError, ValueError):
		return False

def address_on_proxy(a, p):
	"""Check that address *a* refers to an object behind the proxy address, p."""
	if a[-1] == p[-1]:
		if len(p) == 1 and len(a) > 1:
			return True
	return False
