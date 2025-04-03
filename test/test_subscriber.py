# test_subscriber.py
# Demonstrate the subscribe side of pub-sub networking.
# Call lc.subscribe() to declare a search of the library namespace.
# Matching use of lc.publish() in a service process will result
# in a network transport between the processes and session
# notifications at each end, i.e. Available.
import layer_cake as lc

def subscriber(self, name: str=None):
	'''Open communications with a named service and exchange messages. Return nothing.'''
	name = name or 'abc'

	# Declare the search.
	lc.subscribe(self, name)

	while True:
		m = self.input()
		if isinstance(m, lc.Available):		# Session notificaton and initiate exchange.
			self.send(lc.Enquiry(), self.return_address)
		elif isinstance(m, lc.Ack):
			continue
		elif isinstance(m, lc.Dropped):		# End of session.
			continue
		elif isinstance(m, lc.Stop):		# Intervention.
			self.complete(lc.Aborted())

# Register with runtime.
lc.bind(subscriber)

# Optional process entry-point.
if __name__ == '__main__':
	lc.create(subscriber)
