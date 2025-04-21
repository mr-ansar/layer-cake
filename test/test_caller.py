# test_caller.py
import layer_cake as lc

from test_api import *
from test_function import *
from test_library import *


def caller(self, x: int=None, y: int=None, convention: CallingConvention=None) -> list[list[float]]:
	'''Call the test function in different ways. Return the same matrix of floats.'''
	x = x or 2
	y = y or 2
	convention = convention or DEFAULT_CONVENTION

	if convention == CallingConvention.CALL:		# Standard Python call.
		response = texture(self, x=x, y=x)

	elif convention == CallingConvention.THREAD:	# Run texture as a thread.
		self.create(texture, x=x, y=y)
		returned = self.input()						# Thread terminated.
		response = returned.value_only()			# Extract value returned by the function.

	elif convention == CallingConvention.PROCESS:			# Run texture as a process.
		self.create(lc.ProcessObject, texture, x=x, y=y)
		returned = self.input()								# Process terminated.
		response = returned.value_only()					# Extract value returned by the function.

	elif convention == CallingConvention.LIBRARY:			# Run texture as a request to an external process.
		lib = self.create(lc.ProcessObject, library)		# Start the process.

		self.send(Xy(x=x, y=y), lib)						# Submit the request.
		response = self.input()

	else:
		response = lc.Faulted(f'unexpected calling convention "{convention}"')

	return response

lc.bind(caller)					# Register with runtime.

if __name__ == '__main__':		# Process entry-point.
	lc.create(caller)
