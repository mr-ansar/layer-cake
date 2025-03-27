# test_client.py
# Demonstrate the client side of traditional
# client-server networking.

import layer_cake as lc

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

def client(self, server_address: lc.HostPort=None):
	'''Establish a network connection and respond to API messages. Return nothing.'''
	server_address = server_address or DEFAULT_ADDRESS

	# Initiate a network connection.
	lc.connect(self, server_address)
	i, m, p = self.select(lc.Connected, lc.Faulted, lc.Stop)
	if i == 1:
		return m
	elif i == 2:
		return lc.Aborted()
	server = self.return_address	# Remember where Connected came from.

	# A few request/response exchanges.
	self.send(lc.Ack(), server)
	m = self.input()
	assert isinstance(m, lc.Nak)

	self.send(lc.Nak(), server)
	m = self.input()
	assert isinstance(m, lc.Ack)

	# Explicit close of the connection.
	self.send(lc.Close(), server)
	i, m, p = self.select(lc.Closed, lc.Faulted, lc.Stop)
	if i == 1:
		return m
	elif i == 2:
		return lc.Aborted()
	return None

# Register with runtime.
lc.bind(client, api=(lc.Ack, lc.Nak))

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(client)
