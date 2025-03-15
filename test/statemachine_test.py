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
from test_statemachine import *

__all__ = [
	'TestStateMachine',
]

list_int_cast = lc.type_cast(list[int])
dict_UUID_Person_cast = lc.type_cast(dict[uuid.UUID, Person])

#
class TestStateMachine(TestCase):
	def test_stateless(self):
		statemachine = Main()
		m, p, f = statemachine.transition(INITIAL, lc.Start())
		assert f == Main_INITIAL_Start
		m, p, f = statemachine.transition(INITIAL, Person())
		assert f == Main_INITIAL_Unknown

		m, p, f = statemachine.transition(READY, lc.int_cast(42))
		assert f == Main_READY_int
		m, p, f = statemachine.transition(READY, list_int_cast([42,21]))
		assert f == Main_READY_list_int
		m, p, f = statemachine.transition(READY, Person('Gwendoline'))
		assert f == Main_READY_Person
		d = {uuid.uuid4(): Person('Hieronymus')}
		m, p, f = statemachine.transition(READY, dict_UUID_Person_cast(d))
		assert f == Main_READY_dict_UUID_Person
		m, p, f = statemachine.transition(READY, lc.Stop())
		assert f == Main_READY_Stop

		m, p, f = statemachine.transition(READY, lc.TimedOut())
		assert f == Main_READY_TimedOut
		m, p, f = statemachine.transition(READY, lc.Faulted())
		assert f == Main_READY_Faulted
		m, p, f = statemachine.transition(READY, lc.Ack())
		assert f == Main_READY_Unknown
