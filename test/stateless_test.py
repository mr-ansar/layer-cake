# object_startup_test.py
import uuid
from unittest import TestCase

import layer_cake as lc
from layer_cake.virtual_memory import *
from layer_cake.command_line import *
from layer_cake.command_startup import *
from layer_cake.object_runtime import *
from layer_cake.object_startup import *

from test_person import *
from test_stateless import *

__all__ = [
	'TestStateless',
]

list_int_type = lc.def_type(list[int])
dict_UUID_Person_type = lc.def_type(dict[uuid.UUID, Person])

#
class TestStateless(TestCase):
	def test_stateless(self):
		stateless = Main()
		m, p, a, f = stateless.transition(lc.Start())
		assert f == Main_Start
		m, p, a, f = stateless.transition(lc.cast_to(42, lc.int_type))
		assert f == Main_int
		m, p, a, f = stateless.transition(lc.cast_to([42,21], list_int_type))
		assert f == Main_list_int
		m, p, a, f = stateless.transition(Person('Gwendoline'))
		assert f == Main_Person
		d = {uuid.uuid4(): Person('Hieronymus')}
		m, p, a, f = stateless.transition(lc.cast_to(d, dict_UUID_Person_type))
		assert f == Main_dict_UUID_Person
		m, p, a, f = stateless.transition(lc.Stop())
		assert f == Main_Stop
