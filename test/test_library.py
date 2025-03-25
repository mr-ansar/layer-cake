# test_library.py
import layer_cake as lc
from layer_cake.listen_connect import *

def main(self):
	# Errors, sessions and inbound client messages.
	while True:
		i, m, p = self.select(lc.Stop,			# Intervention.
			lc.Unknown)							# An inbound message.

		if i == 0:					# Terminate as requested.
			m = lc.Aborted()
			break

		c = lc.cast_to(m, p)		# Send the message back over the connection.
		self.reply(c)

	return m

lc.bind(main, api=(lc.Ack, lc.Enquiry))

if __name__ == '__main__':
	lc.create(main)
