# message_memory_test.py
from unittest import TestCase
import typing
import types

from typing import get_type_hints

import layer_cake as lc
from layer_cake.convert_type import *
__all__ = [
	'TestMessageMemory',
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
		self.a = a or [0] * 3

class Vector(object):
	def __init__(self, a: list[int]=None):
		self.a = a or []

class Deck(object):
	def __init__(self, a: lc.deque[int]=None):
		self.a = a or lc.deque()

class Set(object):
	def __init__(self, a: set[int]=None):
		self.a = a or set()

class Map(object):
	def __init__(self, a: dict[int, str]=None):
		self.a = a or {}

class C(object): pass

class NotRegistered(object): pass

class M(object):
	def __init__(self, a: int=None, b: float=None):
		self.a = a
		self.b = b

class User(object):
	def __init__(self, a: C=None):
		self.a = a or C()

class BirdsNest(object):
	def __init__(self, a=None):
		self.a = a or {}

class FixExpression(object):
	def __init__(self, a=None):
		self.a = a

class Infer(object):
	def __init__(self, a=10, b=C()):
		self.a = a
		self.b = b

class CantConstruct(object):
	def __init__(self, a):
		self.a = a

class Returning(object):
	def __init__(self, a: int) -> int:
		self.a = a
		return 0

class NotEnough(object):
	def __init__(self, a=None):
		self.a = a

class InferType(object):
	def __init__(self, a=1):
		self.a = a

lc.bind_message(C)
lc.bind_message(M)

'''

def f_empty():
	pass

def f_void() -> None:
	return

def f_boolean() -> bool:
	return True

def f_float() -> float:
	return 1.25

def f_birdsnest() -> dict[int, dict[str,list[C,8]]]:
	return {}
'''

class TestMessageMemory(TestCase):
	def test_default(self):
		lc.default_byte()
		lc.default_character()
		lc.default_rune()
		lc.default_block()
		lc.default_string()
		lc.default_unicode()
		lc.default_clock()
		lc.default_span()
		lc.default_world()
		lc.default_delta()
		lc.default_uuid()
		lc.default_array(lc.Integer8(), 4)
		lc.default_vector()
		lc.default_set()
		lc.default_map()
		lc.default_deque()
		lc.default_none()

		assert True

	def test_empty(self):
		lc.bind_message(Empty)
		rt = Empty.__art__
		assert len(rt.schema) == 0

	def test_single(self):
		lc.bind_message(Single)
		rt = Single.__art__

		assert isinstance(rt.schema, dict)
		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.Integer8)

	def test_basic(self):
		lc.bind_message(Basic)
		rt = Basic.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.Boolean)

		b = rt.schema.get('b', None)
		assert b is not None
		assert isinstance(b, lc.Integer8)

		c = rt.schema.get('c', None)
		assert c is not None
		assert isinstance(c, lc.Float8)

		d = rt.schema.get('d', None)
		assert d is not None
		assert isinstance(d, lc.Unicode)

		e = rt.schema.get('e', None)
		assert e is not None
		assert isinstance(e, lc.String)

		f = rt.schema.get('f', None)
		assert f is not None
		assert isinstance(f, lc.Block)

	def test_array(self):
		lc.bind_message(Array, a=lc.ArrayOf(lc.Integer8(), 3))
		rt = Array.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.ArrayOf)
		assert isinstance(a.element, lc.Integer8)
		assert a.size == 3

	def test_vector(self):
		lc.bind_message(Vector)
		rt = Vector.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.VectorOf)
		assert isinstance(a.element, lc.Integer8)

	def test_deck(self):
		lc.bind_message(Deck)
		rt = Deck.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.DequeOf)
		assert isinstance(a.element, lc.Integer8)

	def test_set(self):
		lc.bind_message(Set)
		rt = Set.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.SetOf)
		assert isinstance(a.element, lc.Integer8)

	def test_map(self):
		lc.bind_message(Map)
		rt = Map.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.MapOf)
		assert isinstance(a.key, lc.Integer8)
		assert isinstance(a.value, lc.Unicode)

	def test_user(self):
		lc.bind_message(User)
		rt = User.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.UserDefined)
		assert a.element == C

	def test_birdsnest(self):
		lc.bind_message(BirdsNest, a=lc.MapOf(lc.Integer8(), lc.MapOf(lc.Unicode(),lc.ArrayOf(lc.Integer8(), 3))))
		rt = BirdsNest.__art__

		a = rt.schema.get('a', None)
		assert a is not None
		assert isinstance(a, lc.MapOf)
		k = a.key
		v = a.value
		assert isinstance(k, lc.Integer8)
		assert isinstance(v, lc.MapOf)
		k2 = v.key
		v2 = v.value
		assert isinstance(k2, lc.Unicode)
		assert isinstance(v2, lc.ArrayOf)
		element = v2.element
		size = v2.size
		assert isinstance(element, lc.Integer8)
		assert size == 3

	def test_is(self):
		e = NotRegistered()
		assert not lc.is_message(e)
		assert not lc.is_message_class(NotRegistered)

		c = C()
		assert lc.is_message(c)
		assert lc.is_message_class(C)

	def test_fix_builtin_class(self):
		lc.bind_message(FixExpression, a=int)
		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.Integer8)

	def test_fix_builtin_instance(self):
		lc.bind_message(FixExpression, a=lc.Integer8)
		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.Integer8)

	def test_cant_fix_container(self):
		try:
			lc.bind_message(FixExpression, a=dict)
			assert False
		except ValueError:
			assert True

	def test_fix_memory_class(self):
		lc.bind_message(FixExpression, a=lc.Boolean)

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.Boolean)

	def test_cant_fix_container_class(self):
		try:
			lc.bind_message(FixExpression, a=lc.VectorOf)
			assert False
		except ValueError as e:
			assert True

	def test_fix_nested_class(self):
		lc.bind_message(FixExpression, a=lc.ArrayOf(lc.Boolean,4))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.ArrayOf)
		assert isinstance(a.element, lc.Boolean)

	def test_fix_vector(self):
		lc.bind_message(FixExpression, a=lc.VectorOf(lc.Boolean()))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.VectorOf)

	def test_fix_set(self):
		lc.bind_message(FixExpression, a=lc.SetOf(lc.Integer8()))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.SetOf)

	def test_fix_map(self):
		lc.bind_message(FixExpression, a=lc.MapOf(lc.Integer8(), lc.Unicode()))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.MapOf)

	def test_fix_deque(self):
		lc.bind_message(FixExpression, a=lc.DequeOf(lc.Integer8()))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.DequeOf)

	def test_fix_user_defined(self):
		lc.bind_message(FixExpression, a=lc.UserDefined(C))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.UserDefined)
		assert a.element == C

	def test_fix_user_defined_class(self):
		lc.bind_message(FixExpression, a=C)

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.UserDefined)
		assert a.element == C

	def test_cant_fix_unknown(self):
		try:
			lc.bind_message(FixExpression, a=lc.UserDefined(NotRegistered))
			assert False
		except ValueError as e:
			assert True

	def test_fix_pointer_to(self):
		lc.bind_message(FixExpression, a=lc.PointerTo(lc.UserDefined(C)))

		rt = FixExpression.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.PointerTo)
		assert isinstance(a.element, lc.UserDefined)
		assert a.element.element == C

	def test_infer_type(self):
		lc.bind_message(Infer)

		rt = Infer.__art__

		a = rt.schema.get('a', None)
		assert isinstance(a, lc.Integer8)

	def test_cant_construct(self):
		try:
			lc.bind_message(CantConstruct)
			assert False
		except lc.MessageRegistrationError:
			assert True

	def test_returning(self):
		try:
			lc.bind_message(Returning)
			assert False
		except lc.MessageRegistrationError:
			assert True

	def test_not_enough(self):
		try:
			lc.bind_message(NotEnough)
			assert False
		except lc.MessageRegistrationError as e:
			s = str(e)
			assert True

	def test_cant_fix_non_message(self):
		try:
			lookup_portable(lc.UTC)
			assert False
		except ValueError as e:
			assert True

	def test_equal_to(self):
		a = C()
		b = C()
		assert lc.equal_to(a, b)

		a = 0
		b = 0
		assert lc.equal_to(a, b)

		a = 0
		b = C()
		assert not lc.equal_to(a, b)

		a = [0]
		b = [0]
		t = lc.ArrayOf(lc.Integer8(), 1)
		assert lc.equal_to(a, b, t)

		a = [0]
		b = [0]
		t = lc.VectorOf(lc.Integer8())
		assert lc.equal_to(a, b, t)

		a = lc.deque([0])
		b = lc.deque([0])
		t = lc.DequeOf(lc.Integer8())
		assert lc.equal_to(a, b, t)

		a = set([0])
		b = set([0])
		t = lc.SetOf(lc.Integer8())
		assert lc.equal_to(a, b, t)

		a = {'a':0}
		b = {'a':0}
		t = lc.MapOf(lc.Unicode(),lc.Integer8())
		assert lc.equal_to(a, b, t)

		a = C()
		b = C()
		assert lc.equal_to(a, b, lc.UserDefined(C))

		a = C()
		b = C()
		assert lc.equal_to(a, b, lc.PointerTo(lc.UserDefined(C)))

		a = C()
		b = C()
		assert lc.equal_to(a, b, lc.Any())

		a = M()
		b = M()
		assert lc.equal_to(a, b)

		#def f_empty():
		#def f_void() -> None:
		#def f_boolean() -> bool:
		#def f_float() -> float:
		#def f_birdsnest() -> dict[int, dict[str,list[C,8]]]:

	'''
	def test_f_empty(self):
		h = get_type_hints(f_empty)
		assert isinstance(h, dict)
		assert len(h) == 0

	def test_f_void(self):
		h = get_type_hints(f_void)
		t = h.get('return', None)
		a = lc.hint_to_memory(t)
		assert a is None

	def test_f_boolean(self):
		h = get_type_hints(f_boolean)
		t = h.get('return', None)
		a = lc.hint_to_memory(t)
		assert isinstance(a, lc.Boolean)

	def test_f_float(self):
		h = get_type_hints(f_float)
		t = h.get('return', None)
		a = lc.hint_to_memory(t)
		assert isinstance(a, lc.Float8)

	def test_birdsnest(self):
		h = get_type_hints(f_birdsnest)
		t = h.get('return', None)
		a = lc.hint_to_memory(t)

		assert isinstance(a, lc.MapOf)
		k = a.key
		v = a.value
		assert isinstance(k, lc.Integer8)
		assert isinstance(v, lc.MapOf)
		k2 = v.key
		v2 = v.value
		assert isinstance(k2, lc.Unicode)
		assert isinstance(v2, lc.ArrayOf)
		element = v2.element
		size = v2.size
		assert isinstance(element, lc.UserDefined)
		assert size == 8
		assert element.element == C
	'''
