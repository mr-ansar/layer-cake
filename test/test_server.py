# test_server.py
# Demonstrate the server side of traditional
# client-server networking.

import layer_cake as lc

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)


def server(self, server_address: lc.HostPort=None):
	'''Establish a network listen and process API requests. Return nothing.'''
	server_address = server_address or DEFAULT_ADDRESS

	# Open a network port for inbound connections.
	lc.listen(self, server_address)
	i, m, p = self.select(lc.Listening, lc.Faulted, lc.Stop)
	if i == 1:
		return m				# Something went wrong, e.g. address in use.
	elif i == 2:
		return lc.Aborted()		# Interrupted, i.e. control-c.

	while True:
		i, m, p = self.select(lc.Faulted,	# Something went wrong.
			lc.Accepted,					# New connection.
			lc.Closed, lc.Abandoned,		# End of connection.
			lc.Stop,						# Intervention.
			lc.Ack,							# API.
			lc.Nak							# ..
		)

		if i == 0:					# Terminate with the error.
			return m
		elif i in (1, 2, 3):		# New client or lost existing. Ignore.
			continue
		elif i == 4:				# Terminate as requested.
			return lc.Aborted()
		elif i == 5:				# Client sent an Ack.
			self.reply(lc.Nak())
		elif i == 6:				# Client sent a Nak.
			self.reply(lc.Ack())

# Register with runtime.
lc.bind(server, api=(lc.Ack, lc.Nak))

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(server)
