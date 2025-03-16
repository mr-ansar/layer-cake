# object_startup_test.py
import uuid
from unittest import TestCase

import layer_cake as lc
from layer_cake.object_runtime import *
from layer_cake.listen_connect import *

__all__ = [
	'TestListenConnect',
]

class TestListenConnect(TestCase):
	def setUp(self):
		PB.tear_down_atexit = False
		super().__init__()

	def tearDown(self):
		PB.exit_status = None
		tear_down()
		return super().tearDown()

	def test_listen(self):
		with channel() as ch:
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			selected = ch.select()
		assert True
