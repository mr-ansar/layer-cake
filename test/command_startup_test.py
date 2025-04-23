# convert_hints_test.py
from unittest import TestCase

import layer_cake as lc
from layer_cake.command_line import *
from layer_cake.command_startup import *

__all__ = [
	'TestPocArgs',
]

class C(object): pass

lc.bind_message(C)

class Empty(object):
	def __init__(self):
		pass

class Single(object):
	def __init__(self, a: int=None):
		self.a = a

class BirdsNest(object):
	def __init__(self, a: dict[int, dict[str,list[C]]]=None):
		self.a = a

def empty():
	return

def single(a: int=None) -> bool:
	return True

def birdsnest(a: dict[int, dict[str,list[C]]]):
	return

lc.bind_routine(empty)
lc.bind_routine(single)
lc.bind_routine(birdsnest)

GOOD_FLAGS = ['--full-output=true', 'input', '-hp=other-path', 'output']

SCHEMA = {
	'full_output': lc.Boolean(),
	'home_path': lc.Unicode(),
}

LONG_AND_SHORT = ['--full-output=true', '-fo=true', 'input']

AMBIGUOUS = {
	'runtime_permission': lc.Boolean(),
	'reverse_path': lc.Unicode(),
}

EMPTY = {}


class TestPocArgs(TestCase):
	def test_process_flags(self):
		words, flags = process_flags(GOOD_FLAGS)
		lf, sf = flags

		assert isinstance(words, list)
		assert 'input' in words
		assert 'output' in words

		assert 'full-output' in lf
		assert lf['full-output'] == 'true'

	def test_extract_arguments(self):
		words, flags = process_flags(GOOD_FLAGS)
		extracted, remainder = extract_arguments(SCHEMA, flags)
		assert 'full_output' in extracted
		# Any format.
		assert extracted['full_output'][0] == True

		assert len(remainder[0]) == 0
		assert len(remainder[1]) == 0

	def test_extract_error(self):
		word, flags = process_flags(LONG_AND_SHORT)

		try:
			extract_arguments(SCHEMA, flags)
			assert False
		except ValueError as e:
			assert True

	def test_extract_ambiguous(self):
		word, flags = process_flags(['-rp'])

		try:
			extract_arguments(AMBIGUOUS, flags)
			assert False
		except ValueError as e:
			assert True

	def test_function(self):
		try:
			executable, arguments, word = command_arguments(single, override_arguments=['blah', '--a=10'])
			assert True
		except ValueError as e:
			assert False

	def test_insert_setting(self):
		try:
			executable, arguments, word = command_arguments(single, override_arguments=['blah', '--full-output=true', '--settings-file=content', '--a=10'])
		except ValueError as e:
			assert False

		assert CL.full_output == True
		assert CL.role_file == 'content'
		assert 'a' in arguments
		# Still in any format.
		assert arguments['a'][0] == 10

	def test_extract_unknown(self):
		try:
			executable, arguments, word = command_arguments(empty, override_arguments=['blah', '--no-such-argument=abc', '-nsa=[10,20]'])
			assert False
		except ValueError as e:
			assert True
