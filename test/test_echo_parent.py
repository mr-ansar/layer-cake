# test_echo.py
import layer_cake as lc
from layer_cake.listen_connect import *

import test_echo

def main(self, requested_ipp: lc.HostPort=None):
	requested_ipp = requested_ipp or lc.HostPort('127.0.0.1', 5010)

	self.console(requested_ipp=requested_ipp)

	echo = self.create(lc.ProcessObject, test_echo.main)

	self.start(lc.T1, 2.0)
	m, i = self.select(lc.T1, lc.Faulted, lc.Stop)

	connect(self, requested_ipp=lc.HostPort('127.0.0.1', 5010))
	m, i = self.select(Connected, lc.Faulted, lc.Stop)
	assert isinstance(m, Connected)
	server = self.return_address

	self.send(lc.Ack(), server)
	m, i = self.select(lc.Ack, lc.Faulted, lc.Stop)
	assert isinstance(m, lc.Ack)

	self.start(lc.T1, 5.0)
	self.select()

	self.send(Close(), server)
	m, i = self.select(Closed, lc.Faulted, lc.Stop)
	assert isinstance(m, Closed)

	self.send(lc.Stop(), echo)
	m, i = self.select(lc.Returned, lc.Faulted, lc.Stop)
	assert isinstance(m, lc.Returned)

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
