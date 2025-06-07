# test_server.py
import layer_cake as lc

from test_api import *
from test_function_b import texture


# A bare-bones implementation of a traditional network server that
# demonstrates the different function-calling options.
DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
SERVER_API = (Xy,)

def server(self, server_address: lc.HostPort=None):
	'''Establish a network listen and process API requests. Return nothing.'''

	server_address = server_address or DEFAULT_ADDRESS

	# Open a network port for HTTP clients, e.g. curl.
	lc.listen(self, server_address, api_server=SERVER_API)

	# Run a live network service.
	while True:
		m = self.input()

		if isinstance(m, Xy):					# Request from HTTP client.
			pass

		elif isinstance(m, lc.Returned):		# Child object terminated, e.g. thread.
			d = self.debrief()
			if isinstance(d, lc.OnReturned):	# Execute saved callback.
				d(self, m)
				continue

		elif isinstance(m, lc.NotListening):	# Fault.
			return m

		elif isinstance(m, lc.Stop):			# Terminate this service, e.g. control-c.
			return lc.Aborted()

		else:
			continue	# Ignore everything else.

		# Process the Xy request from one of the connected clients.
		convention = m.convention
		return_address = self.return_address

		# Callback for delayed async processing.
		def respond(self, value, args):
			self.send(lc.cast_to(value, self.returned_type), args.return_address)

		if convention == CallingConvention.CALL:
			response = texture(self, x=m.x, y=m.y)
			self.send(lc.cast_to(response, table_type), self.return_address)

		elif convention == CallingConvention.THREAD:
			a = self.create(texture, x=m.x, y=m.y)
			self.on_return(a, respond, return_address=return_address)


lc.bind(server)	# Register with the framework.


if __name__ == '__main__':	# Process entry-point.
	lc.create(server)
