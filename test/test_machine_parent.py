# object_startup_test.py
import layer_cake as lc
import test_main

class Main(lc.Point, lc.Stateless):
	def __init__(self):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.temperature = 0
		self.timeout = 0

def Main_Start(self, message):
	t = lc.text_to_world('1963-03-26T02:24')
	a = self.create(lc.Process, test_main.main, b=32, c=99, t=t)

	def test_main_complete(value, _):
		self.complete(value)

	self.begin(a, test_main_complete)

def Main_Completed(self, message):
	d = self.debrief()
	if isinstance(d, lc.OnCompleted):
		d(message)

def Main_Stop(self, message):
	self.abort()

lc.bind(Main, dispatch=(lc.Start, lc.Completed, lc.Stop), return_type=lc.Any())

if __name__ == '__main__':
	lc.create(Main)
