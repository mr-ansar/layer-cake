# test_library.py
import layer_cake as lc
from layer_cake.listen_connect import *

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

def server(self, server_address: lc.HostPort=None):
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
			bool,							# API.
		)

		if i == 0:					# Terminate with the error.
			return m
		elif i == 1:				# Terminate as requested.
			return lc.Aborted()

		if m == True:
			self.reply(lc.Ack())
		else:
			self.reply(lc.Nak())

lc.bind(server, api=(bool,))

if __name__ == '__main__':
	lc.create(server)
