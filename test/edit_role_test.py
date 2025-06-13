# edit_role_test.py
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
	'TestEditRole',
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

class TestEditRole(TestCase):
	def setUp(self):
		# Test framework doesnt like atexit.
		PB.tear_down_atexit = False

		try:
			lc.remove_folder('test-cake')
		except FileNotFoundError:
			pass

		# Hand-roll a bare-bones home of roles.
		f = lc.Folder('home')
		r = f.folder('resource')
		r.folder('xyz.py')
		f = f.folder('role')
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
		lc.start_up(lc.log_to_stderr)
		super().__init__()

	def tearDown(self):
		lc.remove_folder('home')
		lc.tear_down()
		return super().tearDown()

	def test_edit_role(self):
		role = join('home', 'role', 'test-3')
		# Unsure about where to point this in testing context.
		resource = join('home', 'role', 'test-3')
		r = open_role(role, resource)
		assert isinstance(r, HomeRole)
		with lc.channel() as ch:
			m = lc.edit_role(ch, r, editor='test-passthru-editor')
			assert isinstance(m, lc.Faulted)
			assert 'settings not modified' in m.condition
