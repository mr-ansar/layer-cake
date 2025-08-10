# signature_test.py
from unittest import TestCase

import uuid
import datetime
import layer_cake as lc
from collections import deque
from layer_cake.convert_type import *
from layer_cake.virtual_runtime import *
from layer_cake.virtual_memory import *
from layer_cake.command_line import *
from layer_cake.command_startup import *
from layer_cake.object_runtime import *
from layer_cake.object_startup import *

from test_person import *

__all__ = [
	'TestSelectList',
]


class Basic(object):
	def __init__(self, a: bool=None, b: int=None, c: float=None, d: dict[int, dict[str, uuid.UUID]]=None, e: bytes=None, f: bytearray=None):
		self.a = a
		self.b = b
		self.c = c
		self.d = d
		self.e = e
		self.f = f

class Array(object):
	def __init__(self, a=None):
		self.a = a or [Basic()] * 8

lc.bind(Basic)
lc.bind(Array, a=lc.ArrayOf(lc.UserDefined(Basic), 8))

truth = lc.select_list(bool)
basic = lc.select_list(bool, int, float, str, bytes, bytearray, datetime.datetime, datetime.timedelta, uuid.UUID)

list_bool_type = lc.def_type(list[bool])
dict_int_float_type = lc.def_type(dict[int, float])
set_str_type = lc.def_type(set[str])
deque_bytes_type = lc.def_type(deque[bytes])

containers = lc.select_list(list[bool], dict[int, float], set[str], deque[bytes])

def echo(self):
	while True:
		m = self.input()
		self.reply(cast_to(m, self.received_type))

lc.bind(echo)

class TestSelectList(TestCase):
	def setUp(self):
		# Test framework doesnt like atexit.
		PB.tear_down_atexit = False
		lc.start_up(lc.log_to_stderr)
		super().__init__()

	def tearDown(self):
		lc.tear_down()
		return super().tearDown()

	def test_list(self):
		b = lc.cast_to(True, bool_type)
		i, m, t = truth.find(b)

		assert i == 0
		assert isinstance(m, bool)
		assert isinstance(t, lc.Boolean)

	def test_basic(self):
		def test(cast, value, is_i, is_m, is_t):
			b = cast_to(value, cast)
			i, m, t = basic.find(b)

			assert i == is_i
			assert isinstance(m, is_m)
			assert isinstance(t, is_t)

		test(bool_type, True, 0, bool, lc.Boolean)
		test(int_type, 42, 1, int, lc.Integer8)
		test(float_type, 1.0125, 2, float, lc.Float8)
		test(str_type, 'hello', 3, str, lc.Unicode)
		test(bytes_type, b'hello', 4, bytes, lc.String)
		test(bytearray_type, bytearray(b'hello'), 5, bytearray, lc.Block)
		test(datetime_type, lc.world_now(), 6, datetime.datetime, lc.WorldTime)
		test(timedelta_type, lc.text_to_delta('1:32:00'), 7, datetime.timedelta, lc.TimeDelta)
		test(uuid_type, uuid.uuid4(), 8, uuid.UUID, lc.UUID)

	def test_empty(self):
		p = install_type(dict[str,Person])
		unknown = lc.select_list_adhoc(lc.Unknown, lc.Stop)
		i, m, x = unknown.find(({}, p))
		assert i == 0
		assert isinstance(m, dict)
		assert id(x) == id(p)

	def test_echo(self):
		with lc.channel() as ch:
			e = ch.create(echo)
			ch.send(cast_to(True, Boolean()), e)
			m, i = ch.select(truth)
			assert i == 0
			assert isinstance(m, bool)
			#assert id(x) == id(p)

	def test_echo_adhoc(self):
		with lc.channel() as ch:
			e = ch.create(echo)
			ch.send(cast_to(True, Boolean()), e)
			m, i = ch.select(bool)
			assert i == 0
			assert isinstance(m, bool)
			#assert id(x) == id(p)

	def test_echo_containers(self):
		with lc.channel() as ch:
			e = ch.create(echo)
			def test(cast, value, is_i, is_m, is_t):
				ch.send(cast_to(value, cast), e)
				m, i = ch.select(containers)

				assert i == is_i
				assert isinstance(m, is_m)
				assert isinstance(ch.received_type, is_t)

			test(list_bool_type, [True, False, True], 0, list, lc.VectorOf)
			test(dict_int_float_type, {1:0.5}, 1, dict, lc.MapOf)
			test(set_str_type, set(["hello", "world"]), 2, set, lc.SetOf)
			test(deque_bytes_type, deque([b'1', b'2']), 3, deque, lc.DequeOf)
