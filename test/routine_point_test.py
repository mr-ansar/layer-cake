# virtual_routine_test.py
from unittest import TestCase

import layer_cake as lc

__all__ = [
	'TestRoutinePoint',
]

class C(object): pass

lc.bind_message(C)

def empty():
	pass

def return_none() -> None:
	return None

def return_boolean() -> bool:
	return True

def return_float() -> float:
	return 1.25

def return_birdsnest() -> dict[int, dict[str,list[C]]]:
	return {}

class TestRoutinePoint(TestCase):
	def test_empty(self):
		lc.bind_routine(empty)
		rt = empty.__art__
		assert len(rt.schema) == 0
		assert rt.return_type is None

	def test_builtin(self):
		lc.bind_routine(empty, return_type=int)
		rt = empty.__art__
		assert isinstance(rt.return_type, lc.Integer8)

	def test_virtual(self):
		lc.bind_routine(empty, return_type=lc.Integer8())
		rt = empty.__art__
		assert isinstance(rt.return_type, lc.Integer8)

	#def test_virtual_class(self):
	#	try:
	#		lc.bind_routine(empty, return_type=lc.VectorOf)
	#		assert False
	#	except lc.PointConstructionError:
	#		pass

	def test_none(self):
		lc.bind_routine(return_none)
		rt = return_none.__art__
		assert len(rt.schema) == 0
		assert rt.return_type is None

	def test_boolean(self):
		lc.bind_routine(return_boolean)
		rt = return_boolean.__art__
		assert isinstance(rt.return_type, lc.Boolean)

	def test_float(self):
		lc.bind_routine(return_float)
		rt = return_float.__art__
		assert isinstance(rt.return_type, lc.Float8)

	def test_birdsnest(self):
		lc.bind_routine(return_birdsnest, return_type=lc.MapOf(lc.Integer8(), lc.MapOf(lc.Unicode(),lc.VectorOf(lc.UserDefined(C)))))
		rt = return_birdsnest.__art__
		assert isinstance(rt.return_type, lc.MapOf)
		k = rt.return_type.key
		v = rt.return_type.value
		assert isinstance(k, lc.Integer8)
		assert isinstance(v, lc.MapOf)
		k = v.key
		v = v.value
		assert isinstance(k, lc.Unicode)
		assert isinstance(v, lc.VectorOf)
		e = v.element
		assert isinstance(e, lc.UserDefined)
		assert e.element == C
