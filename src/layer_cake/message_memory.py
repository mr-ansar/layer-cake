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

"""Registration of messages.

Bind additional information about a message to its class definition. This
includes more complete type information about its members but also settings
associated with how an instance of the message should be treated, e.g. during
logging.

.. autoclass:: Message
.. autoclass:: Unknown
.. autoclass:: Incognito

.. autofunction:: default_clock
.. autofunction:: default_span
.. autofunction:: default_world
.. autofunction:: default_delta
.. autofunction:: default_uuid
.. autofunction:: default_array
.. autofunction:: default_vector
.. autofunction:: default_set
.. autofunction:: default_map
.. autofunction:: default_deque
.. autofunction:: default_none

.. autofunction:: bind_message

.. autofunction:: is_message
.. autofunction:: is_message_class
.. autofunction:: equal_to
"""

__docformat__ = 'restructuredtext'

import typing
import uuid
from datetime import MINYEAR, datetime, timedelta
from enum import Enum
from .virtual_memory import *
from .convert_memory import *
from .convert_type import *
from .virtual_runtime import *

__all__ = [
	'MessageError',
	'MessageRegistrationError',
	'TypeTrack',
	'correct_track',

	'Message',
	'Unknown',
	'Incognito',

	'DEFAULT_STRING',
	'DEFAULT_UNICODE',
	'DEFAULT_CLOCK',
	'DEFAULT_SPAN',
	'DEFAULT_WORLD',
	'DEFAULT_DELTA',
	'DEFAULT_ZONE',
	'DEFAULT_UUID',

	# No parameters.
	'default_byte',
	'default_character',
	'default_rune',
	'default_block',
	'default_string',
	'default_unicode',
	'default_clock',
	'default_span',
	'default_world',
	'default_delta',
	'default_uuid',
	'default_vector',
	'default_set',
	'default_map',
	'default_deque',
	'default_none',

	# Require parameters.
	'default_array',

	'fix_expression',
	'is_message',
	'is_message_class',
	'compile_schema',

	'MessageRuntime',
	'bind_message',
	'equal_to',
]

# Exceptions
#
class MessageError(Exception):
	"""Base exception for all message exceptions."""

class MessageRegistrationError(MessageError):
	"""A request to register a class cannot be fulfilled.

	:param name: the name of the class being registered
	:type name: str
	:param reason: a short description
	:type reason: str
	"""

	def __init__(self, name, reason):
		"""Refer to class."""
		self.name = name
		self.reason = reason
		super().__init__(reason)

	def __str__(self):
		"""Compose a readable diagnostic."""
		if self.name:
			return f'cannot register "{self.name}" ({self.reason})'
		return f'registration failed ({self.reason})'

# Holds nested names that would be helpful in the event
# of an error.
class TypeTrack(Exception):
	"""Construct a readable name for a message.member.member, during exceptions."""

	def __init__(self, name, reason):
		"""Keep building the trace."""
		super().__init__(reason)
		if name:
			self.path = [name]
		else:
			self.path = []
		self.reason = reason

def correct_track(e):
	"""Generate a readable version of a TypeTrack exception."""
	t = '.'.join(reversed(e.path))
	return t

#
#
class Message(object):
	"""Internal placeholder class used for dispatching."""

class Unknown(object):
	"""An abstract class used to indicate an unexpected message."""

class Incognito(object):
	"""A class that holds the recovered materials of an unregistered message.

	:param type_name: portable identity of the associated word
	:type type_name: str
	:param decoded_word: parsed but unmarshaled object
	:type decoded_word: word
	"""

	def __init__(self, type_name=None, decoded_word=None, saved_pointers=None):
		"""Refer to class."""
		self.type_name = type_name
		self.decoded_word = decoded_word
		self.saved_pointers = saved_pointers

# A group of functions that exist to allow type descriptions for
# messages to make use of *classes* rather than *instances* of those
# classes;
#	 VectorOf(Float8)
# instead of;
#	 VectorOf(Float8())
# Unclear on best design/engineering response to the issue but
# certainly this results in fewer parentheses and quicker development.
# Fully correct declaration of user-defined messages quite verbose
# and consequently less clear;
#	 VectorOf(SomeMessage)
# vs;
#	 VectorOf(UserDefined(SomeMessage))

# Default initializers (i.e. no parameters available) for tricky
# types. Want an instance of the type but preferrably without
# side-effects and at the least cost. Most containers need
# a fresh instance of themselves (i.e. list,
# deque...) but other types are objects that are immutable,
# such as bytes and datetime. These can be initialized with a
# single constant value to reduce the cycles consumed by
# initialization. This whole issue is further complicated by
# the merging of the two type systems - ansar and python - and
# how String does not map to str.

# Immutable initializer constants.
DEFAULT_STRING = bytes()
DEFAULT_UNICODE = str()
DEFAULT_CLOCK = float(0)
DEFAULT_SPAN = float(0)
DEFAULT_WORLD = datetime(MINYEAR, 1, 1)
DEFAULT_DELTA = timedelta()
DEFAULT_ZONE = UTC
DEFAULT_UUID = uuid.uuid4()

def default_byte():
	"""Initialize the smallest, integer value, i.e. ``Byte``.

	:return: byte
	:rtype: int
	"""
	return int()

def default_character():
	"""Initialize a single, printable character, i.e. ``Character``.

	:return: character
	:rtype: bytes
	"""
	return b' '

def default_rune():
	"""Initialize a single Unicode codepoint, i.e. ``Unicode``.

	:return: codepoint
	:rtype: str
	"""
	return ' '

def default_block():
	"""Initialize a sequence of the smallest integers, i.e. ``Block``.

	:return: fresh instance of an empty block
	:rtype: bytearray
	"""
	return bytearray()  # New object every time.

def default_string():
	"""Initialize a sequence of printable characters, i.e. ``String``.

	:return: an empty sequence of characters
	:rtype: bytes
	"""
	return DEFAULT_STRING

def default_unicode():
	"""Initialize a sequence of Unicode codepoints, i.e. ``Unicode``.

	:return: empty sequence of codepoints
	:rtype: str
	"""
	return DEFAULT_UNICODE

def default_clock():
	"""Initialize a local time variable, i.e. ``ClockTime``.

	:return: the beginning of time
	:rtype: datetime
	"""
	return DEFAULT_CLOCK

def default_span():
	"""Initialize a local time difference variable, i.e. ``TimeSpan``.

	:return: no time
	:rtype: timedelta
	"""
	return DEFAULT_SPAN

def default_world():
	"""Initialize a date-and-time variable, i.e. ``WorldTime``.

	:return: the beginning of time
	:rtype: datetime
	"""
	return DEFAULT_WORLD

def default_delta():
	"""Initialize a date-and-time delta variable, i.e. ``TimeDelta``.

	:return: no time
	:rtype: timedelta
	"""
	return DEFAULT_DELTA

def default_uuid():
	"""Initialize a UUID variable.

	:return: a global, constant UUID value
	:rtype: uuid.UUID
	"""
	return DEFAULT_UUID

def default_array(value, size):
	"""Initialize a vector variable.

	:return: a fresh, empty vector
	:rtype: list
	"""
	return [value] * size   # New object.

def default_vector():
	"""Initialize a vector variable.

	:return: a fresh, empty vector
	:rtype: list
	"""
	return list()   # New object.

def default_set():
	"""Initialize a set variable.

	:return: a fresh, empty set
	:rtype: set
	"""
	return set()

def default_map():
	"""Initialize a map variable.

	:return: a fresh, empty map
	:rtype: dict
	"""
	return dict()

def default_deque():
	"""Initialize a deque variable.

	:return: a fresh, empty double-ended queue
	:rtype: collections.deque
	"""
	return deque()

def default_none():
	return None

# Allow the use of basic python types
# in type expressions.
CONVERT_PYTHON = {
	bool: Boolean(),
	int: Integer8(),
	float: Float8(),
	str: Unicode(),
	bytes: String(),
	bytearray: Block(),
	datetime: WorldTime(),
	timedelta: TimeDelta(),
	uuid.UUID: UUID(),
}

# NEEDS TO BE DROPPED
# Legacy requirement in the arg processing for
# the Utility class.
def fix_expression(a, bread=None):
	"""Promote parameter a from class to instance, as required."""
	if bread is None:
		bread = {}

	if is_portable(a):
		if not is_container(a):
			return a	# No change.
		# Fall thru for structured processing.
	elif is_portable_class(a):
		if not is_container_class(a):
			return a()  # Promotion of simple type.
		raise TypeTrack(a.__name__, 'container class used in type information, instance required')
	elif is_message_class(a):
		return UserDefined(a)
	else:
		# Is it one of the mapped Python classes.
		try:
			e = CONVERT_PYTHON[a]
			return e
		except KeyError:
			pass
		except TypeError:   # Unhashable - list.
			pass
		# Is it an instance of a mapped Python class.
		try:
			e = CONVERT_PYTHON[a.__class__]
			return e
		except KeyError:
			pass
		except AttributeError:   # No class.
			pass
		raise TypeTrack(None, 'not one of the portable types')

	# We have an instance of a structuring.
	try:
		name = a.__class__.__name__
		if isinstance(a, ArrayOf):
			a.element = fix_expression(a.element, bread)
		elif isinstance(a, VectorOf):
			a.element = fix_expression(a.element, bread)
		elif isinstance(a, SetOf):
			a.element = fix_expression(a.element, bread)
		elif isinstance(a, MapOf):
			a.key = fix_expression(a.key, bread)
			a.value = fix_expression(a.value, bread)
		elif isinstance(a, DequeOf):
			a.element = fix_expression(a.element, bread)
		elif isinstance(a, UserDefined):
			if not is_message_class(a.element):
				raise TypeTrack(None, '"%s" is not a user-defined message' % (name,))
		elif isinstance(a, PointerTo):
			try:
				e = bread[id(a)]
			except KeyError:
				e = fix_expression(a.element, bread)
				bread[id(a)] = e
			a.element = e
		else:
			raise TypeTrack(None, 'unexpected container type')
	except TypeTrack as e:
		e.path.append(name)
		raise e
	return a

def override(name, explicit):
	"""Is there explicit information for the named item.

	:param name: name of the message
	:type name: str
	:param explicit: a supplied schema
	:type explicit: a map of <name, portable declaration> pairs
	:return: the explicit information or None
	"""
	if not explicit:
		return None

	try:
		t = explicit[name]
		return t
	except KeyError:
		return None

def infer_type(a):
	"""Map an instance of a Python type to the proper memory description, or None."""
	try:
		t = CONVERT_PYTHON[a.__class__]
		return t
	except AttributeError:
		return None	 # No class.
	except KeyError:
		pass
	if is_message(a):
		return UserDefined(a.__class__)
	return None

def compile_schema(message, explicit_schema):
	"""Produce the best-possible type information for the specified message.

	Use the class and the application-supplied declarations. The
	declarations override any default info that might otherwise be
	acquired from the message.
	"""
	name = message.__name__
	hints = typing.get_type_hints(message)
	class_hints, _ = install_hints(hints)
	if hasattr(message, '__init__'):
		hints = typing.get_type_hints(message.__init__)
		init_hints, init_return = install_hints(hints)
		if init_return:
			raise MessageRegistrationError(name, 'returns value from ctor')

	hint_schema = class_hints or init_hints
	explicit_schema = {k: install_portable(v) for k, v in explicit_schema.items()}

	try:
		m = message()
	except TypeError:
		raise MessageRegistrationError('%s' % (name,), 'not default constructable')
	d = getattr(m, '__dict__', None)
	r = {}
	if d:
		for k, a in d.items():
			t = hint_schema.get(k, None)
			if t is None:
				t = override(k, explicit_schema)
				if t is None:
					t = infer_type(a)

			if not t:
				name_k = f"{name}.{k}"
				reason = 'not enough type information provided/discoverable'
				raise MessageRegistrationError(name_k, reason)
			r[k] = t
	return r

#
#
class MessageRuntime(Runtime):
	"""Settings to control logging and other behaviour, for objects and messages."""

	def __init__(self,
			name, module, schema,
			**flags):
		"""Construct the settings.

		:param name: the name of the class being registered
		:type name: str
		:param module: the name of the module the class is located in
		:type module: str
		:param value: the application value, e.g. a function
		:type value: any
		:param lifecycle: enable logging of created, destroyed
		:type lifecycle: bool
		:param message_trail: enable logging of sent
		:type message_trail: bool
		:param execution_trace: enable logging of received
		:type execution_trace: bool
		:param copy_before_sending: enable auto-copy before send
		:type copy_before_sending: bool
		:param not_portable: prevent inappropriate send
		:type not_portable: bool
		:param user_logs: log level
		:type user_logs: int
		"""
		super().__init__(name, module, **flags)
		self.schema = schema

def bind_message(message,
		message_trail=True, execution_trace=True,
		copy_before_sending=True, not_portable=False,
		**object_schema):
	"""Set the type information and runtime controls for the given message type.

	:param message: a message class.
	:type message: class
	:param object_schema: application-supplied type information.
	:type object_schema: a map of <name,portable declaration> pairs.
	:param message_trail: log every time this message is sent.
	:type message_trail: bool
	:param execution_trace: log every time this message is received.
	:type execution_trace: bool
	:param copy_before_sending: make a copy of the message before each send.
	:type copy_before_sending: bool
	:param not_portable: prevent serialization/transfer, e.g. of a file handle.
	:type not_portable: bool
	:param object_schema: explicit type declarations by name.
	:type object_schema: dict
	:return: nothing.

	Values assigned in this function affect the behaviour for all instances of
	the given type.
	"""
	rt = MessageRuntime(message.__name__, message.__module__, None,
		message_trail=message_trail,
		execution_trace=execution_trace,
		copy_before_sending=copy_before_sending,
		not_portable=not_portable)

	setattr(message, '__art__', rt)
	if not not_portable:
		rt.schema = compile_schema(message, object_schema)
	
	install_portable(UserDefined(message))

# This should not need be needed (Incognito) as they are never
# on-the-wire. But registration needed for dispatching within
# encode/decode process.
bind_message(Unknown)
bind_message(Incognito,
	type_name=Unicode,
	decoded_word=Word,
	saved_pointers=MapOf(Unicode, Word))

#
#
def is_message(m):
	"""Is *m* an instance of a registered class; return a bool."""
	try:
		c = m.__class__
	except AttributeError:
		return False
	b = hasattr(c, '__art__')
	return b

def is_message_class(c):
	"""Has *c* been registered with the library; return a bool."""
	try:
		p = c.__class__	 # Parent class.
	except AttributeError:
		return hasattr(c, '__art__')
	a = getattr(c, '__art__', None)
	b = a is not None and a.name == c.__name__
	return b

def equal_to(a, b, t=None):
	"""Compare the two operands as instances of portable memory."""
	if t is None:
		if not is_message(b):
			return a == b
		if not isinstance(a, b.__class__):
			return False
		t = UserDefined(b.__class__)

	if isinstance(t, ArrayOf):
		if len(a) != len(b):
			return False
		return all(equal_to(i, j, t.element) for i, j in zip(a, b))
	elif isinstance(t, VectorOf):
		if len(a) != len(b):
			return False
		return all(equal_to(i, j, t.element) for i, j in zip(a, b))
	elif isinstance(t, DequeOf):
		if len(a) != len(b):
			return False
		return all(equal_to(i, j, t.element) for i, j in zip(a, b))
	elif isinstance(t, SetOf):
		# if len(a) != len(b):
		#	return False
		# return all(i in a for i in b)
		return a == b
	elif isinstance(t, MapOf):
		if len(a) != len(b):
			return False
		return all(k in b and equal_to(a[k], v, t.value) for k, v in b.items())
	elif isinstance(t, UserDefined):
		x = t.element.__art__
		for k, v in x.schema.items():
			try:
				lhs = getattr(a, k)
				rhs = getattr(b, k)
			except AttributeError:
				return False
			if not equal_to(lhs, rhs, v):
				return False
		return True
	elif isinstance(t, PointerTo):
		# Difficult issue. Have to consider circular
		# references and graphs, i.e. infinite loops.
		# Its also true that its intended for comparision
		# of messages and 2 messages should never, ever
		# refer to common data.
		return False
	elif isinstance(t, Any):
		if equal_to(a, b):
			return True
		return False
	else:
		return a == b

def type_equal_to(a, b):
	"""Compare the two operands as instances of portable memory."""
	if isinstance(a, Portable):
		if isinstance(a, Container):
			pass
		else:
			return a.__class__ == b.__class__

	if isinstance(a, (VectorOf, DequeOf, SetOf, PointerTo)):
		return type_equal_to(a.element, b.element)
	elif isinstance(a, ArrayOf):
		return type_equal_to(a.element, b.element) and a.size == b.size
	elif isinstance(a, MapOf):
		return type_equal_to(a.key, b.key) and type_equal_to(a.value, b.value)
	elif isinstance(a, (Enumeration, UserDefined)):
		return a.element == b.element
	elif isinstance(a, Any):
		return isinstance(b, Any())
	else:
		return a == b
