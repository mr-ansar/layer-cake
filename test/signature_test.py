# signature_test.py
from unittest import TestCase

import uuid
import layer_cake as lc
from layer_cake.convert_type import *
from layer_cake.virtual_runtime import *
from layer_cake.virtual_runtime import *

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

lc.bind_message(Empty)
lc.bind_message(Single)
lc.bind_message(Basic)
lc.bind_message(Array, a=lc.ArrayOf(lc.UserDefined(Basic), 8))

class TestSignature(TestCase):
	def test_bool(self):
		schema = Basic.__art__.schema
		a = schema.get('a', None)
		s = lookup_portable(lc.Boolean())

		assert id(a) == id(s)

	def test_user(self):
		schema = Array.__art__.schema
		a = schema['a']
		s = lookup_portable(lc.ArrayOf(lc.UserDefined(Basic), 8))

		assert id(a) == id(s)

	def test_by_type(self):
		schema = Array.__art__.schema
		a = schema['a']
		t = lookup_portable(lc.ArrayOf(lc.UserDefined(Basic), 8))
		x = install_portable(lc.ArrayOf(lc.UserDefined(Basic), 9))

		assert id(a) == id(t)
		assert id(a) != id(x)

	def test_by_sub_type_fault(self):
		# Appears in declaration of Array but as a
		# sub-type - consequently it is not installed.
		try:
			t = lookup_portable(lc.UserDefined(Basic))
		except PointConstructionError as e:
			assert True

	def test_by_sub_type_fault(self):
		# Appears in declaration of Array but as a
		# sub-type - consequently it is not installed.
		try:
			t = lookup_portable(lc.UserDefined(Basic))
		except PointConstructionError as e:
			assert True

	def test_by_sub_type(self):
		# Appears in declaration of Basic as a sub-type.
		try:
			t = lookup_portable(lc.MapOf(lc.Unicode(), lc.UUID()))
			assert True
		except PointConstructionError as e:
			assert False
