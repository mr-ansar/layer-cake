# send_test.py
import types
import uuid
from datetime import datetime, timedelta
from unittest import TestCase
from collections import deque

import layer_cake as lc
from layer_cake.listen_connect import *

from test_message import *

__all__ = [
	'TestSend',
]

class TestSend(TestCase):
	def setUp(self):
		lc.PB.tear_down_atexit = False
		super().__init__()

	def tearDown(self):
		lc.PB.exit_status = None
		lc.tear_down()
		return super().tearDown()

	def test_send_ack(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(lc.Ack(), server)
			i, selected, p = ch.select()
		assert isinstance(selected, lc.Ack)

	def test_send_ack_reply(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(lc.Ack(), server)
			i, selected, p = ch.select()
			ch.reply(selected)
			i, selected, p = ch.select()
		assert isinstance(selected, lc.Ack)

	def test_send_ack_forward(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			ch.send(lc.Ack(), server)
			i, selected, p = ch.select()
			ch.forward(selected, ch.return_address, ch.object_address)
			i, selected, p = ch.select()
		assert isinstance(selected, lc.Ack)

	def test_send_cast(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			def send_check(value, check, original=None):
				ch.send(value, server)
				i, selected, p = ch.select()
				assert isinstance(selected, check)
				if original is not None:
					assert selected == original
			
			send_check(lc.cast_to(True, lc.bool_type), bool, True)
			send_check(lc.cast_to(False, lc.bool_type), bool, False)
			send_check(lc.cast_to(0, lc.int_type), int, 0)
			send_check(lc.cast_to(-1, lc.int_type), int, -1)
			send_check(lc.cast_to(1, lc.int_type), int, 1)
			send_check(lc.cast_to(42, lc.int_type), int, 42)
			send_check(lc.cast_to(42007, lc.int_type), int, 42007)
			send_check(lc.cast_to(None, lc.int_type), types.NoneType)

			send_check(lc.cast_to(0.0, lc.float_type), float, 0.0)
			send_check(lc.cast_to(-1.0, lc.float_type), float, -1.0)
			send_check(lc.cast_to(1.0, lc.float_type), float, 1.0)
			send_check(lc.cast_to(42.0, lc.float_type), float, 42.0)
			send_check(lc.cast_to(42007.0, lc.float_type), float, 42007.0)
			send_check(lc.cast_to(0.1, lc.float_type), float, 0.1)
			send_check(lc.cast_to(0.01, lc.float_type), float, 0.01)
			send_check(lc.cast_to(0.0001, lc.float_type), float, 0.0001)
			send_check(lc.cast_to(-0.1, lc.float_type), float, -0.1)
			send_check(lc.cast_to(-0.01, lc.float_type), float, -0.01)
			send_check(lc.cast_to(-0.0001, lc.float_type), float, -0.0001)
			send_check(lc.cast_to(None, lc.float_type), types.NoneType)

			send_check(lc.cast_to('hello world', lc.str_type), str, 'hello world')
			send_check(lc.cast_to('', lc.str_type), str, '')
			send_check(lc.cast_to('\t\r\n\f', lc.str_type), str, '\t\r\n\f')
			send_check(lc.cast_to('\00', lc.str_type), str, '\0')
			send_check(lc.cast_to('Fichier non trouvé', lc.str_type), str, 'Fichier non trouvé')
			send_check(lc.cast_to('Gürzenichstraße', lc.str_type), str, 'Gürzenichstraße')
			send_check(lc.cast_to(None, lc.str_type), types.NoneType)

			send_check(lc.cast_to(b'hello world', lc.bytes_type), bytes, b'hello world')
			send_check(lc.cast_to(b'', lc.bytes_type), bytes, b'')
			send_check(lc.cast_to(b'\t\r\n\f', lc.bytes_type), bytes, b'\t\r\n\f')
			send_check(lc.cast_to(b'\00', lc.bytes_type), bytes, b'\0')
			send_check(lc.cast_to(b'Fichier non trouvee', lc.bytes_type), bytes, b'Fichier non trouvee')
			send_check(lc.cast_to(b'GuurzenichstraBe', lc.bytes_type), bytes, b'GuurzenichstraBe')
			send_check(lc.cast_to(None, lc.bytes_type), types.NoneType)

			hello_world = bytearray(b'hello world')
			empty = bytearray(b'')
			slashed = bytearray(b'\t\r\n\f')
			bin = bytearray(b'\x00\x01\xf0\xf1\xfe\xff')
			vee = bytearray(b'Fichier non trouvee')
			abe = bytearray(b'GuurzenichstraBe')

			send_check(lc.cast_to(hello_world, lc.bytearray_type), bytearray, hello_world)
			send_check(lc.cast_to(empty, lc.bytearray_type), bytearray, empty)
			send_check(lc.cast_to(slashed, lc.bytearray_type), bytearray, slashed)
			send_check(lc.cast_to(bin, lc.bytearray_type), bytearray, bin)
			send_check(lc.cast_to(vee, lc.bytearray_type), bytearray, vee)
			send_check(lc.cast_to(abe, lc.bytearray_type), bytearray, abe)
			send_check(lc.cast_to(None, lc.bytearray_type), types.NoneType)

	def test_send_cast_extra(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			def send_check(value, check, original=None):
				ch.send(value, server)
				i, selected, p = ch.select()
				assert isinstance(selected, check)
				if original is not None:
					assert selected == original

			birthday = lc.text_to_world('1963-03-26T02:24')
			now = lc.world_now()
			mia = lc.text_to_world('2007-09-18T14:24:16')
			revolution = lc.text_to_world('1789-01-01')

			send_check(lc.cast_to(birthday, lc.datetime_type), datetime, birthday)
			send_check(lc.cast_to(now, lc.datetime_type), datetime, now)
			send_check(lc.cast_to(mia, lc.datetime_type), datetime, mia)
			send_check(lc.cast_to(revolution, lc.datetime_type), datetime, revolution)

			days = lc.text_to_delta('1:0:0:0')
			hours = lc.text_to_delta('1:0:0')
			minutes = lc.text_to_delta('0:1:0')
			seconds = lc.text_to_delta('0:0:1')
			tenth = lc.text_to_delta('0:0:0.1')
			hundredth = lc.text_to_delta('0:0:0.01')
			fraction = lc.text_to_delta('0:0:0.700252')

			send_check(lc.cast_to(days, lc.timedelta_type), timedelta, days)
			send_check(lc.cast_to(hours, lc.timedelta_type), timedelta, hours)
			send_check(lc.cast_to(minutes, lc.timedelta_type), timedelta, minutes)
			send_check(lc.cast_to(seconds, lc.timedelta_type), timedelta, seconds)
			send_check(lc.cast_to(tenth, lc.timedelta_type), timedelta, tenth)
			send_check(lc.cast_to(hundredth, lc.timedelta_type), timedelta, hundredth)
			send_check(lc.cast_to(fraction, lc.timedelta_type), timedelta, fraction)

			days = lc.text_to_delta('-1:0:0:0')
			hours = lc.text_to_delta('-1:0:0')
			minutes = lc.text_to_delta('-0:1:0')
			seconds = lc.text_to_delta('-0:0:1')
			tenth = lc.text_to_delta('-0:0:0.1')
			hundredth = lc.text_to_delta('-0:0:0.01')
			fraction = lc.text_to_delta('-0:0:0.700252')

			send_check(lc.cast_to(days, lc.timedelta_type), timedelta, days)
			send_check(lc.cast_to(hours, lc.timedelta_type), timedelta, hours)
			send_check(lc.cast_to(minutes, lc.timedelta_type), timedelta, minutes)
			send_check(lc.cast_to(seconds, lc.timedelta_type), timedelta, seconds)
			send_check(lc.cast_to(tenth, lc.timedelta_type), timedelta, tenth)
			send_check(lc.cast_to(hundredth, lc.timedelta_type), timedelta, hundredth)
			send_check(lc.cast_to(fraction, lc.timedelta_type), timedelta, fraction)

			magic = uuid.uuid4()

			send_check(lc.cast_to(magic, lc.uuid_type), uuid.UUID, magic)

	def test_send_container(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			def send_check(value, check, original=None):
				ch.send(value, server)
				i, selected, p = ch.select()
				assert isinstance(selected, check)
				if original is not None:
					assert selected == original

			v3ct0r = [True, True, False, True]
			arr4y = [1, 2, 3, 4]
			d3qu3 = deque([0.124, 2.48, 24.89])
			s3t = set(['sue', 'tez', 'mia', 'scott', 'bee'])
			d1ct = {uuid.uuid4(): 0.1, uuid.uuid4(): 0.2, uuid.uuid4(): 0.3, uuid.uuid4(): 0.4, uuid.uuid4(): 0.5}

			send_check(lc.cast_to(v3ct0r, vector_type), list, v3ct0r)
			send_check(lc.cast_to(arr4y, array_type), list, arr4y)
			send_check(lc.cast_to(d3qu3, deque_type), deque, d3qu3)
			send_check(lc.cast_to(s3t, set_type), set, s3t)
			send_check(lc.cast_to(d1ct, dict_type), dict, d1ct)

	def test_send_message(self):
		with lc.channel() as ch:
			listen(ch, lc.HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, lc.HostPort('127.0.0.1', 5050))
			# Expect Connected and Accepted.
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address
			i, selected, p = ch.select()
			if isinstance(selected, Connected):
				server = ch.return_address

			def send_check(value, check, original=None):
				ch.send(value, server)
				i, selected, p = ch.select()
				assert isinstance(selected, check)
				if original is not None:
					assert lc.equal_to(selected, original)

			atx = AutoTypes()
			ptx = PlainTypes()
			ctx = ContainerTypes()
			stx = SpecialTypes()
			ttx = TimeTypes()
			Ptx = PointerTypes()

			send_check(atx, AutoTypes, atx)
			send_check(ptx, PlainTypes, ptx)
			send_check(ctx, ContainerTypes, ctx)
			send_check(stx, SpecialTypes)			# Equality check fails on changing addresses.
			send_check(ttx, TimeTypes, ttx)

			send_check(lc.cast_to(accept, pointer_type), State, accept)
			send_check(lc.cast_to(line_3, pointer_type), State, line_3)
			send_check(lc.cast_to(line_2, pointer_type), State, line_2)
			send_check(lc.cast_to(line_1, pointer_type), State, line_1)
			send_check(lc.cast_to(line_0, pointer_type), State, line_0)

			send_check(lc.cast_to(tree_3, pointer_type), State, tree_3)
			send_check(lc.cast_to(tree_2, pointer_type), State, tree_2)
			send_check(lc.cast_to(tree_1, pointer_type), State, tree_1)
			send_check(lc.cast_to(tree_0, pointer_type), State, tree_0)

			send_check(lc.cast_to(graph_3, pointer_type), State, graph_3)
			send_check(lc.cast_to(graph_2, pointer_type), State, graph_2)
			send_check(lc.cast_to(graph_1, pointer_type), State, graph_1)
			send_check(lc.cast_to(graph_0, pointer_type), State, graph_0)

			send_check(Ptx, PointerTypes, Ptx)

			send_check(lc.cast_to(quick_0, pointer_type), State, quick_0)

# End of chain.
accept = State()

# Single linked list, 0-1-2-3-accept.
line_3 = State(edge={None: accept})
line_2 = State(edge={'3': line_3})
line_1 = State(edge={'2': line_2})
line_0 = State(edge={'1': line_1})

# Tree, 0-1-2-3-accept.
tree_3 = State(edge={None: accept})
tree_2 = State(edge={'3': tree_3})
tree_1 = State(edge={'2': tree_2})
tree_0 = State(edge={'1': tree_1})

# Plus 3 links from 0-1-2 to unique ends.
tree_0.edge['1'].edge['2'].edge['4'] = State()
tree_0.edge['1'].edge['2'].edge['5'] = State()
tree_0.edge['1'].edge['2'].edge['6'] = State()

# And 3 links from 0-1 to unique ends.
tree_0.edge['1'].edge['7'] = State()
tree_0.edge['1'].edge['8'] = State()
tree_0.edge['1'].edge['9'] = State()

# A graph that starts with a straight linked
# list but adds edge from all nodes to a common
# end
graph_3 = State(edge={None: accept})
graph_2 = State(edge={None: accept, '3': graph_3})
graph_1 = State(edge={None: accept, '2': graph_2})
graph_0 = State(edge={None: accept, '1': graph_1})

# Links from 0-1-2 that jump forward and back.
graph_0.edge['1'].edge['2'].edge['3'] = graph_2
graph_0.edge['1'].edge['2'].edge['4'] = graph_0
graph_0.edge['1'].edge['2'].edge['5'] = graph_1

# Add to complexity.
graph_0.edge['1'].edge['6'] = graph_3
graph_0.edge['1'].edge['7'] = accept
graph_0.edge['1'].edge['8'] = graph_0

#
quick_3 = State(edge={None: accept})
quick_2 = State(edge={None: accept, '3': graph_3})
quick_1 = State(edge={None: accept, '2': quick_2})
quick_0 = State(edge={None: accept, '1': quick_1})

quick_0.edge['1'].edge['4'] = quick_0
quick_0.edge['1'].edge['6'] = quick_3
quick_0.edge['5'] = quick_2

#
pointer_type = lc.def_type(lc.PointerTo(lc.UserDefined(State)))

vector_type = lc.def_type(list[bool])
array_type = lc.def_type(lc.ArrayOf(int,4))
deque_type = lc.def_type(deque[float])
set_type = lc.def_type(set[str])
dict_type = lc.def_type(dict[uuid.UUID,float])
