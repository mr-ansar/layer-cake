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
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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
			
			send_check(lc.bool_cast(True), bool, True)
			send_check(lc.bool_cast(False), bool, False)
			send_check(lc.int_cast(0), int, 0)
			send_check(lc.int_cast(-1), int, -1)
			send_check(lc.int_cast(1), int, 1)
			send_check(lc.int_cast(42), int, 42)
			send_check(lc.int_cast(42007), int, 42007)
			send_check(lc.int_cast(None), types.NoneType)

			send_check(lc.float_cast(0.0), float, 0.0)
			send_check(lc.float_cast(-1.0), float, -1.0)
			send_check(lc.float_cast(1.0), float, 1.0)
			send_check(lc.float_cast(42.0), float, 42.0)
			send_check(lc.float_cast(42007.0), float, 42007.0)
			send_check(lc.float_cast(0.1), float, 0.1)
			send_check(lc.float_cast(0.01), float, 0.01)
			send_check(lc.float_cast(0.0001), float, 0.0001)
			send_check(lc.float_cast(-0.1), float, -0.1)
			send_check(lc.float_cast(-0.01), float, -0.01)
			send_check(lc.float_cast(-0.0001), float, -0.0001)
			send_check(lc.float_cast(None), types.NoneType)

			send_check(lc.str_cast('hello world'), str, 'hello world')
			send_check(lc.str_cast(''), str, '')
			send_check(lc.str_cast('\t\r\n\f'), str, '\t\r\n\f')
			send_check(lc.str_cast('\00'), str, '\0')
			send_check(lc.str_cast('Fichier non trouvé'), str, 'Fichier non trouvé')
			send_check(lc.str_cast('Gürzenichstraße'), str, 'Gürzenichstraße')
			send_check(lc.str_cast(None), types.NoneType)

			send_check(lc.bytes_cast(b'hello world'), bytes, b'hello world')
			send_check(lc.bytes_cast(b''), bytes, b'')
			send_check(lc.bytes_cast(b'\t\r\n\f'), bytes, b'\t\r\n\f')
			send_check(lc.bytes_cast(b'\00'), bytes, b'\0')
			send_check(lc.bytes_cast(b'Fichier non trouvee'), bytes, b'Fichier non trouvee')
			send_check(lc.bytes_cast(b'GuurzenichstraBe'), bytes, b'GuurzenichstraBe')
			send_check(lc.bytes_cast(None), types.NoneType)

			hello_world = bytearray(b'hello world')
			empty = bytearray(b'')
			slashed = bytearray(b'\t\r\n\f')
			bin = bytearray(b'\x00\x01\xf0\xf1\xfe\xff')
			vee = bytearray(b'Fichier non trouvee')
			abe = bytearray(b'GuurzenichstraBe')

			send_check(lc.bytearray_cast(hello_world), bytearray, hello_world)
			send_check(lc.bytearray_cast(empty), bytearray, empty)
			send_check(lc.bytearray_cast(slashed), bytearray, slashed)
			send_check(lc.bytearray_cast(bin), bytearray, bin)
			send_check(lc.bytearray_cast(vee), bytearray, vee)
			send_check(lc.bytearray_cast(abe), bytearray, abe)
			send_check(lc.bytearray_cast(None), types.NoneType)

	def test_send_cast_extra(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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

			send_check(lc.datetime_cast(birthday), datetime, birthday)
			send_check(lc.datetime_cast(now), datetime, now)
			send_check(lc.datetime_cast(mia), datetime, mia)
			send_check(lc.datetime_cast(revolution), datetime, revolution)

			days = lc.text_to_delta('1:0:0:0')
			hours = lc.text_to_delta('1:0:0')
			minutes = lc.text_to_delta('0:1:0')
			seconds = lc.text_to_delta('0:0:1')
			tenth = lc.text_to_delta('0:0:0.1')
			hundredth = lc.text_to_delta('0:0:0.01')
			fraction = lc.text_to_delta('0:0:0.700252')

			send_check(lc.timedelta_cast(days), timedelta, days)
			send_check(lc.timedelta_cast(hours), timedelta, hours)
			send_check(lc.timedelta_cast(minutes), timedelta, minutes)
			send_check(lc.timedelta_cast(seconds), timedelta, seconds)
			send_check(lc.timedelta_cast(tenth), timedelta, tenth)
			send_check(lc.timedelta_cast(hundredth), timedelta, hundredth)
			send_check(lc.timedelta_cast(fraction), timedelta, fraction)

			days = lc.text_to_delta('-1:0:0:0')
			hours = lc.text_to_delta('-1:0:0')
			minutes = lc.text_to_delta('-0:1:0')
			seconds = lc.text_to_delta('-0:0:1')
			tenth = lc.text_to_delta('-0:0:0.1')
			hundredth = lc.text_to_delta('-0:0:0.01')
			fraction = lc.text_to_delta('-0:0:0.700252')

			send_check(lc.timedelta_cast(days), timedelta, days)
			send_check(lc.timedelta_cast(hours), timedelta, hours)
			send_check(lc.timedelta_cast(minutes), timedelta, minutes)
			send_check(lc.timedelta_cast(seconds), timedelta, seconds)
			send_check(lc.timedelta_cast(tenth), timedelta, tenth)
			send_check(lc.timedelta_cast(hundredth), timedelta, hundredth)
			send_check(lc.timedelta_cast(fraction), timedelta, fraction)

			magic = uuid.uuid4()

			send_check(lc.uuid_cast(magic), uuid.UUID, magic)

	def test_send_container(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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

			send_check(vector_cast(v3ct0r), list, v3ct0r)
			send_check(array_cast(arr4y), list, arr4y)
			send_check(deque_cast(d3qu3), deque, d3qu3)
			send_check(set_cast(s3t), set, s3t)
			send_check(dict_cast(d1ct), dict, d1ct)

	def test_send_message(self):
		with lc.channel() as ch:
			listen(ch, requested_ipp=HostPort('127.0.0.1', 5050))
			i, listening, p = ch.select()
			connect(ch, requested_ipp=HostPort('127.0.0.1', 5050))
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
			send_check(stx, SpecialTypes)
			send_check(ttx, TimeTypes, ttx)

			send_check(pointer_cast(accept), State, accept)
			send_check(pointer_cast(line_3), State, line_3)
			send_check(pointer_cast(line_2), State, line_2)
			send_check(pointer_cast(line_1), State, line_1)
			send_check(pointer_cast(line_0), State, line_0)

			send_check(pointer_cast(tree_3), State, tree_3)
			send_check(pointer_cast(tree_2), State, tree_2)
			send_check(pointer_cast(tree_1), State, tree_1)
			send_check(pointer_cast(tree_0), State, tree_0)

			send_check(pointer_cast(graph_3), State, graph_3)
			send_check(pointer_cast(graph_2), State, graph_2)
			send_check(pointer_cast(graph_1), State, graph_1)
			send_check(pointer_cast(graph_0), State, graph_0)

			send_check(Ptx, PointerTypes, Ptx)

			send_check(pointer_cast(quick_0), State, quick_0)

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
pointer_cast = lc.type_cast(lc.PointerTo(lc.UserDefined(State)))

vector_cast = lc.type_cast(list[bool])
array_cast = lc.type_cast(lc.ArrayOf(int,4))
deque_cast = lc.type_cast(deque[float])
set_cast = lc.type_cast(set[str])
dict_cast = lc.type_cast(dict[uuid.UUID,float])
