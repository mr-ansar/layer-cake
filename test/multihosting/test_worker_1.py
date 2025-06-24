# test_worker_1.py
import layer_cake as lc
from test_api import Xy, table_type
from test_function_1 import texture

def worker(self):
	lc.publish(self, 'test-multihosting:worker-1')
	m = self.input()
	if not isinstance(m, lc.Published):
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

		table = texture(x=m.x, y=m.y)
		self.send(lc.cast_to(table, table_type), self.return_address)

lc.bind(worker)

if __name__ == '__main__':
	lc.create(worker)
