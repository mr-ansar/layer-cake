# send_test.py
import types
import uuid
from datetime import datetime, timedelta
from unittest import TestCase
from collections import deque

import layer_cake as lc
from layer_cake.listen_connect import *
from test_ip import *
from test_message import *

__all__ = [
	'TestGetResponse',
]

TEST_PORT = TEST_PORT_START + 100

def ack(self):
	while True:
		m = self.input()
		if isinstance(m, lc.Stop):
			return None
		elif isinstance(m, lc.Enquiry):
			self.reply(lc.Ack())
		elif isinstance(m, lc.Faulted):
			return m
		else:
			self.reply(lc.Nak())

lc.bind(ack)

class TestGetResponse(TestCase):
	def setUp(self):
		lc.PB.tear_down_atexit = False
		super().__init__()

	def tearDown(self):
		lc.PB.exit_status = None
		lc.tear_down()
		return super().tearDown()

	def test_get_response(self):
		with lc.channel() as s, lc.channel() as c:
			listen(s, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 0))
			listening, i = s.select()
			connect(c, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 0))
			# Expect Connected and Accepted.
			selected, i = c.select()
			assert isinstance(selected, Connected)
			server = c.return_address
			selected, i = s.select()
			assert isinstance(selected, Accepted)
			client = s.return_address

			c.create(lc.GetResponse, lc.Enquiry(), server)
			selected, i = s.select()
			assert isinstance(selected, lc.Enquiry)
			s.reply(lc.Ack())
			selected, i = c.select()
			assert isinstance(selected, lc.Returned)
			assert isinstance(selected.message, lc.Ack)

	def test_concurrently(self):
		with lc.channel() as s, lc.channel() as c:
			listen(s, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 0))
			listening, i = s.select()
			connect(c, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 0))
			# Expect Connected and Accepted.
			selected, i = c.select()
			assert isinstance(selected, Connected)
			server = c.return_address
			selected, i = s.select()
			assert isinstance(selected, Accepted)
			client = s.return_address

			c.create(lc.Concurrently,
				(lc.Enquiry(), server),
				(lc.Enquiry(), server),
				(lc.Enquiry(), server),
				(lc.Enquiry(), server)
			)

			selected, i = s.select()
			assert isinstance(selected, lc.Enquiry)
			s.reply(lc.Ack())
			selected, i = s.select()
			assert isinstance(selected, lc.Enquiry)
			s.reply(lc.Ack())
			selected, i = s.select()
			assert isinstance(selected, lc.Enquiry)
			s.reply(lc.Ack())
			selected, i = s.select()
			assert isinstance(selected, lc.Enquiry)
			s.reply(lc.Ack())

			selected, i = c.select()
			assert isinstance(selected, lc.Returned)
			m, p = lc.cast_back(selected.message)
			assert isinstance(m, list)
			assert isinstance(m[0], lc.Ack)

	def test_sequentially(self):
		with lc.channel() as ch:
			server = ch.create(ack)

			ch.create(lc.Sequentially,
				(lc.Enquiry(), server),
				(lc.Enquiry(), server),
				(lc.Enquiry(), server),
				(lc.Enquiry(), server)
			)

			selected, i = ch.select()
			assert isinstance(selected, lc.Returned)
			assert isinstance(selected.message, list)
			assert isinstance(selected.message[0], lc.Ack)

			ch.send(lc.Stop(), server)
			selected, i = ch.select()
			assert isinstance(selected, lc.Returned)
