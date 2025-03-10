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

"""Management of types - Python hints, library types and a signature set.

This is partly about the conversion of Python hints into usable library types
and partly about conversion of types to-and-from a signature representation (i.e. a
portable string representation of a library type). At the same time there is
a need to collapse all instances of a certain type into a single instance for
the purposes of comparison, i.e. control flow, dispatching.
"""

import typing
import types

__all__ = [
	'convert_hint',
]

from .virtual_memory import *
from .virtual_runtime import *
from .convert_signature import *
from collections import deque
from datetime import datetime, timedelta
import uuid

# Map of signature-to-type, ensuring the same type
# instance is in use at runtime.

# Direct mapping from Python hint to
# library type.
SIMPLE_HINT = {
	bool: Boolean(),
	int: Integer8(),
	float: Float8(),
	str: Unicode(),
	bytes: String(),
	bytearray: Block(),
	datetime: WorldTime(),
	timedelta: TimeDelta(),
	uuid.UUID: UUID(),
	Any: Any(),
}

def convert_hint(hint):
	"""Map a Python type hint to the proper memory description, or None."""

	if hint == types.NoneType:
		return None

	def get():
		t = SIMPLE_HINT.get(hint, None)
		if t is not None:
			return t

		if isinstance(hint, types.GenericAlias):
			c = hint.__origin__
			a = hint.__args__
			if c == list:
				if len(a) != 1:
					raise PointConstructionError(f'expected an argument for type "{c.__name__}"')
				a0 = convert_hint(a[0])
				return VectorOf(a0)
			elif c == dict:
				if len(a) != 2:
					raise PointConstructionError(f'expected key and value arguments for type "{c.__name__}"')
				a0 = convert_hint(a[0])
				a1 = convert_hint(a[1])
				return MapOf(a0, a1)
			elif c == set:
				if len(a) != 1:
					raise PointConstructionError(f'expected an argument for type "{c.__name__}"')
				a0 = convert_hint(a[0])
				return SetOf(a0)
			elif c == deque:
				if len(a) != 1:
					raise PointConstructionError(f'expected an argument for type "{c.__name__}"')
				a0 = convert_hint(a[0])
				return DequeOf(a0)
		elif hint == typing.Any:
			return None
		return UserDefined(hint)

	t = get()
	if t is None:
		return None
	s = portable_to_signature(t)
	return lookup_signature(s, candidate=t)
