# test_main_args.py
import datetime
import uuid
import layer_cake as lc

from test_person import *

class Catcher(lc.Point, lc.Stateless):
	def __init__(self, ):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)

def Catcher_Start(self, message):
	pass

def Catcher_dict_str_list_Person(self, message):
	person = []
	for v in message.values():
		for p in v:
			person.append(p.given_name)

	csv = ','.join(person)
	self.console(table=csv)

def Catcher_int(self, message):
	self.console(message=message)

def Catcher_float(self, message):
	self.console(message=message)

def Catcher_Person(self, message):
	self.console(person=message.given_name)

def Catcher_datetime(self, message):
	self.console(message=message)

def Catcher_UUID(self, message):
	self.complete()

lc.bind(Catcher, dispatch=(lc.Start,
	dict[str,list[Person]],
	int, float,
	Person,
	datetime.datetime,uuid.UUID))

#
table_type = lc.def_type(dict[str,list[Person]])

class Main(lc.Point, lc.Stateless):
	def __init__(self, table: dict[str,list[Person]]=None,
		count: int=10, ratio: float=0.5,
		who: Person=None, when: datetime.datetime=None,
		unique_id: uuid.UUID=None):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.table = table or dict(recent=[Person('Felicity'), Person('Frederic')])
		self.who = who or Person('Wilfred')
		self.when = when or lc.world_now()
		self.unique_id = unique_id or uuid.uuid4()
		self.count = count
		self.ratio = ratio

def Main_Start(self, message):
	j = self.create(Catcher)
	self.send(lc.cast_to(self.table, table_type), j)
	self.send(lc.cast_to(self.count, lc.int_type), j)
	self.send(lc.cast_to(self.ratio, lc.float_type), j)
	self.send(self.who, j)
	self.send(lc.cast_to(self.when, lc.datetime_type), j)
	self.send(lc.cast_to(self.unique_id, lc.uuid_type), j)

def Main_Returned(self, message):
	# Catcher terminates on receiving UUID.
	self.complete()

def Main_Stop(self, message):
	self.complete()

lc.bind(Main, dispatch=(lc.Start, lc.Returned, lc.Stop))

if __name__ == '__main__':
	lc.create(Main)
