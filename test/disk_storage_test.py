# disk_storage_test.py
# Verify the encode/decode operation of the folder module.
import os

from unittest import TestCase
from collections import Counter
import time
import json
import uuid

from test_message import *

import shutil, tempfile
import os
import layer_cake as lc
from layer_cake.virtual_memory import *
from layer_cake.command_line import *
from layer_cake.command_startup import *
from layer_cake.object_runtime import *
from layer_cake.object_startup import *

__all__ = [
	'TestDiskStorage',
]

class TestDiskStorage(TestCase):
	def setUp(self):
		# Test framework doesnt like atexit.
		PB.tear_down_atexit = False
		self.temp = tempfile.mkdtemp()
		super().__init__()

	def tearDown(self):
		lc.tear_down()
		shutil.rmtree(self.temp)
		super().tearDown()

	def test_storage_manifest(self):
		m, t = lc.storage_manifest('asset/mixed-content')

		assert isinstance(m, lc.StorageManifest)
		assert m.listings >= 9
		assert m.manifests >= 1
		assert isinstance(t, lc.StorageTables)
		assert len(t.group_name) >= 1
		assert len(t.user_name) >= 1

	def test_storage_selection(self):
		m, t = lc.storage_selection(['asset/mixed-content'])

		assert isinstance(m, lc.StorageManifest)
		assert m.listings >= 9
		assert m.manifests >= 1
		assert isinstance(t, lc.StorageTables)
		assert len(t.group_name) >= 1
		assert len(t.user_name) >= 1

	def test_storage_delta(self):
		source, t = lc.storage_manifest('asset/mixed-content')
		target, t = lc.storage_manifest(self.temp)

		delta = [d for d in lc.storage_delta(source, target)]
		'''
		if not storage_delta:			# Nothing to see or do.
			return None

		if not make_changes:			# Without explicit command, show what would happen.
			for d in storage_delta:
				print(d)
			return None

		a = self.create(lc.FolderTransfer, storage_delta, target_storage.path)

		m, _ = self.select(lc.Returned, lc.Stop)
		if isinstance(m, lc.Stop):
			self.send(m, a)
			m, _ = self.select(lc.Returned)
			return lc.Aborted()
		'''
		assert isinstance(delta, list)
		add_file = [d for d in delta if isinstance(d, lc.AddFile)]
		add_folder = [d for d in delta if isinstance(d, lc.AddFolder)]
		assert len(add_file) >= 4
		assert len(add_folder) >= 1

	def test_make_change(self):
		source, t = lc.storage_manifest('asset/mixed-content')
		target, t = lc.storage_manifest(self.temp)

		delta = [d for d in lc.storage_delta(source, target)]

		with lc.channel() as ch:
			a = ch.create(lc.FolderTransfer, delta, target.path)

			m, _ = ch.select(lc.Returned, lc.Stop)
			if isinstance(m, lc.Stop):
				ch.send(m, a)
				m, _ = ch.select(lc.Returned)

		assert isinstance(m, lc.Returned)
		assert isinstance(m.value, lc.Ack)

		source, t = lc.storage_manifest('asset/mixed-content')
		target, t = lc.storage_manifest(self.temp)

		delta = [d for d in lc.storage_delta(source, target)]

		assert len(delta) == 0

	def test_walk(self):
		# Not much real testing. More about getting
		# the coverage statistic down.
		source, t = lc.storage_manifest('asset/mixed-content')
		walk = [s for s in lc.storage_walk(source)]
		assert len(walk) > 10
		lc.show_listings(source)
