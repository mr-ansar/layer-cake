# virtual_routine_test.py
'''First steps in building the point machinery.

There is no supporting runtime expected for these
tests. No logging, no timing and no background
threads for running machines.

Logs go nowhere, i.e. the log_address is NSA.
'''
from unittest import TestCase
from time import sleep

import layer_cake as lc

from layer_cake.virtual_memory import *
from layer_cake.virtual_runtime import *
from layer_cake.object_space import *
from layer_cake.point_runtime import *
from layer_cake.virtual_point import *
from layer_cake.routine_point import *

__all__ = [
	'TestRoutinePoint',
]

# Simple message.
class C(object):
	pass

lc.bind_message(C)

# Simple routine.
def empty(self):
	pass

lc.bind_routine(empty)

# Routine that receives and completes,
def receiver(self) -> int:
	m, t, r = self.get()
	return 42

lc.bind_routine(receiver, a=Address())

# Routine that sends.
def sender(self, a=None) -> int:
	self.send(C(), a)
	return 42

lc.bind_routine(sender, a=Address())

class TestRoutinePoint(TestCase):
	def test_existence(self):
		# A floating, unregistered point with no parent
		# or queue, or anything.
		root = Point()
		assert root.object_address == NO_SUCH_ADDRESS
		assert root.parent_address == NO_SUCH_ADDRESS
		assert root.queue_address == NO_SUCH_ADDRESS

		# Create the first registered point (i.e a Channel)
		c = root.create(Channel)
		assert isinstance(c, Channel)
		assert is_address(c.object_address)
		assert c.parent_address == NO_SUCH_ADDRESS
		assert is_address(c.queue_address)

		a = c.object_address
		f = find_object(a)
		assert isinstance(f, Channel)
		assert id(f) == id(c)

		# Clean is out.
		destroy_an_object(a)
		f = find_object(a)
		assert f is None

	def test_completed(self):
		root = Point()
		c = root.create(Channel)
		assert isinstance(c, Channel)

		# Start the function in a thread and then
		# wait for it to complete.
		a = c.create(empty)
		m, t, r = c.get()

		# Check that Completed came from the
		# instance of empty.
		assert r == a
		assert isinstance(m, Completed)

	def test_send(self):
		root = Point()
		c = root.create(Channel)
		assert isinstance(c, Channel)

		a = c.create(receiver)
		f = find_object(a)
		assert isinstance(f, Channel)

		c.send(C(), a)
		sleep(0.5)
		f = find_object(a)
		assert f is None

	def test_exchange(self):
		root = Point()
		c = root.create(Channel)
		assert isinstance(c, Channel)

		r = c.create(receiver)
		f = find_object(r)
		assert isinstance(f, Channel)

		s = c.create(sender, r)
		sleep(0.5)
		f = find_object(r)
		assert f is None
		f = find_object(s)
		assert f is None

