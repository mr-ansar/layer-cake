# test_server_1.py
import layer_cake as lc
from test_api import Xy

DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
SERVER_API = (Xy,)

def server(self, server_address: lc.HostPort=None):
	server_address = server_address or DEFAULT_ADDRESS

	lc.listen(self, server_address, http_server=SERVER_API)
	m = self.input()
	if not isinstance(m, lc.Listening):
		return m

	lc.subscribe(self, 'test-multihosting:worker-1')
	m = self.input()
	if not isinstance(m, lc.Subscribed):
		return m

	worker_spool = self.create(lc.ObjectSpool, None)

	while True:
		m = self.input()
		if isinstance(m, Xy):
			pass
		elif isinstance(m, lc.Returned):
			d = self.debrief()
			if isinstance(d, lc.OnReturned):
				d(self, m)
			continue
		elif isinstance(m, lc.Available):
			self.send(lc.JoinSpool(m.publisher_address), worker_spool)
			continue
		elif isinstance(m, lc.Dropped):
			self.send(lc.LeaveSpool(m.remote_address), worker_spool)
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

		a = self.create(lc.GetResponse, m, worker_spool)
		self.on_return(a, respond, return_address=self.return_address)

lc.bind(server)

if __name__ == '__main__':
	lc.create(server)
