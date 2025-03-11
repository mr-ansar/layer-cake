# object_startup_test.py
import layer_cake as lc
import test_main

def main(self):
	t = lc.text_to_world('1963-03-26T02:24')
	a = self.create(lc.ProcessObject, test_main.main, b=32, c=99, t=t)
	i, m, t = self.select(lc.Returned, lc.Stop)
	if isinstance(m, lc.Returned):
		if m.created_type not in (lc.ProcessObject, test_main.main):
			return lc.Faulted(f'not the expected source type ({m.created_type})')
		return m.value					# Return type of main must match test_main.main.
	self.send(m, a)
	self.select(lc.Returned)
	return lc.Aborted()

lc.bind(main, return_type=lc.Any())

if __name__ == '__main__':
	lc.create(main)
