# file_test.py
# Verify the encode/decode operation of the file module.
import os

from unittest import TestCase
import time
import json
import uuid

from test_message import *

import shutil, tempfile
import os
import layer_cake as lc

from layer_cake.virtual_codec import *
from layer_cake.file_object import *

__all__ = [
	'TestFileObject',
]

class TestFileObject(TestCase):
	def setUp(self):
		self.temp = tempfile.mkdtemp()

	def tearDown(self):
		shutil.rmtree(self.temp)

	def test_write_read_cycle(self):
		a = os.path.join(self.temp, 'write-read-inferred')
		t = lc.UserDefined(AutoTypes)
		d = lc.make(t)

		write_to_file(d, a)
		r = read_from_file(t, a)

		assert isinstance(r, AutoTypes)
		assert lc.equal_to(r, d, t)

	def test_write_read_bigger(self):
		a = os.path.join(self.temp, 'write-read-explicit')
		t = lc.UserDefined(ContainerTypes)
		d = lc.make(t)

		write_to_file(d, a)

		r = read_from_file(t, a)
		assert isinstance(r, ContainerTypes)
		assert lc.equal_to(r, d, t)

	def test_not_found(self):
		a = os.path.join(self.temp, 'not_found')
		t = lc.WorldTime()

		try:
			read_from_file(t, a)
			assert False
		except FileNotFoundError as e:
			s = str(e)
			assert a in s

	def test_not_a_file(self):
		a = self.temp			# Use *folder* a.
		t = lc.WorldTime()

		try:
			read_from_file(t, a, decorate_names=False)
			assert False
		except IsADirectoryError as e:
			s = str(e)
			assert a in s

	def test_encoding(self):
		a = os.path.join(self.temp, 'cannot_encode')
		t = lc.UserDefined(ContainerTypes)

		try:
			write_to_file(AutoTypes(), a, t)
			assert False
		except CodecError as e:
			s = str(e)
			assert 'no transform bool/ArrayOf' in s

	def test_write_read_file_cycle(self):
		a = os.path.join(self.temp, 'write-read_file-inferred')
		t = lc.UserDefined(AutoTypes)
		d = lc.make(t)

		f = lc.File(a, expression=t)

		f.store(d)
		r = f.recover()
		assert isinstance(r, AutoTypes)
		assert lc.equal_to(r, d, t)

