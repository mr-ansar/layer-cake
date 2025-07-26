# object_spool_test.py
from unittest import TestCase

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
	'TestObjectSpool',
]

class TestObjectSpool(TestCase):
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

	def test_spool(self):
		with lc.channel() as ch:
			library = ch.create(lc.ObjectSpool, test_library.library)

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
