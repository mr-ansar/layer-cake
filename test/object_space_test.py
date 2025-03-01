# spacing_test.py
"""Testing of the object map at the lowest level.

Bit dubious about this testing. Takes a fair bit of fakery just to get
a few tests going, which detracts from the validity of the testing. At
least it is a mechanism for debugging into the object map with as little
as possible going on.
"""
from unittest import TestCase

import layer_cake as lc
import layer_cake.object_space as lcs
import layer_cake.message_pump as lcp
import layer_cake.point_runtime as lcr

__all__ = [
	'TestSpacing',
]

class ObjectWithPump(lcp.Pump):
	def __init__(self):
		lcp.Pump.__init__(self)
		self.address = lc.NO_SUCH_ADDRESS			# Identity of this object.
		self.queue_address = lc.NO_SUCH_ADDRESS		# Where are messages processed.
		self.parent_address = lc.NO_SUCH_ADDRESS	# Who created this object.
		self.to_address = lc.NO_SUCH_ADDRESS		# Delivery address on current message.
		self.return_address = lc.NO_SUCH_ADDRESS	# Who sent the current message.
		self.assigned_queue = None					# Parent queue for non-threaded machine.
		self.object_ending = None

class ObjectNoPump(object):
	def __init__(self):
		self.address = lc.NO_SUCH_ADDRESS			# Identity of this object.
		self.queue_address = lc.NO_SUCH_ADDRESS		# Where are messages processed.
		self.parent_address = lc.NO_SUCH_ADDRESS	# Who created this object.
		self.to_address = lc.NO_SUCH_ADDRESS		# Delivery address on current message.
		self.return_address = lc.NO_SUCH_ADDRESS	# Who sent the current message.
		self.assigned_queue = None					# Parent queue for non-threaded machine.
		self.object_ending = None

class TestSpacing(TestCase):
	def setUp(self):
		lcs.set_queue(None, lc.NO_SUCH_ADDRESS)

	def tearDown(self):
		pass

	def test_pump(self):
		a1, p1 = lcs.create_an_object(ObjectWithPump, None, None, (), {})
		a2, p2 = lcs.create_an_object(ObjectWithPump, None, None, (), {})

		assert isinstance(a1, tuple)
		assert len(a1) == 1
		assert isinstance(a2, tuple)
		assert len(a2) == 1
		assert a1 != a2

		assert isinstance(p1, ObjectWithPump)
		assert isinstance(p2, ObjectWithPump)
		assert id(p1) != id(p2)
		assert p1.queue_address == p1.object_address
		assert p2.queue_address == p2.object_address

	def test_no_pump(self):
		a1, owp = lcs.create_an_object(ObjectWithPump, None, None, (), {})
		lcs.set_queue(ObjectNoPump, a1)
		a2, onp = lcs.create_an_object(ObjectNoPump, None, None, (), {})

		assert isinstance(owp, ObjectWithPump)
		assert isinstance(onp, ObjectNoPump)
		assert isinstance(owp, lcs.Pump)
		assert id(owp) != id(onp)
		assert owp.queue_address == owp.object_address
		assert onp.queue_address == owp.object_address

		lcs.send_a_message(lcr.Start(), a1, a2)

		m, t, r = owp.get()
		assert isinstance(m, lcr.Start)
		assert t == a1
		assert r == a2

