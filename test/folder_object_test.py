# folder_test.py
# Verify the encode/decode operation of the folder module.
import os

from unittest import TestCase
import time
import json
import uuid

from test_message import *

import shutil, tempfile
import os
import layer_cake as lc

__all__ = [
	'TestFolderObject',
]

class TestFolderObject(TestCase):
	def setUp(self):
		self.temp = tempfile.mkdtemp()

	def tearDown(self):
		shutil.rmtree(self.temp)

	def test_existing_folder_file_cycle(self):
		t = lc.UserDefined(AutoTypes)
		d = lc.make(t)

		# 1. Declare the location
		# 2. Declare a file at that location.
		# 3. Write and then read the object in that file
		# 4. Compare r to d.
		F = lc.Folder(self.temp)
		f = F.file('write-read-inferred', tip=t)

		f.store(d)
		r = f.recover()

		assert isinstance(r, AutoTypes)
		assert lc.equal_to(r, d, t)

	def test_new_folder_file_cycle(self):
		name = os.path.join(self.temp, 'write-read-inferred')
		t = lc.UserDefined(AutoTypes)
		d = lc.make(t)

		# 1. Declare the location
		# 2. Declare a file at that location.
		# 3. Write and then read the object in that file
		# 4. Compare r to d.
		F = lc.Folder(name)
		f = F.file('inferred-t', tip=t)

		f.store(d)
		r = f.recover()

		assert isinstance(r, AutoTypes)
		assert lc.equal_to(r, d, t)

	def test_map_cycle(self):
		t = lc.UserDefined(AutoTypes)

		kn = (lambda m: m.b, lambda m: '%04d' % (m.b))

		# Give test its own folder.
		name = os.path.join(self.temp, 'store-recover-cycle')
		f = lc.Folder(name, tip=t, keys_names=kn)
		a = lc.Folder(name, tip=t, keys_names=kn)

		# Generate a suitable map.
		d = {}
		for i in range(20):
			e = lc.make(t)
			e.b = i
			d[i] = e

		f.store(d)
		a.store(d)
		r = {k: m for k, m in f.recover()}

		assert isinstance(r, dict)

		o5 = d[5]
		r5 = r[5]

		assert isinstance(o5, AutoTypes)
		assert isinstance(r5, AutoTypes)
		assert lc.equal_to(o5, r5, t)

	def test_add_remove(self):
		# Add and remove items from a folder store.
		# Write as older version and process the version
		# when reading.
		t = lc.UserDefined(AutoTypes)

		kn = (lambda m: m.b, lambda m: '%04d' % (m.b))

		# Give test its own folder.
		name = os.path.join(self.temp, 'add-remove')
		f = lc.Folder(name, tip=t, keys_names=kn)

		# Generate a suitable map.
		d = {}
		for i in range(256):
			e = lc.make(t)
			e.b = i
			d[i] = e

		f.store(d)

		r = {}
		for k, m in f.recover():
			r[k] = m

		assert isinstance(r, dict)

		a = lc.make(t)
		a.b = 392

		f.add(r, a)
		f.remove(r, r[210])

		lastly = {k: m for k, m in f.recover()}

		assert len(d) == 256
		assert len(r) == 256
		assert len(lastly) == 256
		assert 210 in d
		assert 392 not in d
		assert 210 not in r
		assert 392 in r
		assert 210 not in lastly
		assert 392 in lastly

	def test_store_clear(self):
		t = lc.UserDefined(AutoTypes)

		kn = (lambda m: m.b, lambda m: '%04d' % (m.b))

		# Give test its own folder.
		name = os.path.join(self.temp, 'store-clear')
		f = lc.Folder(name, tip=t, keys_names=kn)

		# Generate a suitable map.
		d = {}
		for i in range(256):
			e = lc.make(t)
			e.b = i
			d[i] = e

		f.store(d)
		r = {k: m for k, m in f.recover()}
		assert len(d) == 256
		assert len(r) == 256

		f.clear(r)
		assert len(r) == 0

		lastly = {k: m for k, m in f.recover()}
		assert len(lastly) == 0

	def test_trees(self):
		t = lc.UserDefined(AutoTypes)
		kn = (lambda m: m.b, lambda m: '%04d' % (m.b,))
		name = os.path.join(self.temp, 'trees')

		f = lc.Folder(name, tip=t, keys_names=kn)

		# Create a small tree, remembering the
		# folder at the deepest location.
		f.folder('a')
		f.folder('b').folder('x')
		cy = f.folder('c').folder('y')
		f.folder('d').folder('z')
		f.folder('e')

		assert f.exists('a')
		assert f.exists(cy.path)

		f.erase('c')
		assert not f.exists('c')

	def test_tree_of_files(self):
		t = lc.UserDefined(AutoTypes)
		d = lc.make(t)
		kn = (lambda m: m.b, lambda m: '%04d' % (m.b,))
		name = os.path.join(self.temp, 'tree-of-files')

		f = lc.Folder(name, tip=t, keys_names=kn)

		X = f.folder('X')
		X.folder('a')
		X.folder('b')
		cy = X.folder('c').folder('y')
		cyz = X.folder('c').folder('y').folder('z')
		e = X.folder('e')
		X.folder('d')

		assert X.exists('a')
		assert X.exists(cy.path)

		cyf = cy.file('f', tip=t)
		cyf.store(d)

		assert cy.exists('f')
		p = os.path.join('c','y','f')
		assert X.exists(p)

		# Generate a suitable map.
		table = {}
		for i in range(256):
			r = lc.make(t)
			r.b = i
			table[i] = r

		cyz.store(table)
		names = [m for m in cyz.matching()]
		count = len(names)
		assert cyz.exists('0000')
		assert cyz.exists('0255')
		assert count == 256

		cy.erase('z')
		assert not cy.exists('z')

		e.store(table)
		assert e.exists('0000')
		assert e.exists('0255')

		table_0 = table[0]
		e.remove(table, table_0)
		assert not e.exists('0000')
		assert 0 not in table

		e.add(table, table_0)
		assert e.exists('0000')
		assert 0 in table

		f.erase('X')
		assert not f.exists('X')
		# All sub-folder objects now invalid as underlying
		# locations are gone.

		s = ''
		try:
			cyf.recover()
		except FileNotFoundError as e:
			s = str(e)
			assert 'No such file' in s
