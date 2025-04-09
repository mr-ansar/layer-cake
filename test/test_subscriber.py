# test_subscriber.py
# Demonstrate the subscribe side of pub-sub networking.
# Call lc.subscribe() to declare a search of the library namespace.
# Matching use of lc.publish() in a service process will result
# in a network transport between the processes and session
# notifications at each end, i.e. Available.
import layer_cake as lc

def subscriber(self, search: str=None, scope: lc.ScopeOfDirectory=None):
	'''Open communications with a named service and exchange messages. Return nothing.'''
	search = search or 'acme'
	scope = scope or lc.ScopeOfDirectory.WAN
	subscribed = None

	# Declare the search for the matching publish.
	lc.subscribe(self, search, scope=scope)

	while True:
		m = self.input()
		if isinstance(m, lc.Subscribed):	# Search registered with directory.
			subscribed = m
			self.console(f'Subscribed', subscribed_id=subscribed.subscribed_id)

		elif isinstance(m, lc.NotSubscribed):	# Faulted.
			self.complete(m)

		# Start of a session with a matching publisher.
		# Send an Enquiry to open an exchange.
		elif isinstance(m, lc.Available):
			self.console(f'Available', route_id=m.route_id, published_id=m.published_id)

			self.send(lc.Enquiry(), self.return_address)

		elif isinstance(m, lc.Ack):		# Completed handshake.
			continue

		# End of a session. Publisher has cleared, process has terminated
		# or the network connection was lost.
		elif isinstance(m, lc.Dropped):
			self.console(f'Dropped', route_id=m.route_id, published_id=m.published_id)
			continue

		# Intervention, e.g. control-c or inter-process signaling.
		# Delete the search and wait for confirmation.
		elif isinstance(m, lc.Stop):
			lc.clear_subscribed(self, subscribed)	# Start a teardown.

		elif isinstance(m, lc.SubscribedCleared):	# Completed teardown.
			self.complete(lc.Aborted())

# Register with runtime.
lc.bind(subscriber)

# Process entry-point.
if __name__ == '__main__':
	lc.create(subscriber)
