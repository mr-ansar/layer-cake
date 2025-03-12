# test_main_args.py
import datetime
import uuid
import layer_cake as lc

from test_person import *

def main(self, table: dict[str,list[Person]]=None,
	count: int=10, ratio: float=0.5,
	who: Person=None, when: datetime.datetime=None,
	unique_id: uuid.UUID=None):

	# Traditional defaults.
	table = table or dict(recent=[Person('Felicity'), Person('Frederic')])
	who = who or Person('Wilfred')
	when = when or lc.world_now()
	unique_id = unique_id or uuid.uuid4()

	# Name of every person.
	person = []
	for v in table.values():
		for p in v:
			person.append(p.given_name)

	# Log values.
	csv = ','.join(person)
	self.console(table=csv)
	self.console(count=count, ratio=ratio)
	self.console(who=who.given_name, when=when)
	self.console(unique_id=unique_id)

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
