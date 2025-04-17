# test_server.py
# Demonstrate the server side of traditional
# client-server networking.

import layer_cake as lc
from test_api import *
import test_function
import test_library

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)


def server(self, server_address: lc.HostPort=None, flooding: int=64):
	'''Establish a network listen and process API requests. Return nothing.'''
	server_address = server_address or DEFAULT_ADDRESS

	# Open a network port for inbound connections.
	lc.listen(self, server_address)
	m = self.input()
	if isinstance(m, lc.Faulted):	# Something went wrong, e.g. address in use.
		return m
	elif isinstance(m, lc.Stop):	# Interrupted, i.e. control-c.
		return lc.Aborted()

	# Manage a private server, i.e. library.
	library = self.create(lc.ProcessObject, test_library.library)

	# Manage a job spool, i.e. a cluster of libraries.
	spool = self.create(lc.ProcessObjectSpool, test_library.library, responsiveness=0.5)

	# Listening.
	while True:
		m = self.input()

		if isinstance(m, (lc.Accepted, lc.Closed)):
			continue
		elif isinstance(m, lc.Faulted):
			return m
		elif isinstance(m, lc.Stop):
			return lc.Aborted()
		elif isinstance(m, CreateTable):
			pass
		else:
			return lc.Faulted(f'unexpected message {m}')

		# CreateTable.
		request = m
		convention = m.convention
		return_address = self.return_address

		if convention == CallingConvention.CALL:
			response = test_function.function(self, x=request.x, y=request.y)

		elif convention == CallingConvention.THREAD:
			self.create(test_function.function, x=request.x, y=request.y)
			returned = self.input()
			response = returned.value_only()

		elif convention == CallingConvention.PROCESS:
			self.create(lc.ProcessObject, test_function.function, x=request.x, y=request.y)
			returned = self.input()
			response = returned.value_only()

		elif convention == CallingConvention.LIBRARY:
			self.send(request, library)
			response = self.input()

		elif convention == CallingConvention.SPOOL:
			self.send(request, spool)
			response = self.input()

		elif convention == CallingConvention.FLOOD:
			for i in range(flooding):
				self.send(request, spool)
			for i in range(flooding):
				response = self.input()

		else:
			response = lc.Faulted('no such calling convention')
			self.send(response, return_address)
			continue

		self.send(lc.cast_to(response, table_type), return_address)

# Register with runtime.
lc.bind(server, api=(CreateTable,))

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(server)
