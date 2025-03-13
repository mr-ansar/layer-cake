# signature_test.py
from unittest import TestCase

import uuid
import datetime
import layer_cake as lc
from collections import deque
from layer_cake.convert_type import *
from layer_cake.virtual_runtime import *
from layer_cake.virtual_runtime import *

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
containers = lc.select_list(list[bool], dict[int, float], set[str], deque[bytes])

class TestServiceList(TestCase):
	def test_list(self):
		b = lc.bool_cast(True)
		i, m, t = truth.find(b)

		assert i == 0
		assert isinstance(m, bool)
		assert isinstance(t, lc.Boolean)

	def test_basic(self):
		def test(cast, value, is_i, is_m, is_t):
			b = cast(value)
			i, m, t = basic.find(b)

			assert i == is_i
			assert isinstance(m, is_m)
			assert isinstance(t, is_t)

		test(bool_cast, True, 0, bool, lc.Boolean)
		test(int_cast, 42, 1, int, lc.Integer8)
		test(float_cast, 1.0125, 2, float, lc.Float8)
		test(str_cast, 'hello', 3, str, lc.Unicode)
		test(bytes_cast, b'hello', 4, bytes, lc.String)
		test(bytearray_cast, bytearray(b'hello'), 5, bytearray, lc.Block)
		test(datetime_cast, lc.world_now(), 6, datetime.datetime, lc.WorldTime)
		test(timedelta_cast, lc.text_to_delta('1:32:00'), 7, datetime.timedelta, lc.TimeDelta)
		test(uuid_cast, uuid.uuid4(), 8, uuid.UUID, lc.UUID)
