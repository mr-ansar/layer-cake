# test_echo.py
import layer_cake as lc

def main(self, requested_ipp: lc.HostPort=None):
	requested_ipp = requested_ipp or lc.HostPort('127.0.0.1', 5010)

	self.console(requested_ipp=requested_ipp)

	# Establish the network listen.
	lc.listen(self, requested_ipp=requested_ipp)
	m, i = self.select(lc.Listening, lc.NotListening, lc.Stop)
	if i == 1:
		return m
	if i == 2:
		return lc.Aborted()

	# Errors, sessions and inbound client messages.
	while True:
		m, i = self.select(lc.NotListening,		# Listen failed.
			lc.Accepted, lc.Closed,				# Session notifications.
			lc.Stop,							# Intervention.
			lc.Unknown)							# An inbound message.

		if i == 0:				# Terminate with the fault.
			break
		elif i in (1, 2):		# Ignore.
			continue
		elif i == 3:			# Terminate as requested.
			m = lc.Aborted()
			break

		rt = type(self.received_type)
		self.console(typ=rt)
		if rt == lc.UserDefined:
			self.console(element=self.received_type.element)
		c = lc.cast_to(m, self.received_type)	# Send the message back over the connection.
		self.reply(c)

	return m

lc.bind(main, entry_point=(lc.Ack, lc.Enquiry))

if __name__ == '__main__':
	lc.create(main)
