# test_server.py
# Demonstrate the server side of traditional
# client-server networking.

import layer_cake as lc
from layer_cake.listen_connect import *

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

def server(self, server_address: lc.HostPort=None):
	'''Establish a network listen and process API requests. Return nothing.'''
	server_address = server_address or DEFAULT_ADDRESS

	listen(self, server_address)
	i, m, p = self.select(Listening, lc.Faulted, lc.Stop)
	if i == 1:
		return m
	elif i == 2:
		return lc.Aborted()

	while True:
		i, m, p = self.select(lc.Faulted,	# Something went wrong.
			lc.Stop,						# Intervention.
			lc.Ack,							# API.
			lc.Nak,							# ..
		)

		if i == 0:					# Terminate with the error.
			return m
		elif i == 1:				# Terminate as requested.
			return lc.Aborted()
		elif i == 2:				# Client sent an Ack.
			self.reply(lc.Nak())
		elif i == 3:				# Client sent a Nak.
			self.reply(lc.Ack())

# Register with runtime.
lc.bind(server, api=(lc.Ack, lc.Nak))

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(server)
