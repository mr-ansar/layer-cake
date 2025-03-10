#
#
import layer_cake as lc

# MESSAGES ------------------------------------------------------------------------------
class Cook(object):
	def __init__(self, a: int=None, b: dict[int, str]=None, c=None):	# Cant hint here (-> int). Would annoy checkers.
		self.a = a
		self.b = b
		self.c = c

class Radiating(object):
	pass

lc.bind_message(Cook, c=lc.PointerTo(lc.Boolean))
lc.bind_message(Radiating)

# 1. List of message contents and their types (as hints)
# 2. Still must be default constructible (flexible matching policy on decoding)
# 3. Types provided on bind when hints fall short.
# 4. Hints use Python syntax, bind types expect Portable (unfixed) but accept hint or class as well.

# POINT AS FUNCTION ---------------------------------------------------------------------
BR_1 = 1	#lc.branch_table(int, dict[int, str])
JP_1 = 2	#lc.jump_table(a=int, b=dict[int, str])

def main(self, a: int=None, b: dict[int, str]=None, c=None) -> int:
	b = b or {}

	# self.select(h, h, h, ...) -> matching message
	# self.branch(table) -> matching index and message
	# self.jump -> matching index and message after call to jump routine

	isinstance(a, int)
	isinstance(b, dict)

	i, m = self.branch(BR_1)

	def a(self, i):
		return i + 1

	i, r = self.jump(JP_1, a=a)

	return 0

lc.bind_routine(main, c=lc.TimeSpan())

#
#
def poly(self, a: int=None, b: dict[int, str]=None, c=None) -> lc.Any:
	b = b or {}

	isinstance(a, int)
	isinstance(b, dict)

	m, i = self.branch(BR_1)
	if i == 0:
		return (0, None)

	return ({'a':1}, None)

lc.bind_routine(main, c=lc.TimeSpan())
