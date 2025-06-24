# test_server_1.py
import layer_cake as lc
from test_api import Xy, table_type
from test_function_1 import texture

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
SERVER_API = (Xy,)

def server(self, server_address: lc.HostPort=None):
	server_address = server_address or DEFAULT_ADDRESS

	lc.listen(self, server_address, http_server=SERVER_API)
	m = self.input()
	if not isinstance(m, lc.Listening):
		return m

	while True:
		m = self.input()
		if isinstance(m, Xy):
			pass
		elif isinstance(m, lc.Faulted):
			return m
		elif isinstance(m, lc.Stop):
			return lc.Aborted()
		else:
			continue

		client_address = self.return_address
		self.create(lc.ProcessObject, texture, x=m.x, y=m.y)
		m = self.input()
		response = m.value

		self.send(lc.cast_to(response, self.received_type), client_address)

lc.bind(server)

if __name__ == '__main__':
	lc.create(server)
