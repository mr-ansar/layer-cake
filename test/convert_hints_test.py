# convert_hints_test.py
from unittest import TestCase
import typing
import types

from typing import get_type_hints

import layer_cake as lc

__all__ = [
	'TestConvertHints',
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
		self.a = a or [0] * 8

class Vector(object):
	def __init__(self, a: list[int]=None):
		self.a = a

class Deck(object):
	def __init__(self, a: lc.deque[int]=None):
		self.a = a

class Set(object):
	def __init__(self, a: set[int]=None):
		self.a = a

class Map(object):
	def __init__(self, a: dict[int, str]=None):
		self.a = a

class C(object): pass

class User(object):
	def __init__(self, a: C=None):
		self.a = a

class BirdsNest(object):
	def __init__(self, a: dict[int, dict[str,list[C]]]=None):
		self.a = a

def f_empty():
	pass

def f_void() -> None:
	return

def f_boolean() -> bool:
	return True

def f_float() -> float:
	return 1.25

def f_birdsnest() -> dict[int, dict[str,list[C]]]:
	return {}

class TestConvertHints(TestCase):
	def test_empty(self):
		h = get_type_hints(Empty.__init__)
		assert len(h) == 0

	def test_single(self):
		h = get_type_hints(Single.__init__)
		a = h.get('a', None)
		t = lc.lookup_hint(a)

		assert isinstance(t, lc.Integer8)

	def test_basic(self):
		h = get_type_hints(Basic.__init__)
		t = h.get('a', None)
		a = lc.lookup_hint(t)
		t = h.get('b', None)
		b = lc.lookup_hint(t)
		t = h.get('c', None)
		c = lc.lookup_hint(t)
		t = h.get('d', None)
		d = lc.lookup_hint(t)
		t = h.get('e', None)
		e = lc.lookup_hint(t)
		t = h.get('f', None)
		f = lc.lookup_hint(t)

		assert isinstance(a, lc.Boolean)
		assert isinstance(b, lc.Integer8)
		assert isinstance(c, lc.Float8)
		assert isinstance(d, lc.Unicode)
		assert isinstance(e, lc.String)
		assert isinstance(f, lc.Block)

	def test_array(self):
		lc.bind_message(Array, a=lc.ArrayOf(lc.Integer8(), 8))
		schema = Array.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.ArrayOf)
		assert isinstance(t.element, lc.Integer8)
		assert t.size == 8

	def test_vector(self):
		lc.bind_message(Vector)
		schema = Vector.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.VectorOf)
		assert isinstance(t.element, lc.Integer8)

	def test_deck(self):
		lc.bind_message(Deck)
		schema = Deck.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.DequeOf)
		assert isinstance(t.element, lc.Integer8)

	def test_set(self):
		lc.bind_message(Set)
		schema = Set.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.SetOf)
		assert isinstance(t.element, lc.Integer8)

	def test_map(self):
		lc.bind_message(Map)
		schema = Map.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.MapOf)
		assert isinstance(t.key, lc.Integer8)
		assert isinstance(t.value, lc.Unicode)

	def test_user(self):
		lc.bind_message(C)
		lc.bind_message(User)
		schema = User.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.UserDefined)
		assert t.element == C

	def test_birdsnest(self):
		lc.bind_message(C)
		lc.bind_message(BirdsNest)
		schema = BirdsNest.__art__.schema
		t = schema.get('a', None)

		assert isinstance(t, lc.MapOf)
		k = t.key
		v = t.value
		assert isinstance(k, lc.Integer8)
		assert isinstance(v, lc.MapOf)
		k2 = v.key
		v2 = v.value
		assert isinstance(k2, lc.Unicode)
		assert isinstance(v2, lc.VectorOf)
		element = v2.element
		assert isinstance(element, lc.UserDefined)
		assert element.element == C

	#
	#
	def test_f_empty(self):
		lc.bind_routine(f_empty)
		art = f_empty.__art__
		schema, return_type = art.schema, art.return_type
		assert isinstance(schema, dict)
		assert len(schema) == 0
		assert return_type is None

	def test_f_void(self):
		lc.bind_routine(f_void)
		art = f_empty.__art__
		schema, return_type = art.schema, art.return_type
		assert return_type is None

	def test_f_boolean(self):
		lc.bind_routine(f_boolean)
		art = f_boolean.__art__
		schema, return_type = art.schema, art.return_type
		assert isinstance(return_type, lc.Boolean)

	def test_f_float(self):
		lc.bind_routine(f_float)
		art = f_float.__art__
		schema, return_type = art.schema, art.return_type
		assert isinstance(return_type, lc.Float8)

	def test_birdsnest_return(self):
		lc.bind_message(C)
		lc.bind_routine(f_birdsnest)
		art = f_birdsnest.__art__
		schema, return_type = art.schema, art.return_type

		assert isinstance(return_type, lc.MapOf)
		k = return_type.key
		v = return_type.value
		assert isinstance(k, lc.Integer8)
		assert isinstance(v, lc.MapOf)
		k2 = v.key
		v2 = v.value
		assert isinstance(k2, lc.Unicode)
		assert isinstance(v2, lc.VectorOf)
		element = v2.element
		assert isinstance(element, lc.UserDefined)
		assert element.element == C
