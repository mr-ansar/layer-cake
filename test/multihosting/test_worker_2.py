# test_worker_2.py
import uuid
import layer_cake as lc
from test_api import Xy, table_type
from test_function_2 import texture

def worker(self):
	tag = uuid.uuid4()
	lc.publish(self, f'test-multihosting:worker-2:{tag}', scope=lc.ScopeOfDirectory.LAN)
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
