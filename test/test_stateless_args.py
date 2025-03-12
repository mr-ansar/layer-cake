# test_main_args.py
import datetime
import uuid
import layer_cake as lc

from test_person import *

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
	# Name of every person.
	person = []
	for v in self.table.values():
		for p in v:
			person.append(p.given_name)

	# Log values.
	csv = ','.join(person)
	self.console(table=csv)
	self.console(count=self.count, ratio=self.ratio)
	self.console(who=self.who.given_name, when=self.when)
	self.console(unique_id=self.unique_id)

	self.complete()

lc.bind(Main, dispatch=(lc.Start,))

if __name__ == '__main__':
	lc.create(Main)
