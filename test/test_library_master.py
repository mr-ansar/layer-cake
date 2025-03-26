# test_echo.py
import layer_cake as lc
import test_library

def main(self):
	echo = self.create(lc.ProcessObject, test_library.main)		# Load the library process.

	self.send(lc.Ack(), echo)									# Request and
	i, m, p = self.select(lc.Ack, lc.Faulted, lc.Stop)			# response.
	assert isinstance(m, lc.Ack)

	i, m, p = self.select()			# response.
	return lc.Aborted()

	# Optional housekeeping.
	# self.send(lc.Stop(), echo)									# Unload the library.
	# i, m, p = self.select(lc.Returned, lc.Faulted, lc.Stop)		# Gone.
	# assert isinstance(m, lc.Returned)

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
