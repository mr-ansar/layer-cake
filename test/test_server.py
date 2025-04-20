# test_server.py
# Demonstrate the server side of traditional
# client-server networking.

import layer_cake as lc
from test_api import *
import test_function
import test_library
import random

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

random.seed()

def breather(period):
    s = int(period / 0.1) + 1
    b = int(s * 0.65)		# Quicker.
    e = int(s * 1.75)		# Slower.
    a = random.randrange(b, e) * 0.1
    if a < 0.25:
        return 0.25
    return a

def flood(self, spool, request, flooding) -> list[list[float]]:
	for i in range(flooding):
		self.send(request, spool)

	for i in range(flooding):
		response = self.input()
		if isinstance(response, lc.Stop):
			return lc.Aborted()

	return response

lc.bind(flood)

def soak(self, spool, request, flooding, soaking) -> list[list[float]]:
	for i in range(soaking):
		for j in range(flooding):
			self.send(request, spool)

		for j in range(flooding):
			response = self.input()
			if isinstance(response, lc.Stop):
				return lc.Aborted()

		self.start(lc.T1, breather(2.0))
		m = self.input()
		if isinstance(m, lc.Stop):
			return lc.Aborted()
	return response

lc.bind(soak)

def server(self, server_address: lc.HostPort=None, flooding: int=64, soaking: int=100):
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
	library = self.create(lc.ProcessObject, 'test_library', role_name='library', object_api=(Xy,))

	# Manage a job spool, i.e. a cluster of libraries.
	spool = self.create(lc.ProcessObjectSpool, test_library.library, role_name='spool', process_count=32, responsiveness=0.5)

	#
	client = {}

	# Listening.
	while True:
		m = self.input()

		if isinstance(m, lc.Accepted):
			client[self.return_address] = m
			continue
		elif isinstance(m, lc.Closed):
			c = client.pop(self.return_address, None)
			continue
		elif isinstance(m, lc.Faulted):
			return m
		elif isinstance(m, lc.Returned):
			d = self.debrief()
			if isinstance(d, lc.OnReturned):
				d(m, self)
			continue
		elif isinstance(m, lc.Stop):
			return lc.Aborted()
		elif isinstance(m, Xy):
			pass
		else:
			return lc.Faulted(f'unexpected message {m}')

		# Xy.
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
			f = self.create(flood, spool, request, flooding)

			def drained(value, kv):
				self.send(lc.cast_to(value, self.returned_type), kv.return_address)

			self.callback(f, drained, return_address=self.return_address)
			continue

		elif convention == CallingConvention.SOAK:
			s = self.create(soak, spool, request, flooding, soaking)

			def drained(value, kv):
				self.send(lc.cast_to(value, self.returned_type), kv.return_address)

			self.callback(s, drained, return_address=self.return_address)
			continue

		else:
			response = lc.Faulted('no such calling convention')
			self.send(response, return_address)
			continue

		self.send(lc.cast_to(response, table_type), return_address)

# Register with runtime.
lc.bind(server, api=(Xy,))

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(server)
