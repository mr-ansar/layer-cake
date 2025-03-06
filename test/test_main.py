# object_startup_test.py
import datetime
import layer_cake as lc

from test_person import *

TYPE_A = dict[int, dict[str,list[Person]]]
ARGUMENT_A = {10: {'S': [Person('Martha'), Person('Hortense'), Person('Gertrude')]}}
PORTABLE_A = lc.MapOf(lc.Integer8(),lc.MapOf(lc.Unicode(),lc.VectorOf(lc.UserDefined(Person))))

def main(self, a: TYPE_A=None, b: int=10, c: int=0, d: Person=None, e: list[int]=None, t: datetime.datetime=None):
	a = a or ARGUMENT_A
	d = d or Person()
	if t is None:
		self.console(f'b: {b}, c: {c}')
	else:
		self.console(f'b: {b}, c: {c}, t: {lc.world_to_text(t)}')
	value = [c] * b
	return (ARGUMENT_A[10]['S'], lc.VectorOf(lc.UserDefined(Person)))

lc.bind(main, return_type=lc.Any())

if __name__ == '__main__':
	lc.create(main)
