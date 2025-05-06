# object_startup_test.py
import uuid
from unittest import TestCase
import datetime

import layer_cake as lc
from layer_cake.virtual_memory import *
from layer_cake.command_line import *
from layer_cake.command_startup import *
from layer_cake.object_runtime import *
from layer_cake.object_startup import *
import test_main
import test_main_return
import test_main_return_any
import test_main_args

from test_person import *

__all__ = [
	'TestProcessObject',
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

class TestProcessObject(TestCase):
	def setUp(self):
		# Test framework doesnt like atexit.
		PB.tear_down_atexit = False

		try:
			lc.remove_folder('test-cake')
		except FileNotFoundError:
			pass

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
		lc.start_up(lc.log_to_stderr)
		super().__init__()

	def tearDown(self):
		lc.remove_folder('home')
		lc.tear_down()
		return super().tearDown()

	def test_channel(self):
		with lc.channel() as ch:
			assert isinstance(ch, lc.Channel)

	def test_return_none(self):
		# test_main.main is a procedure - no declared return type.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main.main)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.value is None
		assert m.created_type == lc.ProcessObject

	def test_return_int_expecting_none(self):
		# test_main_return returns values according to flag arguments.
		# Returning int will fail cos there is not enough
		# type info available to write encoding to stdout.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_return.main, return_an_int=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m.value, lc.Faulted)
		s = str(m.value)
		assert 'cannot encode' in s
		assert 'int/Any' in s
		assert m.created_type == lc.ProcessObject

	def test_return_an_int_any(self):
		# Supply type info and it passes back to parent.
		number = 26
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_return.main, return_an_int_any=number)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert isinstance(m.value, tuple)
		assert isinstance(m.value[0], int)
		assert m.value[0] == number
		assert m.created_type == lc.ProcessObject

	def test_return_any_default(self):
		name = 'Gerald'
		height = 50
		width = 50
		who = None # Person(name)
		when = None # lc.world_now()

		# height: int=4, width: int=4, who: Person=None, when: datetime.datetime=None
		# Returns Faulted, table of Person, table of datetime or bool.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_return_any.main)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, tuple)
		assert isinstance(m.value[0], bool)

	def test_return_any_faulted(self):
		name = 'Gerald'
		height = 0	# Out of bounds.
		width = 50
		who = None # Person(name)
		when = None # lc.world_now()

		# height: int=4, width: int=4, who: Person=None, when: datetime.datetime=None
		# Returns Faulted, table of Person, table of datetime or bool.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_return_any.main, height=height)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.Faulted)
		s = str(m.value)
		assert 'out of bounds' in s

	def test_return_any_person(self):
		name = 'Gerald'
		height = 237
		width = 104
		who = Person(name)
		when = None # lc.world_now()

		# height: int=4, width: int=4, who: Person=None, when: datetime.datetime=None
		# Returns Faulted, table of Person, table of datetime or bool.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_return_any.main, height=height, width=width, who=who)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, tuple)
		table = m.value[0]
		shape = m.value[1]
		assert len(table) == height
		first, last = table[0], table[height-1]
		assert isinstance(first, list)
		assert len(first) == width
		assert len(last) == width
		assert isinstance(first[0], Person)
		assert first[0].given_name == name

	def test_return_any_when(self):
		name = 'Gerald'
		height = 603
		width = 811
		who = None	# Person(name)
		when = lc.world_now()

		# height: int=4, width: int=4, who: Person=None, when: datetime.datetime=None
		# Returns Faulted, table of Person, table of datetime or bool.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_return_any.main, height=height, width=width, when=when)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, tuple)
		table = m.value[0]
		shape = m.value[1]
		assert len(table) == height
		first, last = table[0], table[height-1]
		assert isinstance(first, list)
		assert len(first) == width
		assert len(last) == width
		assert isinstance(first[0], datetime.datetime)
		assert first[0] == when

	def test_pass_mixed_args(self):
		table = dict(recent=[Person('Gerard'), Person('Niall')])
		when = lc.world_now()
		unique_id = uuid.uuid4()
		count = 10
		ratio = 0.125

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, table=table, count=count, ratio=ratio, when=when, unique_id=unique_id)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert m.value is None

	def test_pass_mismatched_arg(self):
		table = dict(recent=[Person('Gerard'), Person('Niall')])
		when = lc.world_now()

		table = when

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, table=table)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.Faulted)
		s = str(m.value)
		# None in message is cos of test framework.
		assert 'cannot encode' in s
		assert 'argument "table"' in s
		assert 'datetime/MapOf' in s

	def test_create_role_empty(self):
		# Watch out for materials left in "../layer-cake/test/.layer-cake/test_main_args"
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', create_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'create-role'
		assert response.note == 'empty'

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', delete_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'delete-role'
		assert response.note is None

	def test_create_role_full(self):
		# Full set.
		table = {'recent': [Person('Gerard'), Person('Niall')]}
		when = lc.world_now()
		unique_id = uuid.uuid4()
		count = 10
		ratio = 0.125

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', create_role=True,
			table=table, count=count, ratio=ratio, when=when, unique_id=unique_id)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'create-role'
		assert response.note == 'table,count,ratio,when,unique_id'

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', delete_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'delete-role'
		assert response.note is None

	def test_create_role_update(self):
		# Full set.
		table = dict(recent=[Person('Gerard'), Person('Niall')])
		when = lc.world_now()
		unique_id = uuid.uuid4()
		count = 10
		ratio = 0.125

		# Create with half.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', create_role=True,
			table=table, count=count)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'create-role'
		assert response.note == 'table,count'

		# Add other half plus overlap.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', update_role=True,
			count=count, ratio=ratio, when=when, unique_id=unique_id)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'update-role'
		assert response.note == 'table,count,ratio,when,unique_id'

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', delete_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'delete-role'
		assert response.note is None

	def test_settings_faulted(self):
		# Create with half.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', create_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'create-role'
		assert response.note == 'empty'

		# Repeat.
		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', create_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.Faulted)
		response = str(m.value)
		assert 'already exists' in response

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', delete_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.CommandResponse)
		response = m.value
		assert response.command == 'delete-role'
		assert response.note is None

		with lc.channel() as ch:
			ch.create(lc.ProcessObject, test_main_args.main, home_path='test-cake', role_name='command', delete_role=True)
			m, i = ch.select(lc.Returned, lc.Stop)

		assert isinstance(m, lc.Returned)
		assert m.created_type == lc.ProcessObject
		assert isinstance(m.value, lc.Faulted)
		response = str(m.value)
		assert 'no settings available' in response
