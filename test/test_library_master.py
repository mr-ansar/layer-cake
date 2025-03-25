# test_echo.py
import layer_cake as lc
from layer_cake.listen_connect import *

import test_library

def main(self):
	echo = self.create(lc.ProcessObject, test_library.main)

	self.send(lc.Ack(), echo)
	i, m, p = self.select(lc.Ack, lc.Faulted, lc.Stop)
	assert isinstance(m, lc.Ack)

	self.send(lc.Stop(), echo)
	i, m, p = self.select(lc.Returned, lc.Faulted, lc.Stop)
	assert isinstance(m, lc.Returned)

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
