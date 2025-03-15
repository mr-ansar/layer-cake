# test_main_args.py
import uuid
import layer_cake as lc

from test_person import *

__all__ = [
	'INITIAL',
	'READY',
	'Main',
	'Main_INITIAL_Start',
	'Main_INITIAL_Faulted',
	'Main_INITIAL_Unknown',
	'Main_READY_int',
	'Main_READY_list_int',
	'Main_READY_Person',
	'Main_READY_dict_UUID_Person',
	'Main_READY_TimedOut',
	'Main_READY_Faulted',
	'Main_READY_Stop',
	'Main_READY_Unknown',
]

class INITIAL: pass
class READY: pass

class Main(lc.Point, lc.StateMachine):
	def __init__(self, height: int=8, width: int=8, value: float=0.125):
		lc.Point.__init__(self)
		lc.StateMachine.__init__(self, INITIAL)
		self.height = height
		self.width = width
		self.value = value

def Main_INITIAL_Start(self, message):
	self.console(height=self.height, width=self.width, value=self.value)
	return READY

def Main_INITIAL_Faulted(self, message):
	self.console(wtf=message)
	return INITIAL

def Main_INITIAL_Unknown(self, message):
	self.console(wtf=message)
	return INITIAL

def Main_READY_int(self, message):
	self.console(message=message)
	return READY

def Main_READY_list_int(self, message):
	self.console(message=message)
	return READY

def Main_READY_Person(self, message):
	self.console(message=message)
	return READY

def Main_READY_dict_UUID_Person(self, message):
	self.console(message=message)
	return READY

def Main_READY_TimedOut(self, message):
	self.console(message=message)
	return READY

def Main_READY_Faulted(self, message):
	self.console(message=message)
	return READY

def Main_READY_Stop(self, message):
	table = [[self.value] * self.height] * self.width
	self.complete(table)

def Main_READY_Unknown(self, message):
	self.console(message=message)
	return READY

MAIN_DISPATCH = {
	INITIAL: ((lc.Start, lc.Faulted, lc.Unknown), ()),
	READY: ((int, list[int], Person, dict[uuid.UUID, Person], lc.TimedOut, lc.Faulted, lc.Stop, lc.Unknown), ()),
}

lc.bind(Main,
	MAIN_DISPATCH,
	return_type=lc.VectorOf(lc.VectorOf(float)))

if __name__ == '__main__':
	lc.create(Main)
