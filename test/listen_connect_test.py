# object_startup_test.py
import uuid
from unittest import TestCase

import layer_cake as lc
from layer_cake.listen_connect import *

__all__ = [
	'TestListenConnect',
]

class TestListenConnect(TestCase):
	def setUp(self):
		lc.PB.tear_down_atexit = False
		super().__init__()

	def tearDown(self):
		lc.PB.exit_status = None
		lc.tear_down()
		return super().tearDown()

	def test_listen(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected, p = ch.select()
		assert isinstance(selected, Listening)

	def test_listen_duplicate(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected, p = ch.select()
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected, p = ch.select()
		assert isinstance(selected, NotListening)
		e = str(selected)
		assert 'already in use' in e

	def test_no_listen(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 90050))
			i, selected, p = ch.select()
		assert isinstance(selected, NotListening)

	def test_listen_and_stop(self):
		with lc.channel() as ch:
			lid = listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected, p = ch.select()
			stop_listening(ch, lid)
			i, selected, p = ch.select()
		assert isinstance(selected, NotListening)

	def test_no_stop(self):
		with lc.channel() as ch:
			lid = uuid.uuid4()
			stop_listening(ch, lid)
			i, selected, p = ch.select()
		assert isinstance(selected, NotListening)

	def test_listen_and_connect(self):
		with lc.channel() as ch:
			lid = listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(Close(), server)
			i, selected1, p = ch.select()
			i, selected2, p = ch.select()

			stop_listening(ch, lid)
			i, selected3, p = ch.select()

		assert isinstance(selected1, (Closed, Abandoned))
		assert isinstance(selected2, (Closed, Abandoned))
		assert isinstance(selected3, NotListening)

	def test_listen_and_multi_connect(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected1, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected2, p = ch.select()
			i, selected3, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected4, p = ch.select()
			i, selected5, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected6, p = ch.select()
			i, selected7, p = ch.select()
		assert isinstance(selected2, (Accepted, Connected))
		assert isinstance(selected3, (Accepted, Connected))
		assert isinstance(selected4, (Accepted, Connected))
		assert isinstance(selected5, (Accepted, Connected))
		assert isinstance(selected6, (Accepted, Connected))
		assert isinstance(selected7, (Accepted, Connected))

	def test_no_connect(self):
		with lc.channel() as ch:
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5051))
			i, selected, p = ch.select()
		assert isinstance(selected, NotConnected)
		e = str(selected)
		assert 'refused' in e

	def test_send(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected1, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, selected2, p = ch.select()
			if isinstance(selected2, Connected):
				server = ch.return_address
			i, selected3, p = ch.select()
			if isinstance(selected3, Connected):
				server = ch.return_address
			ch.send(lc.cast_to(42, lc.int_type), server)
			i, selected, p = ch.select()
			ch.send(lc.cast_to([[0.125, 30.02],[0.5, 2.5],[1.1, 2.2, 3.3]], table_type), server)
			i, selected, p = ch.select()
			ch.send(lc.Ack(), server)
			i, selected, p = ch.select()
		assert isinstance(selected, lc.Ack)

table_type = lc.def_type(list[list[float]])
