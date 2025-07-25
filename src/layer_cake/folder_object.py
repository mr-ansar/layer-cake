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

"""Manage folders of files containing encodings of application data.

The :class:`~.Folder` class provides for one-time description of folder location and
contents. The description is inherited by any child objects (i.e. ``Files``
and sub-``Folders``) created, and by operations within the folder.

The class also provides for persistence of maps. Rather than using a file
to store an entire map, the :class:`~.Folder` class can be used to store the
map on a one-file-per-entry basis.
"""

__docformat__ = 'restructuredtext'

# .. autoclass:: Folder
#   :members:
#   :no-undoc-members:

__all__ = [
	'Folder',
	'remove_folder',
	'remove_contents',
	'shape_of_folder',
]

import os
import errno
import re as regex

from .virtual_memory import *
from .message_memory import *
from .make_message import *
from .convert_type import *
from .virtual_codec import *
from .json_codec import *
from .file_object import *

#
#
def remove_contents(path):
	"""Delete everything under the given folder, down."""

	for f in os.listdir(path):
		p = os.path.join(path, f)
		if os.path.isdir(p):
			remove_folder(p)
		elif os.path.isfile(p):
			os.remove(p)

def remove_folder(path):
	"""Delete everything under the given folder, and then the folder."""

	remove_contents(path)

	try:
		os.rmdir(path)
	except OSError as e:
		if e.errno == errno.ENOENT:
			return

def shape_of_folder(path):
	"""Walk the given folder, acumulating folders, files and bytes (3-tuple)."""
	folders, files, bytes = 0, 0, 0

	p = path
	for f in os.listdir(path):
		p = os.path.join(path, f)
		if os.path.isdir(p):
			folders += 1
			fo, fi, by = shape_of_folder(p)
			folders += fo
			files += fi
			bytes += by
		elif os.path.isfile(p):
			s = os.stat(p)
			files += 1
			bytes += s.st_size

	return folders, files, bytes

#
#
class Folder(object):
	"""Create and manage a folder of application encodings.

	:param path: the location in the filesystem
	:param tip: type expression for the content
	:type tip: :ref:`tip<layer-cake-type-reference>`
	:param re: formal, regular expression description of expected file names
	:param encoding: selection of representation, defaults to ``CodecJson``
	:type encoding: class
	:param pretty_format: generate human-readable file contents, defaults to ``True``
	:param decorate_names: auto-append an encoding-dependent extension to the file name, defaults to ``True``
	:param keys_names: a key-composer function and a name-composer function
	:type keys_names: 2-tuple of functions
	:param make_absolute: expand a relative path to be an absolute location, defaults to ``True``
	:param auto_create: create folders as necessary, defaults to ``True``
	"""

	def __init__(self, path: str=None,
			tip=None, re: str=None, encoding=None,
			pretty_format: bool=True, decorate_names: bool=True,
			create_default: bool=False, keys_names=None,
			make_absolute: bool=False, auto_create: bool=True):
		"""Construct a Folder instance."""
		path = path or '.'
		if make_absolute:
			path = os.path.abspath(path)
		self.path = path

		if re is None:
			self.re = None
		else:
			self.re = regex.compile(re)

		if tip is None:
			self.file_type = None
		elif isinstance(tip, Portable):
			self.file_type = tip
		elif hasattr(tip, '__art__'):
			self.file_type = UserDefined(tip)
		else:
			self.file_type = lookup_type(tip)

		self.encoding = encoding or CodecJson
		self.pretty_format = pretty_format
		self.decorate_names = decorate_names
		self.create_default = create_default
		self.keys_names = keys_names
		self.auto_create = auto_create

		if not auto_create:
			return
		try:
			os.makedirs(self.path)
		except OSError as e:
			if e.errno == errno.EEXIST:
				return

	def folder(self, name: str, tip=None, re: str=None, encoding=None,
			pretty_format: bool=None, decorate_names: bool=None, create_default: bool=None,
			auto_create: bool=None, keys_names=None):
		"""Create a new :class:`~.Folder` object representing a sub-folder at the current location.

		:param path: the name to be added to the saved ``path``
		:param tip: type expression for the content
		:type tip: :ref:`tip<layer-cake-type-reference>`
		:param re: formal, regular expression description of expected file names
		:param encoding: selection of representation, defaults to ``CodecJson``
		:type encoding: class
		:param pretty_format: generate human-readable file contents, defaults to ``True``
		:param decorate_names: auto-append an encoding-dependent extension to the file name, defaults to ``True``
		:param keys_names: a key-composer function and a name-composer function
		:type keys_names: 2-tuple of functions
		:param make_absolute: expand a relative path to be an absolute location, defaults to ``True``
		:param auto_create: create folders as necessary, defaults to ``None``
		:return: a new location in the filesystem
		:rtype: Folder
		"""
		tip = tip or self.file_type
		if re is None:
			self.re = None
		else:
			self.re = regex.compile(re)
		encoding = encoding or self.encoding
		if pretty_format is None: pretty_format = self.pretty_format
		if decorate_names is None: decorate_names = self.decorate_names
		if create_default is None: create_default = self.create_default
		if auto_create is None: auto_create = self.auto_create
		keys_names = keys_names or self.keys_names

		path = os.path.join(self.path, name)
		return Folder(path, re=re, tip=tip, encoding=encoding,
			pretty_format=pretty_format, decorate_names=decorate_names, create_default=create_default,
			keys_names=keys_names, make_absolute=False, auto_create=auto_create)

	def file(self, name: str, tip=None, encoding=None,
			pretty_format: bool=None, decorate_names: bool=None, create_default: bool=None):
		"""Create a new :class:`~.File` object representing a file at the current location.

		:param name: the name to be added to the saved ``path``
		:param tip: type expression for the content
		:type tip: :ref:`tip<layer-cake-type-reference>`
		:param encoding: selection of representation, defaults to ``CodecJson``
		:type encoding: class
		:param pretty_format: generate human-readable file contents, defaults to ``True``
		:param decorate_names: auto-append an encoding-dependent extension to the file name, defaults to ``True``
		:param create_default: return default instance on file not found, defaults to ``False``
		:return: a new file in the filesystem
		:rtype: File
		"""
		tip = tip or self.file_type
		encoding = encoding or self.encoding
		if pretty_format is None: pretty_format = self.pretty_format
		if decorate_names is None: decorate_names = self.decorate_names
		if create_default is None: create_default = self.create_default

		path = os.path.join(self.path, name)	# Let the I/O operation decorate.
		return File(path, tip, encoding=encoding,
			pretty_format=pretty_format, decorate_names=decorate_names, create_default=create_default)

	def matching(self):
		"""Scan for files in the folder.

		:return: a sequence of filenames matching the :class:`~.Folder` criteria.
		:rtype: str
		"""
		re = self.re
		decorate_names = self.decorate_names
		extension = '.%s' % (self.encoding.EXTENSION,)
		for f in os.listdir(self.path):
			m = None
			p = os.path.join(self.path, f)
			if not os.path.isfile(p):
				continue
			if decorate_names:
				b, e = os.path.splitext(f)
				if e != extension:
					continue
				f = b
			if re:
				m = re.fullmatch(f)
				if not m:
					continue
			yield f

	def each(self):
		"""Process the files in the folder.

		:return: a sequence of :class:`~.File` objects matching the :class:`~.Folder` criteria.
		:rtype: File
		"""
		# Get a fresh image of folder/slice.
		# Use a snapshot for iteration to avoid
		# complications arising from changes to the folder.
		matched = [f for f in self.matching()]
		# Visit each named file.
		# Yield a file object, ready for I/O.
		for f in matched:
			yield self.file(f, tip=self.file_type)

	def store(self, values: dict):
		"""Store a ``dict`` of values as files in the folder.

		:param values: a collection of application values
		"""
		# Get a fresh image of folder/slice.
		matched = set(self.matching())
		stored = set()
		for k, v in values.items():
			name = self.name(v)
			io = self.file(name, tip=self.file_type)
			io.store(v)
			stored.add(name)
		# Clean out files that look like they
		# have been previously written but are
		# no longer in the map.
		matched -= stored
		for m in matched:
			self.erase(m)

	def recover(self):
		"""Recover application values from the files in the folder.

		A generator function that yields a sequence of tuples that
		allow the caller to process an entire folder with a clean loop.

		All arguments are forwarded to :meth:`~.file_object.recover`.

		The return value includes the version of the main decoded object, or None
		if the encoding and decoding applications are at the same version. This value is
		the mechanism by which applications can select different code-paths in support of
		older versions of encoded materials.

		:return: a sequence of 2-tuples, 0) key and 1) the value
		:rtype: tuple
		"""
		# Get a fresh image of folder/slice.
		matched = [f for f in self.matching()]
		# Visit each named file.
		# Yield the key, message tuple.
		for f in matched:
			io = self.file(f, tip=self.file_type)
			r = io.recover()
			if self.keys_names is None:
				k = None
			else:
				k = self.key(r)
			yield k, r

	def add(self, values: dict, item):
		"""Add a value, both to a ``dict`` of values and as a file in the folder.

		:param values: a collection of application values
		:param item: the value to be added
		:type item: :ref:`tip<layer-cake-type-reference>`
		"""
		keys_names = self.keys_names
		if keys_names is None:
			raise ValueError(f'key/name functions not set for "{self.path}" (add)')

		key = keys_names[0](item)
		name = keys_names[1](item)

		io = self.file(name, tip=self.file_type)
		if key in values:
			raise ValueError(f'name "{io.name}" already present (add)')
		io.store(item)
		values[key] = item

	def update(self, values: dict, item):
		"""Update a value, both in a ``dict`` of values and as a file in the folder.

		:param values: a collection of application values
		:param item: the value to be updated
		:type item: :ref:`tip<layer-cake-type-reference>`
		"""
		keys_names = self.keys_names
		if keys_names is None:
			raise ValueError(f'key/name functions not set for "{self.path}" (update)')

		key = keys_names[0](item)
		name = keys_names[1](item)

		io = self.file(name, tip=self.file_type)
		if key not in values:
			raise ValueError(f'name "{io.name}" not an existing entry (update)')

		io.store(item)
		values[key] = item

	def remove(self, values: dict, item):
		"""Remove a value, both from a ``dict`` of values and as a file in the folder.

		:param values: a collection of application values
		:param item: the value to be removed
		:type item: :ref:`tip<layer-cake-type-reference>`
		"""
		keys_names = self.keys_names
		if keys_names is None:
			raise ValueError(f'key/name functions not set for "{self.path}" (remove)')
		key = keys_names[0](item)
		name = keys_names[1](item)

		self.erase(name)
		del values[key]

	def clear(self, values: dict):
		"""Remove all values, both from a ``dict`` of values and as files in the folder.

		:param values: a collection of application values
		"""
		# Brute force. Delete any candidates from
		# the folder and dump everything from the dict.
		matched = [f for f in self.matching()]
		for removing in matched:
			self.erase(removing)
		values.clear()

	def erase(self, name: str):
		"""Delete the named file from the folder.

		:param name: a name of a file
		"""
		path = os.path.join(self.path, name)
		name = path
		if self.decorate_names:
			name = '%s.%s' % (path, self.encoding.EXTENSION)
		if os.path.isfile(name):
			os.remove(name)
			return True
		elif os.path.isdir(path):
			remove_folder(path)
			return True
		return False

	def exists(self, name: str=None):
		"""Detect the named file, within the folder.

		:param name: a name of a file
		:return: does the file exist
		:rtype: bool
		"""
		if name is None:
			return os.path.isdir(self.path)

		path = os.path.join(self.path, name)
		name = path
		if self.decorate_names:
			name = '%s.%s' % (path, self.encoding.EXTENSION)
		if os.path.isfile(name):
			return True
		elif os.path.isdir(path):
			return True
		return False

	def key(self, item):
		"""Generate the stable key for a given application value.

		:param item: an application value
		:type item: :ref:`tip<layer-cake-type-reference>`
		:return: the key
		:rtype: folder dependent
		"""
		keys_names = self.keys_names
		if keys_names is None:
			raise ValueError(f'key/name functions not set for "{self.path}" (key)')
		return keys_names[0](item)

	def name(self, item):
		"""Generate the stable filename for a given application value.

		:param item: an application value
		:type item: :ref:`tip<layer-cake-type-reference>`
		:return: the filename
		:rtype: str
		"""
		keys_names = self.keys_names
		if keys_names is None:
			raise ValueError(f'key/name functions not set for "{self.path}" (name)')
		return keys_names[1](item)
