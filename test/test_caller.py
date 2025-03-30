# test_caller.py
# Demonstration of the different calling conventions
# available to the developer.
import layer_cake as lc
from test_api import *
from test_function import *


def caller(self, convention: CallingConvention=None) -> list[list[float]]:
	'''Apply the selected calling convention. Return a matrix of floats'''
	convention = convention or DEFAULT_CONVENTION

	# Use python calling mechanism.
	if convention == CallingConvention.CALL:
		response = function(self, x=2, y=2)

	# Wrap the function in a dedicated thread.
	elif convention == CallingConvention.THREAD:
		self.create(function, x=4, y=4)
		returned = self.input()
		response = returned.value_only()

	# Wrap the function in a process.
	elif convention == CallingConvention.PROCESS:
		self.create(lc.ProcessObject, function, x=16, y=16)
		returned = self.input()
		response = returned.value_only()

	else:
		response = lc.Faulted(f'unexpected calling convention "{convention}"')

	return response

# Register with runtime.
lc.bind(caller)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(caller)
