# test_library.py
import layer_cake as lc
import test_api
import test_function

def library(self):
	while True:
		m = self.input()

		if isinstance(m, lc.Faulted):
			return m
		elif isinstance(m, lc.Stop):
			return lc.Aborted()

		table = test_function.function(self, x=m.x, y=m.y)
		self.send(lc.cast_to(table, test_api.table_type), self.return_address)

lc.bind(library, api=(test_api.Xy,))

if __name__ == '__main__':
	lc.create(library)
