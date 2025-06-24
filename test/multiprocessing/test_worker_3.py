# test_worker_3.py
import layer_cake as lc
from test_api import Xy, table_type
from test_function_3 import texture

def worker(self):
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

lc.bind(worker, api=(Xy,))

if __name__ == '__main__':
	lc.create(worker)
