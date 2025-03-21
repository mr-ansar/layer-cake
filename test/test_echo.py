# test_echo.py
import layer_cake.listen_connect as lc

def main(self, requested_ipp: lc.HostPort=None):
	requested_ipp = requested_ipp or lc.HostPort('127.0.0.1', 5010)

	self.console(requested_ipp=requested_ipp)

	# Establish the network listen.
	lc.listen(self, requested_ipp=requested_ipp)
	i, m, p = self.select(lc.Listening, lc.NotListening, lc.Stop)
	if i == 1:
		return m
	if i == 2:
		return lc.Aborted()

	# Errors, sessions and inbound client messages.
	while True:
		i, m, p = self.select(lc.NotListening,			# Listen failed.
			lc.Accepted, lc.Closed, lc.Abandoned,		# Session notifications.
			lc.Stop,									# Intervention.
			lc.Unknown)									# An inbound message.

		if i == 0:				# Terminate with the fault.
			break
		elif i in (1, 2, 3):	# Ignore.
			continue
		elif i == 4:			# Terminate as requested.
			m = lc.Aborted()
			break

		c = lc.cast_to(m, p)	# Send the message back over the connection.
		self.reply(c)

	return m

lc.bind(main)

if __name__ == '__main__':
	lc.create(main)
