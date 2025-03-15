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

list_int_cast = lc.type_cast(list[int])
dict_UUID_Person_cast = lc.type_cast(dict[uuid.UUID, Person])

#
class TestStateless(TestCase):
	def test_stateless(self):
		stateless = Main()
		m, p, f = stateless.transition(lc.Start())
		assert f == Main_Start
		m, p, f = stateless.transition(lc.int_cast(42))
		assert f == Main_int
		m, p, f = stateless.transition(list_int_cast([42,21]))
		assert f == Main_list_int
		m, p, f = stateless.transition(Person('Gwendoline'))
		assert f == Main_Person
		d = {uuid.uuid4(): Person('Hieronymus')}
		m, p, f = stateless.transition(dict_UUID_Person_cast(d))
		assert f == Main_dict_UUID_Person
		m, p, f = stateless.transition(lc.Stop())
		assert f == Main_Stop
