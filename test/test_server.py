# test_server.py
import layer_cake as lc

from test_api import *
from test_function import *
from test_library import *


# A bare-bones implementation of a traditional network server that
# demonstrates the different function-calling options.
DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
SERVER_API = (Xy,)

def server(self, server_address: lc.HostPort=None, flooding: int=64, soaking: int=100):
	'''Establish a network listen and process API requests. Return nothing.'''
	server_address = server_address or DEFAULT_ADDRESS

	# 1. Open a network port for HTTP clients, e.g. curl,
	# 2. manage a private server, i.e. a loadable library, and
	# 3. manage a job spool, i.e. a cluster of libraries.
	lc.listen(self, server_address, api_server=SERVER_API)
	lib = self.create(lc.ProcessObject, library, role_name='library')
	spool = self.create(lc.ProcessObjectSpool, library, role_name='spool', process_count=2)

	# Run a live network service, library and spool.
	while True:
		m = self.input()

		if isinstance(m, Xy):					# Request from HTTP client.
			pass

		elif isinstance(m, lc.Returned):		# Child object terminated, e.g. thread, process, ...
			d = self.debrief()
			if isinstance(d, lc.OnReturned):	# Execute saved callback.
				d(self, m)
				continue
			return lc.Faulted('Supporting process terminated.')

		elif isinstance(m, (lc.Accepted, lc.Closed)):		# HTTP clients coming and going.
			continue

		elif isinstance(m, lc.Listening):		# Bound to the port.
			continue

		elif isinstance(m, lc.Faulted):			# Any fault, including NotListening.
			return m

		elif isinstance(m, lc.Stop):
			return lc.Aborted()

		else:
			return lc.Faulted(f'unexpected message {m}')

		# Received an Xy request from one of the connected clients.
		request = m
		convention = m.convention
		return_address = self.return_address

		# Callback for the async variants.
		def respond(self, value, kv):
			self.send(lc.cast_to(value, self.returned_type), kv.return_address)

		# Demonstrate the selected behaviour.
		if convention == CallingConvention.CALL:
			response = texture(self, x=request.x, y=request.y)

		elif convention == CallingConvention.THREAD:
			a = self.create(texture, x=request.x, y=request.y)
			self.on_return(a, respond, return_address=return_address)
			continue

		elif convention == CallingConvention.PROCESS:
			a = self.create(lc.ProcessObject, texture, x=request.x, y=request.y)
			self.on_return(a, respond, return_address=return_address)
			continue

		elif convention == CallingConvention.LIBRARY:
			a = self.create(lc.GetResponse, request, lib)
			self.on_return(a, respond, return_address=return_address)
			continue

		elif convention == CallingConvention.SPOOL:
			a = self.create(lc.GetResponse, request, spool)
			self.on_return(a, respond, return_address=return_address)
			continue

		elif convention == CallingConvention.FLOOD:
			a = self.create(flood, spool, request, flooding)
			self.on_return(a, respond, return_address=return_address)
			continue

		elif convention == CallingConvention.SOAK:
			a = self.create(soak, spool, request, flooding, soaking)
			self.on_return(a, respond, return_address=return_address)
			continue

		else:
			response = lc.Faulted('No such calling convention')
			self.send(response, return_address)
			continue

		self.send(lc.cast_to(response, table_type), return_address)

lc.bind(server, api=(Xy,))	# Register with the framework.

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

		self.start(lc.T1, lc.spread_out(2.0))
		b = self.input()
		if isinstance(b, lc.Faulted):
			return b
		if isinstance(b, lc.Stop):
			return lc.Aborted()

	return response

lc.bind(soak)


if __name__ == '__main__':	# Process entry-point.
	lc.create(server)
