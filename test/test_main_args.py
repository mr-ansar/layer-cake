# test_main_args.py
import datetime
import uuid
import layer_cake as lc

from test_person import *

def main(self, table: dict[str,list[Person]]=None, count: int=10, ratio: float=0.5, when: datetime.datetime=None, unique_id: uuid.UUID=None):
	# Ensure printable values.
	table = table or dict(recent=[Person('Felicity'), Person('Frederic')])
	when = when or lc.world_now()
	unique_id = unique_id or uuid.uuid4()

	person = []
	for v in table.values():
		for p in v:
			person.append(p.given_name)

	csv = ','.join(person)

	self.console(f'table: {csv}')
	self.console(f'count: {count}, ratio: {ratio}')
	self.console(f'when: {when}, unique_id: {unique_id}')

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
