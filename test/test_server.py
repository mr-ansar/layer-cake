# test_server.py
import random
import layer_cake as lc

from test_api import *
from test_function import *
from test_library import *


# A bare-bones implementation of a traditional network server that
# demonstrates the different function-calling options.
DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

def server(self, server_address: lc.HostPort=None, flooding: int=64, soaking: int=100):
	'''Establish a network listen and process API requests. Return nothing.'''
	server_address = server_address or DEFAULT_ADDRESS

	# Open a network port for inbound connections.
	lc.listen(self, server_address)
	m = self.input()

	if isinstance(m, lc.Listening):		# Good to go.
		pass
	elif isinstance(m, lc.Faulted):		# Something went wrong, e.g. address in use.
		return m
	elif isinstance(m, lc.Stop):		# Interrupted, i.e. control-c.
		return lc.Aborted()

	# Manage a private server, i.e. a library.
	lib = self.create(lc.ProcessObject, library, role_name='library')

	# Manage a job spool, i.e. a cluster of libraries.
	spool = self.create(lc.ProcessObjectSpool, library, role_name='spool', process_count=32)

	# Run a live network service. Framework notifications and
	# client requests.
	while True:
		m = self.input()

		if isinstance(m, (lc.Accepted, lc.Closed)):		# Clients coming and going.
			continue

		elif isinstance(m, lc.Returned):		# Child object terminated, e.g. flood, spool.
			d = self.debrief()
			if isinstance(d, lc.OnReturned):	# Execute a callback.
				d(m, self)
				continue
			return lc.Faulted('Support process terminated.')

		elif isinstance(m, lc.Faulted):
			return m

		elif isinstance(m, lc.Stop):
			return lc.Aborted()

		elif isinstance(m, Xy):
			pass

		else:
			return lc.Faulted(f'unexpected message {m}.')

		# Received an Xy request from client.
		request = m
		convention = m.convention
		return_address = self.return_address

		# Callback for the more complex operations.
		def respond(value, kv):
			self.send(lc.cast_to(value, self.returned_type), kv.return_address)

		# Demonstrate the selected behaviour.
		if convention == CallingConvention.CALL:
			response = texture(self, x=request.x, y=request.y)

		elif convention == CallingConvention.THREAD:
			self.create(texture, x=request.x, y=request.y)
			returned = self.input()
			response = returned.value_only()

		elif convention == CallingConvention.PROCESS:
			self.create(lc.ProcessObject, texture, x=request.x, y=request.y)
			returned = self.input()
			response = returned.value_only()

		elif convention == CallingConvention.LIBRARY:
			self.send(request, lib)
			response = self.input()

		elif convention == CallingConvention.SPOOL:
			self.send(request, spool)
			response = self.input()

		elif convention == CallingConvention.FLOOD:
			f = self.create(flood, spool, request, flooding)
			self.callback(f, respond, return_address=self.return_address)
			continue

		elif convention == CallingConvention.SOAK:
			s = self.create(soak, spool, request, flooding, soaking)
			self.callback(s, respond, return_address=self.return_address)
			continue

		else:
			response = lc.Faulted('No such calling convention')
			self.send(response, return_address)
			continue

		self.send(lc.cast_to(response, table_type), return_address)

lc.bind(server, api=(Xy,))	# Register with the framework.


# Supporting functions and async objects for the more
# complex operations.
random.seed()

def delay(period):
	'''Calculate a short break. Something random around the given length.'''
	cf = random.randrange(75, 125) / 100
	return period * cf

def flood(self, spool, request, flooding) -> list[list[float]]:
	'''Generate a burst of requests. Wait for related responses.'''
	for i in range(flooding):
		self.send(request, spool)

	for i in range(flooding):
		response = self.input()
		if isinstance(response, lc.Faulted):
			return response
		elif isinstance(response, lc.Stop):
			return lc.Aborted()

	return response

lc.bind(flood)

def soak(self, spool, request, flooding, soaking) -> list[list[float]]:
	# Repetitions of flood (i.e. above).
	for i in range(soaking):
		for j in range(flooding):
			self.send(request, spool)

		for j in range(flooding):
			response = self.input()
			if isinstance(response, lc.Faulted):
				return response
			elif isinstance(response, lc.Stop):
				return lc.Aborted()

		self.start(lc.T1, delay(2.0))
		b = self.input()
		if isinstance(b, lc.Faulted):
			return b
		if isinstance(b, lc.Stop):
			return lc.Aborted()

	return response

lc.bind(soak)


if __name__ == '__main__':	# Process entry-point.
	lc.create(server)
