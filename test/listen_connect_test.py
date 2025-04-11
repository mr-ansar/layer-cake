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
			selected, i = ch.select()
		assert isinstance(selected, Listening)

	def test_listen_duplicate(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected, i = ch.select()
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected, i = ch.select()
		assert isinstance(selected, NotListening)
		e = str(selected)
		assert 'already in use' in e

	def test_no_listen(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 90050))
			selected, i = ch.select()
		assert isinstance(selected, NotListening)

	def test_listen_and_stop(self):
		with lc.channel() as ch:
			lid = listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected, i = ch.select()
			stop_listening(ch, lid)
			selected, i = ch.select()
		assert isinstance(selected, NotListening)

	def test_no_stop(self):
		with lc.channel() as ch:
			lid = uuid.uuid4()
			stop_listening(ch, lid)
			selected, i = ch.select()
		assert isinstance(selected, NotListening)

	def test_listen_and_connect(self):
		with lc.channel() as ch:
			lid = listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			listening, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			selected, i = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			selected, i = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(Close(), server)
			selected1, i = ch.select()
			selected2, i = ch.select()

			stop_listening(ch, lid)
			selected3, i = ch.select()

		assert isinstance(selected1, Closed)
		assert isinstance(selected2, Closed)
		assert isinstance(selected3, NotListening)

	def test_listen_and_multi_connect(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected1, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected2, i = ch.select()
			selected3, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected4, i = ch.select()
			selected5, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected6, i = ch.select()
			selected7, i = ch.select()
		assert isinstance(selected2, (Accepted, Connected))
		assert isinstance(selected3, (Accepted, Connected))
		assert isinstance(selected4, (Accepted, Connected))
		assert isinstance(selected5, (Accepted, Connected))
		assert isinstance(selected6, (Accepted, Connected))
		assert isinstance(selected7, (Accepted, Connected))

	def test_no_connect(self):
		with lc.channel() as ch:
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5051))
			selected, i = ch.select()
		assert isinstance(selected, NotConnected)
		e = str(selected)
		assert 'refused' in e

	def test_send(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected1, i = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			selected2, i = ch.select()
			if isinstance(selected2, Connected):
				server = ch.return_address
			selected3, i = ch.select()
			if isinstance(selected3, Connected):
				server = ch.return_address
			ch.send(lc.cast_to(42, lc.int_type), server)
			selected, i = ch.select()
			ch.send(lc.cast_to([[0.125, 30.02],[0.5, 2.5],[1.1, 2.2, 3.3]], table_type), server)
			selected, i = ch.select()
			ch.send(lc.Ack(), server)
			selected, i = ch.select()
		assert isinstance(selected, lc.Ack)

table_type = lc.def_type(list[list[float]])
