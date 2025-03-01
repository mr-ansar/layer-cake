# make_memory_test.py
""".

.
"""
from unittest import TestCase
from enum import Enum

import layer_cake as lc
from layer_cake.make_message import *
from test_message import *

__all__ = [
	'TestMakeMemory',
]

class MOT(Enum):
	CAR=1
	MOTORBIKE=2

class TestMakeMemory(TestCase):
	def test_make(self):
		make(lc.Boolean())
		make(lc.Integer2())
		make(lc.Integer4())
		make(lc.Integer8())
		make(lc.Unsigned2())
		make(lc.Unsigned4())
		make(lc.Unsigned8())
		make(lc.Float4())
		make(lc.Float8())
		make(lc.Byte())
		make(lc.Character())
		make(lc.Rune())
		make(lc.Block())
		make(lc.String())
		make(lc.Unicode())
		make(lc.WorldTime())
		make(lc.TimeDelta())
		make(lc.ClockTime())
		s = make(lc.TimeSpan())

		assert s is None

		make(lc.UUID())
		e = make(lc.Enumeration(MOT))

		assert e is None

		make(lc.Type())
		make(lc.TargetAddress())
		make(lc.Address())
		make(lc.PointerTo(PlainTypes))
		make(lc.Any())

		make(lc.VectorOf(lc.Integer8()))
		a = make(lc.ArrayOf(lc.Integer8(), 8))

		make(lc.DequeOf(lc.Integer8()))
		make(lc.SetOf(lc.Integer8()))
		m = make(lc.MapOf(lc.Integer8(), lc.Unicode()))
		p = make(lc.UserDefined(PlainTypes))

		assert isinstance(m, dict)
		assert len(m) == 0
		assert isinstance(a, list)
		assert len(a) == 8
		assert isinstance(p, PlainTypes)

	def test_fake(self):
		fake(lc.Boolean())
		fake(lc.Integer2())
		fake(lc.Integer4())
		fake(lc.Integer8())
		fake(lc.Unsigned2())
		fake(lc.Unsigned4())
		fake(lc.Unsigned8())
		fake(lc.Float4())
		fake(lc.Float8())
		fake(lc.Byte())
		fake(lc.Character())
		fake(lc.Rune())
		fake(lc.Block())
		fake(lc.String())
		fake(lc.Unicode())
		fake(lc.WorldTime())
		fake(lc.TimeDelta())
		fake(lc.ClockTime())
		s = fake(lc.TimeSpan())

		assert isinstance(s, float)

		fake(lc.UUID())
		e = fake(lc.Enumeration(MOT))

		assert isinstance(e, Enum)

		fake(lc.Type())
		fake(lc.TargetAddress())
		fake(lc.Address())
		fake(lc.PointerTo(lc.UserDefined(PlainTypes)))
		fake(lc.Any())

		v = fake(lc.VectorOf(lc.Integer8()))
		a = fake(lc.ArrayOf(lc.Integer8(), 8))
		d = fake(lc.DequeOf(lc.Integer8()))
		s = fake(lc.SetOf(lc.Integer8()))
		m = fake(lc.MapOf(lc.Integer8(), lc.Unicode()))
		p = fake(lc.UserDefined(PlainTypes))

		assert isinstance(v, list)
		assert len(v) == 1
		assert isinstance(v[0], int)

		assert isinstance(a, list)
		assert len(a) == 8
		assert isinstance(a[7], int)

		assert isinstance(d, lc.deque)
		assert len(d) == 1
		assert isinstance(d[0], int)

		assert isinstance(s, set)
		assert len(s) == 1
		assert isinstance(next(iter(s)), int)

		assert isinstance(m, dict)
		assert len(m) == 1
		k, v = next(iter(m.items()))
		assert isinstance(k, int)
		assert isinstance(v, str)

		assert isinstance(p, PlainTypes)

