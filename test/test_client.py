# test_client.py
# Demonstrate the client side of traditional
# client-server networking.
from enum import Enum
import layer_cake as lc
from test_api import *

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

def client(self, server_address: lc.HostPort=None, convention: CallingConvention=None, x: int=1, y: int=1):
	'''Make a connection, send a request and expect a response. Return a table of floats.'''

	server_address = server_address or DEFAULT_ADDRESS
	convention = convention or DEFAULT_CONVENTION

	# Initiate a network connection.
	lc.connect(self, server_address)
	m, i = self.select(lc.Connected, lc.Faulted, lc.Stop)

	if isinstance(m, lc.Faulted):	# No connection.
		return m
	elif isinstance(m, lc.Stop):	# As advised - abort.
		return lc.Aborted()
	server = self.return_address	# Remember where Connected came from.

	self.send(Xy(x=x, y=y, convention=convention), server)
	response = self.input()

	# Explicit close of the connection.
	self.send(lc.Close(), server)
	m, i = self.select(lc.Closed, lc.Faulted, lc.Stop)
	if isinstance(m, lc.Closed):
		pass
	elif isinstance(m, lc.Faulted):
		return m
	elif isinstance(m, lc.Stop):
		return lc.Aborted()

	return response

# Register with runtime.
lc.bind(client, return_type=table_type)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(client)
