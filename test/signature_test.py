# signature_test.py
from unittest import TestCase

import layer_cake as lc

__all__ = [
	'TestSignature',
]

class Empty(object):
	def __init__(self):
		pass

class Single(object):
	def __init__(self, a: int=None):
		self.a = a

class Basic(object):
	def __init__(self, a: bool=None, b: int=None, c: float=None, d: str=None, e: bytes=None, f: bytearray=None):
		self.a = a
		self.b = b
		self.c = c
		self.d = d
		self.e = e
		self.f = f

class Array(object):
	def __init__(self, a=None):
		self.a = a or [Basic()] * 8

lc.bind_message(Empty)
lc.bind_message(Single)
lc.bind_message(Basic)
lc.bind_message(Array, a=lc.ArrayOf(lc.UserDefined(Basic), 8))

class TestConvertHints(TestCase):
	def test_bool(self):
		schema = Basic.__art__.schema
		a = schema.get('a', None)
		s = lc.lookup_signature('boolean')

		assert id(a) == id(s)

	def test_user(self):
		schema = Array.__art__.schema
		a = schema['a'].element
		s = lc.lookup_signature('signature_test.Basic')

		assert id(a) == id(s)

	def test_by_type(self):
		schema = Array.__art__.schema
		a = schema['a']
		t = lc.lookup_type(lc.ArrayOf(lc.UserDefined(Basic), 8))
		x = lc.lookup_type(lc.ArrayOf(lc.UserDefined(Basic), 9))

		assert id(a) == id(t)
		assert id(x) != id(t)

	def test_by_sub_type(self):
		schema = Array.__art__.schema
		a = schema['a'].element
		t = lc.lookup_type(lc.UserDefined(Basic))

		assert id(a) == id(t)
