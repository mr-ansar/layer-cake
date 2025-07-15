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

"""Storage and recovery of application data using system files.

Two primitives - write_to_file and read_from_file - and the File
class to package the common usage patterns.

.. autofunction:: write_to_file
.. autofunction:: read_from_file

.. autoclass:: File
   :members: store, recover
   :member-order: bysource
"""

__docformat__ = 'restructuredtext'

__all__ = [
	'File',
	'read_from_file',
	'write_to_file',
]

import os

from .virtual_memory import *
from .message_memory import *
from .convert_type import *
from .make_message import *
from .virtual_codec import *
from .json_codec import *

#
#
class File(object):
	"""Store and recover application values using files.

	:param name: name of the file
	:type name: str
	:param tip: type expression for the content
	:type tip: :ref:`tip<layer-cake-type-reference>`
	:param encoding: selection of representation, defaults to ``CodecJson``
	:type encoding: class
	:param create_default: return default instance if file not found on read, defaults to ``False``
	:type create_default: bool
	:param pretty_format: generate human-readable file contents, defaults to ``True``
	:type pretty_format: bool
	:param decorate_names: auto-append an encoding-dependent extension to the file name, defaults to ``True``
	:type decorate_names: bool
	"""
	def __init__(self, name, tip, encoding=None, create_default=False, pretty_format=True, decorate_names=True):
		"""Not published."""
		self.name = name

		if tip is None:
			self.file_type = None
		elif isinstance(tip, Portable):
			self.file_type = tip
		elif hasattr(tip, '__art__'):
			self.file_type = UserDefined(tip)
		else:
			self.file_type = lookup_type(tip)

		self.encoding = encoding
		self.create_default = create_default
		self.pretty_format = pretty_format
		self.decorate_names = decorate_names

	def store(self, value, as_name=None, as_path=None):
		"""Generate a representation of ``value`` and write to the saved ``name``.

		:param value: any application value
		:type value: matching the saved type expression
		:return: none
		"""
		if as_path:
			if as_name:
				name = os.path.join(as_path, as_name)
			else:
				h, t = os.path.split(self.name)
				name = os.path.join(as_path, t)
		elif as_name:
			h, t = os.path.split(self.name)
			name = os.path.join(h, as_name)
		else:
			name = self.name

		write_to_file(value, name, self.file_type, encoding=self.encoding,
			decorate_names=self.decorate_names, pretty_format=self.pretty_format)

	def recover(self, *args, **kwargs):
		"""Read from the saved ``name``, parse and marshal into an application value.

		:param args: remaining positional parameters
		:type args: tuple
		:param kwargs: remaining named parameters
		:type kwargs: dict
		:return: 2-tuple of an application value and a version.
		:rtype: value matching the saved ``expression`` and a ``str``
		"""
		try:
			r = read_from_file(self.file_type, self.name, encoding=self.encoding, decorate_names=self.decorate_names)
		except FileNotFoundError:
			if self.create_default:
				c = self.file_type
				a = make(c)
				return a
			raise
		return r

	def full_name(self, encoding=None):
		encoding = encoding or self.encoding or CodecJson
		encoding = encoding(decorate_names=self.decorate_names)
		return encoding.full_name(self.name)

	def remove(self):
		name = self.full_name()
		try:
			os.remove(name)
		except FileNotFoundError:
			return False
		return True

# The primitives.
def read_from_file(expression, name, encoding=None, **kv):
	"""Recover an application object from the representation loaded from the named file."""
	encoding = encoding or CodecJson
	encoding = encoding(**kv)

	# Add the encoding suffix according
	# to automation settings.
	name = encoding.full_name(name)

	with open(name, 'r') as f:
		s = f.read()

	d = encoding.decode(s, expression)
	return d

#
#
def write_to_file(a, name, expression=None, encoding=None, pretty_format=True, **kv):
	"""Write a representation of the application date into the named file."""
	kv['pretty_format'] = pretty_format
	encoding = encoding or CodecJson
	encoding = encoding(**kv)

	# Add the encoding suffix according
	# to automation settings.
	name = encoding.full_name(name)

	if expression is None:
		if not is_message(a):
			raise CodecUsageError(f'encoding of unregistered message to file "{name}"')
		expression = UserDefined(a.__class__)

	s = encoding.encode(a, expression)

	with open(name, 'w') as f:
		f.write(s)
