# test_main_args.py
import datetime
import uuid
import layer_cake as lc

from test_person import *

class Juggler(lc.Point, lc.Stateless):
	def __init__(self, ):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)

def Juggler_Start(self, message):
	pass

def Juggler_dict_str_list_Person(self, message):
	person = []
	for v in message.values():
		for p in v:
			person.append(p.given_name)

	# Log values.
	csv = ','.join(person)
	self.console(table=csv)

def Juggler_int(self, message):
	self.console(message=message)

def Juggler_float(self, message):
	self.console(message=message)

def Juggler_Person(self, message):
	pass

def Juggler_datetime(self, message):
	pass

def Juggler_UUID(self, message):
	self.complete()

lc.bind(Juggler, dispatch=(lc.Start,
	dict[str,list[Person]],
	int, float,
	Person,
	datetime.datetime,uuid.UUID))

#
table_cast = lc.type_cast(dict[str,list[Person]])

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
	j = self.create(Juggler)
	self.send(table_cast(self.table), j)
	self.send(lc.int_cast(self.count), j)
	self.send(lc.float_cast(self.ratio), j)
	self.send(self.who, j)
	self.send(lc.datetime_cast(self.when), j)
	self.send(lc.uuid_cast(self.unique_id), j)

def Main_Returned(self, message):
	self.complete()

def Main_Stop(self, message):
	self.complete()

lc.bind(Main, dispatch=(lc.Start, lc.Returned, lc.Stop))

if __name__ == '__main__':
	lc.create(Main)
