# test_caller.py
# Demonstration of the different calling conventions
# available to the developer.
from enum import Enum
import layer_cake as lc
from test_function import function

class CallingConvention(Enum):
	TRADITIONAL=1
	THREAD=2
	PROCESS=3

DEFAULT = CallingConvention.TRADITIONAL

def caller(self, convention: CallingConvention=DEFAULT) -> list[list[float]]:
	'''Apply the different calling conventions. Return the selected matrix of floats'''
	direct_call = function(self)

	a = self.create(function, x=2, y=2)
	i, separate_thread, p = self.select(lc.Returned)

	# As a process.
	a = self.create(lc.ProcessObject, function, x=16, y=16)
	i, separate_process, p = self.select(lc.Returned)

	# Gather the 3 results.
	collated = (
		direct_call,					# Straight from the call.
		separate_thread.normalize(),	# Extract from Returned.
		separate_process.normalize(),
	)
	# Return one of them.
	m = collated[convention.value - 1]
	return m

# Register with runtime.
lc.bind(caller)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(caller)
