# memory_parser_test.py
from unittest import TestCase
from enum import Enum

import layer_cake as lc
import layer_cake.convert_type as mp

__all__ = [
	'TestMemoryParser',
]

class C(object): pass

lc.bind_message(C)

class MOT(Enum):
	CAR=1
	BIKE=2

def check_type(t):
	s = mp.type_signature(t)
	p = mp.signature_type(s)
	assert t.__class__ == p.__class__

NO_ARGS = [
		lc.Boolean,

		lc.Integer2,
		lc.Integer4,
		lc.Integer8,

		lc.Unsigned2,
		lc.Unsigned4,
		lc.Unsigned8,

		lc.Float4,
		lc.Float8,

		lc.Byte,
		lc.Block,
		lc.Character,
		lc.String,
		lc.Rune,
		lc.Unicode,

		lc.ClockTime,
		lc.TimeSpan,
		lc.WorldTime,
		lc.TimeDelta,

		lc.UUID,
		lc.Any,
		lc.TargetAddress,
		lc.Address,
		lc.Type,
		lc.Word,
]

class TestMemoryParser(TestCase):
	def test_basic(self):
		for t in NO_ARGS:
			check_type(t())

	def test_user_defined(self):
		check_type(lc.UserDefined(C))

	def test_enumeration(self):
		check_type(lc.Enumeration(MOT))

	def test_vector(self):
		for t in NO_ARGS:
			check_type(lc.VectorOf(t()))

	def test_array(self):
		for t in NO_ARGS:
			check_type(lc.ArrayOf(t(), 2))
		check_type(lc.ArrayOf(lc.Enumeration(MOT), 8))
		check_type(lc.ArrayOf(lc.UserDefined(C), 128))
		check_type(lc.ArrayOf(lc.ArrayOf(lc.UserDefined(C), 16), 16))

	def test_deque(self):
		for t in NO_ARGS:
			check_type(lc.DequeOf(t()))
		check_type(lc.DequeOf(lc.Enumeration(MOT)))
		check_type(lc.DequeOf(lc.UserDefined(C)))

	def test_set(self):
		check_type(lc.SetOf(lc.Boolean()))
		check_type(lc.SetOf(lc.Integer8()))
		check_type(lc.SetOf(lc.Enumeration(MOT)))
		check_type(lc.SetOf(lc.UserDefined(C)))

	def test_map(self):
		for t in NO_ARGS:
			check_type(lc.MapOf(lc.Integer8(), t()))
		check_type(lc.MapOf(lc.Boolean(), lc.Unicode()))
		check_type(lc.MapOf(lc.Integer8(), lc.Integer8()))
		check_type(lc.MapOf(lc.Enumeration(MOT), lc.SetOf(lc.Unsigned8())))
		check_type(lc.MapOf(lc.Integer8(), lc.ArrayOf(lc.UserDefined(C), 4)))
