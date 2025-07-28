# object_startup_test.py
import layer_cake as lc
import test_main

def main(self):
	t = lc.text_to_world('1963-03-26T02:24')
	a = self.create(lc.ProcessObject, test_main.main, b=32, c=99, t=t)
	m, i = self.select(lc.Returned, lc.Stop)
	if isinstance(m, lc.Returned):
		return m.message					# Return type of main must match test_main.main.
	self.send(m, a)
	self.select(lc.Returned)
	return lc.Aborted()

lc.bind(main, return_type=lc.Any())

if __name__ == '__main__':
	lc.create(main)
