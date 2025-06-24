# test_server_3.py
import layer_cake as lc
from test_api import Xy, table_type
from test_worker_3 import worker

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
SERVER_API = (Xy,)

def server(self, server_address: lc.HostPort=None):
	server_address = server_address or DEFAULT_ADDRESS

	# Open a network port for HTTP clients, e.g. curl.
	lc.listen(self, server_address, http_server=SERVER_API)
	m = self.input()
	if not isinstance(m, lc.Listening):
		return m

	# Start a request processor in a separate thread.
	worker_address = self.create(lc.ProcessObject, worker)

	# Run a live network service.
	while True:
		m = self.input()

		if isinstance(m, Xy):
			pass

		elif isinstance(m, lc.Returned):
			d = self.debrief()
			if isinstance(d, lc.OnReturned):
				d(self, m)
			continue

		elif isinstance(m, lc.Faulted):
			return m

		elif isinstance(m, lc.Stop):
			return lc.Aborted()

		else:
			continue

		# Callback for on_return.
		def respond(self, response, args):
			self.send(lc.cast_to(response, self.returned_type), args.return_address)

		a = self.create(lc.GetResponse, m, worker_address)
		self.on_return(a, respond, return_address=self.return_address)

lc.bind(server)

if __name__ == '__main__':
	lc.create(server)
