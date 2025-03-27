# test_caller.py
# Demonstration of the different calling conventions
# available to the developer.
import layer_cake as lc

from enum import Enum
from test_function import function

class CallingConvention(Enum):
	INSTRUCTION=1
	THREAD=2
	PROCESS=3

DEFAULT = CallingConvention.INSTRUCTION

def caller(self, convention: CallingConvention=DEFAULT) -> list[list[float]]:
	'''Apply the selected calling convention. Return a matrix of floats'''

	# Use python calling mechanism.
	if convention == CallingConvention.INSTRUCTION:
		value = function(self, x=2, y=2)

	# Wrap the function in its own thread.
	elif convention == CallingConvention.THREAD:
		a = self.create(function, x=4, y=4)
		r = self.input()
		assert isinstance(r, lc.Returned)
		value = r.value_only()

	# Wrap the function in its own process.
	else:
		a = self.create(lc.ProcessObject, function, x=16, y=16)
		r = self.input()
		assert isinstance(r, lc.Returned)
		value = r.value_only()

	return value

# Register with runtime.
lc.bind(caller)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(caller)
