# test_test.py
from unittest import TestCase
from enum import Enum

import layer_cake as lc

__all__ = [
	'TestVirtualMemory',
]

# Unregistered but good enough.
class Faulty(object): pass

class METHOD_OF_TRANSPORT(Enum):
	CAR=1
	TRUCK=2
	VAN=3
	RAIL=4
	PLANE=5
	BUS=6
	OTHER=7

class TestVirtualMemory(TestCase):
	def test_module_access(self):
		b = lc.Boolean()
		assert isinstance(b, lc.Boolean)

	def test_construction(self):
		lc.Boolean(),

		lc.Integer2(), lc.Integer4(), lc.Integer8(),
		lc.Unsigned2(), lc.Unsigned4(), lc.Unsigned8(),

		# Floats.
		lc.Float4(), lc.Float8(),

		# Bytes, ASCII and unicode.
		lc.Byte(), lc.Character(), lc.Rune(),
		lc.Block(), lc.String(), lc.Unicode(),

		# Name for a number.
		lc.Enumeration(METHOD_OF_TRANSPORT),

		# Time.
		lc.ClockTime(), lc.TimeSpan(),
		lc.WorldTime(), lc.TimeDelta(),

		lc.UUID(),

		# Containers.
		lc.ArrayOf(lc.Boolean(), 10), lc.VectorOf(lc.Boolean()), lc.DequeOf(lc.Boolean()),
		lc.SetOf(lc.Boolean()), lc.MapOf(lc.String(), lc.Boolean()),

		lc.UserDefined(Faulty),
		lc.PointerTo(lc.Boolean()),
		lc.Any(),

		# Networking.
		lc.TargetAddress(),
		lc.Address(),

		# Internal.
		lc.Type(),
		lc.Word()

		b = True
		assert b == True

	def test_enumeration(self):
		assert METHOD_OF_TRANSPORT(3).name == 'VAN'
		assert METHOD_OF_TRANSPORT['BUS'].value == 6
		assert METHOD_OF_TRANSPORT.BUS.value == 6

	def test_predicates(self):
		b = lc.is_portable(lc.Boolean())
		assert b
		assert lc.is_container(lc.VectorOf(lc.Boolean()))
		assert lc.is_structural(lc.ArrayOf(lc.Boolean(), 10))
		assert lc.is_portable_class(lc.Boolean)
		assert lc.is_container_class(lc.VectorOf)
		a = (1, 2, 3)
		assert lc.is_address(a)
		a = (32, 64)
		p = (64,)
		assert lc.address_on_proxy(a, p)
