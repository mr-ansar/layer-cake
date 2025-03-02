# object_startup_test.py
import layer_cake as lc


class C(object):
	def __init__(self, x: float=0.75):
		self.x = x

lc.bind_message(C)

def main(self, a: dict[int, dict[str,list[C]]]=None, b: int=10, c: int=0, d: C=None, e: list[int]=None) -> C:
	d = d or C()
	self.console(f'{d.x}')
	value = [c] * b
	return d	# ([c] * b, lc.VectorOf(lc.Integer8()))

lc.bind_routine(main)

if __name__ == '__main__':
	lc.create(main, sticky=True)
