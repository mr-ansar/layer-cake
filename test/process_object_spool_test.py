# object_startup_test.py
import uuid
from unittest import TestCase
import datetime

import layer_cake as lc
from layer_cake.virtual_memory import *
from layer_cake.command_line import *
from layer_cake.command_startup import *
from layer_cake.object_runtime import *
from layer_cake.object_startup import *
import test_api
import test_main
import test_library

__all__ = [
	'TestProcessObjectSpool',
]

class TestProcessObjectSpool(TestCase):
	def setUp(self):
		# Test framework doesnt like atexit.
		PB.tear_down_atexit = False
		lc.start_up(lc.log_to_stderr)
		super().__init__()

	def tearDown(self):
		lc.tear_down()
		return super().tearDown()

	def test_channel(self):
		with lc.channel() as ch:
			assert isinstance(ch, lc.Channel)

	def test_process(self):
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main.main)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.value is None
		assert m.created_type == lc.ProcessObject

	def test_library(self):
		with lc.channel() as ch:
			library = ch.create(lc.ProcessObject, test_library.library)

			ch.send(test_api.Xy(8, 8), library)
			m, i = ch.select(test_api.table_type, lc.Faulted, lc.Stop)
			assert isinstance(m, list)
			assert len(m) == 8

			ch.send(test_api.Xy(32, 32), library)
			m, i = ch.select(test_api.table_type, lc.Faulted, lc.Stop)
			assert isinstance(m, list)
			assert len(m) == 32

			ch.send(lc.Stop(), library)
			m, i = ch.select(lc.Returned, lc.Faulted, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert isinstance(m.value, lc.Aborted)
		assert m.created_type == lc.ProcessObject

	def test_spool(self):
		with lc.channel() as ch:
			library = ch.create(lc.ProcessObjectSpool, test_library.library)

			ch.send(test_api.Xy(8, 8), library)
			m, i = ch.select(test_api.table_type, lc.Faulted, lc.Stop)
			assert isinstance(m, list)
			assert len(m) == 8

			ch.send(test_api.Xy(32, 32), library)
			m, i = ch.select(test_api.table_type, lc.Faulted, lc.Stop)
			assert isinstance(m, list)
			assert len(m) == 32

			ch.send(lc.Stop(), library)
			m, i = ch.select(lc.Returned, lc.Faulted, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert isinstance(m.value, lc.Aborted)
		assert m.created_type == lc.ProcessObjectSpool

	def test_flood(self):
		with lc.channel() as ch:
			library = ch.create(lc.ProcessObjectSpool, test_library.library, process_count=2)

			for i in range(1024):
				ch.send(test_api.Xy(2, 2), library)

			for i in range(1024):
				m, i = ch.select(test_api.table_type, lc.Faulted, lc.Stop)
				if isinstance(m, lc.T1):
					break

			assert isinstance(m, (list, lc.Overloaded))

			ch.send(lc.Stop(), library)
			m, i = ch.select(lc.Returned, lc.Faulted, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert isinstance(m.value, lc.Aborted)
		assert m.created_type == lc.ProcessObjectSpool
