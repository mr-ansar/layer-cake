# test_library.py
import layer_cake as lc

from test_api import *
from test_function import *


def library(self):
	'''Accept requests from the framework.'''

	# The process runs until it receives a Stop.
	while True:
		m = self.input()

		if isinstance(m, Xy):				# Expected request.
			pass
		elif isinstance(m, (lc.Delivered, lc.Dropped)):		# Check for faults and control-c.
			continue
		elif isinstance(m, lc.Faulted):		# Check for faults and control-c.
			return m
		elif isinstance(m, lc.Stop):
			return lc.Aborted()
		else:
			self.warning(f'unexpected message')

		# Call the function directly and send the
		# results back to the client.
		table = texture(self, x=m.x, y=m.y)
		self.send(lc.cast_to(table, table_type), self.return_address)

lc.bind(library, api=(Xy,))		# Register with the framework. Declare the API.

if __name__ == '__main__':		# Process entry-point.
	lc.create(library)
