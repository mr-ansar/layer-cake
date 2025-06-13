# send_test.py
import types
import uuid
import time
from datetime import datetime, timedelta
from unittest import TestCase
from collections import deque

import layer_cake as lc
from layer_cake.listen_connect import *
from test_message import *
from test_ip import *
from test_api import *


__all__ = [
	'TestSendHttp',
]

TEST_PORT = TEST_PORT_START + 50
TEST_API = (
	Xy,
	lc.Enquiry,
	PlainTypes,
	ContainerTypes,
	TimeTypes,
)

def api(self, json=False, port=TEST_PORT):
	listen(self, requested_ipp=lc.HostPort('127.0.0.1', port), api_server=TEST_API, ansar_client=json)

	while True:
		m = self.input()
		if isinstance(m, lc.Stop):
			return None
		elif isinstance(m, (lc.Listening, lc.Accepted, lc.Closed, lc.NotListening)):
			continue
		elif isinstance(m, TEST_API):
			self.reply(m)
		elif isinstance(m, lc.Faulted):
			return m
		else:
			self.reply(lc.Nak())

lc.bind(api)


class TestSendHttp(TestCase):
	def setUp(self):
		lc.PB.tear_down_atexit = False
		super().__init__()

	def tearDown(self):
		lc.PB.exit_status = None
		lc.tear_down()
		return super().tearDown()

	def test_send_Xy(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 0), api_server=TEST_API)
			listening, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 0), api_client='/')
			# Expect Connected and Accepted.
			selected, i = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			selected, i = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(Xy(), server)
			m = ch.input()
		assert isinstance(m, Xy)

	def test_send_Xy_reply(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 1), api_server=TEST_API)
			listening, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 1), api_client='/')
			# Expect Connected and Accepted.
			selected, i = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			selected, i = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(Xy(), server)
			selected = ch.input()
			table = [[1.0, 2.0],[3.0, 4.0]]
			c = lc.cast_to(table, lc.VectorOf(lc.VectorOf(lc.Float8())))
			ch.reply(c)
			selected = ch.input()
		assert isinstance(selected, lc.HttpResponse)

	def test_Enquiry_Ack(self):
		with lc.channel() as ch:
			server = ch.create(api, port=TEST_PORT + 2)
			time.sleep(1.0)
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 2), api_client='/')

			selected, i = ch.select()
			assert isinstance(selected, Connected)
			server = ch.return_address

			def send_check(value, check, original=None):
				ch.send(value, server)
				selected, i = ch.select()
				assert isinstance(selected, lc.HttpResponse)
				assert selected.status_code == 200
				#if original is not None:
				#	assert selected == original
		
			send_check(lc.Enquiry(), lc.Enquiry, True)
			send_check(PlainTypes(), PlainTypes, True)
			send_check(ContainerTypes(), ContainerTypes, True)
			send_check(TimeTypes(), TimeTypes, True)

			ch.send(lc.Stop(), server)
			selected, i = ch.select()
			assert isinstance(selected, (lc.Closed, lc.Returned))

	def test_json(self):
		with lc.channel() as ch:
			server = ch.create(api, json=True, port=TEST_PORT + 3)
			time.sleep(1.0)
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', TEST_PORT + 3), api_client='/', ansar_server=True)

			selected, i = ch.select()
			assert isinstance(selected, Connected)
			server = ch.return_address

			def send_check(value, check, original=None):
				ch.send(value, server)
				selected, i = ch.select()
				assert isinstance(selected, check)
				#assert selected.status_code == 200
				#if original is not None:
				#	assert selected == original
		
			send_check(lc.Enquiry(), lc.Enquiry, True)
			send_check(PlainTypes(), PlainTypes, True)
			send_check(ContainerTypes(), ContainerTypes, True)
			send_check(TimeTypes(), TimeTypes, True)

			ch.send(lc.Stop(), server)
			selected, i = ch.select()
			assert isinstance(selected, (lc.Closed, lc.Returned))
