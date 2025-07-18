# object_startup_test.py
import uuid
from unittest import TestCase
import os

import layer_cake as lc
from layer_cake.virtual_memory import *
from layer_cake.command_line import *
from layer_cake.command_startup import *
from layer_cake.object_runtime import *
from layer_cake.object_startup import *

__all__ = [
	'TestObjectStartup',
]

class C(object): pass

class Empty(object):
	def __init__(self):
		pass

class Single(object):
	def __init__(self, a: int=None):
		self.a = a

class BirdsNest(object):
	def __init__(self, a: dict[int, dict[str,list[C]]]=None):
		self.a = a

lc.bind_message(C)
lc.bind_message(Empty)
lc.bind_message(Single)
lc.bind_message(BirdsNest)

def empty(self):
	return

def single(self, a: int=None) -> bool:
	return True

def unit_test(self, rootdir: str=None, override_ini: str=None, junit_xml: str=None) -> bool:
	return True

def say_hi(self, rootdir: str=None, override_ini: str=None, junit_xml: str=None) -> bool:
	self.console('Hi')
	return True

def birdsnest(self, a: dict[int, dict[str,list[C]]]):
	return

lc.bind_routine(empty)
lc.bind_routine(single)
lc.bind_routine(unit_test)
lc.bind_routine(say_hi)
lc.bind_routine(birdsnest)

from os.path import join

class TestObjectStartup(TestCase):
	def setUp(self):
		PB.tear_down_atexit = False
		# Hand-roll a bare-bones home of roles.
		f = lc.Folder('home')
		f.folder('client-1')
		f.folder('client-2')
		f.folder('test-1')
		f.folder('test-2')
		f = f.folder('test-3')
		f.file('unique_id', UUID()).store(uuid.uuid4())
		f.file('start_stop', DequeOf(UserDefined(StartStop))).store(deque())
		f.file('settings', MapOf(Unicode(),Any())).store({})
		f.file('log_storage', Integer8()).store(250000000)
		f.file('executable_file', Unicode()).store('xyz.py')

		f = lc.Folder('good')
		f = f.folder('role')
		f = f.folder('one')
		f.file('unique_id', UUID()).store(uuid.uuid4())
		f.file('start_stop', DequeOf(UserDefined(StartStop))).store(deque())
		f.file('settings', MapOf(Unicode(),Any())).store({})
		f.file('log_storage', Integer8()).store(250000000)
		f.file('executable_file', Unicode()).store('xyz.py')
		super().__init__()

	def tearDown(self):
		lc.remove_folder('home')
		return super().tearDown()

	def test_no_role(self):
		r = open_role('no-such-home-role', 'no-such-resource')
		assert r is None

	def test_is_role(self):
		role = join('good', 'role', 'one')
		# Unsure about where to point this in testing context.
		resource = join('good', 'resource')
		r = open_role(role, resource)
		assert isinstance(r, HomeRole)

	def test_no_home(self):
		h = open_home('no-such-home')
		assert h is None

	def test_is_home(self):
		h = open_home('good')
		assert isinstance(h, dict)
		assert len(h) == 1
		assert 'one' in h
		assert h['one'].log_storage() == 250000000

	def test_start_tear(self):
		# Testing the low-level runtime management but
		# cant use the atexit mechanism.
		start_up()
		PB.exit_status = None
		tear_down()
		assert True

	def test_start_light(self):
		return
		lc.create(unit_test)
		PB.exit_status = None
		tear_down()
		value = PB.output_value
		assert isinstance(value, tuple)
		assert isinstance(value[0], bool)
		assert value[0] == True

	def test_start_sticky(self):
		lc.create(unit_test)
		PB.exit_status = None
		tear_down()
		try:
			lc.remove_folder('.layer-cake')
		except FileNotFoundError:
			pass
		assert True

	def test_start_recording(self):
		lc.create(say_hi, sticky=True)
		PB.exit_status = None
		tear_down()
		lc.remove_folder('.layer-cake')

	def test_disk(self):
		lc.create(say_hi, sticky=True)
		PB.exit_status = None

		r = lc.resource_folder()
		m = lc.model_folder()
		t = lc.tmp_folder()

		assert isinstance(r, lc.Folder)
		assert isinstance(m, lc.Folder)
		assert isinstance(t, lc.Folder)

		assert 'resource' in r.path
		assert 'model' in m.path
		assert 'tmp' in t.path

		tear_down()
		lc.remove_folder('.layer-cake')
