# test_publisher.py
# Demonstrate the publish side of pub-sub networking.
# Call lc.publish() to declare a name within the library namespace.
# Matching use of lc.subscribe() in a client process will result
# in a network transport between the processes and session
# notifications at each end, i.e. Delivered.
import layer_cake as lc

def publisher(self, name: str=None, scope: lc.ScopeOfDirectory=None):
	'''Establish a named service, wait for clients and their enquiries. Return nothing.'''
	name = name or 'acme'
	scope = scope or lc.ScopeOfDirectory.WAN
	published = None

	# Declare the name for matching subscribers.
	lc.publish(self, name, scope=scope)

	while True:
		m = self.input()
		if isinstance(m, lc.Published):		# Name registered with directory.
			published = m
			self.console(f'Published', published_id=published.published_id)

		elif isinstance(m, lc.NotPublished):	# Faulted.
			self.complete(m)

		# Start of a session with a matching subscriber.
		# Expect an Enquiry to open an exchange.
		elif isinstance(m, lc.Delivered):
			self.console(f'Delivered', route_id=m.route_id, subscribed_id=m.subscribed_id)
			continue

		elif isinstance(m, lc.Enquiry):		# Opening.
			self.reply(lc.Ack())			# Complete the exchange.

		# End of a session. Subscriber has cleared, process has terminated
		# or the network connection was lost.
		elif isinstance(m, lc.Dropped):
			self.console(f'Dropped', route_id=m.route_id, subscribed_id=m.subscribed_id)
			continue

		# Intervention, e.g. control-c or inter-process signaling.
		# Delete the name and wait for confirmation.
		elif isinstance(m, lc.Stop):
			lc.clear_published(self, published)

		elif isinstance(m, lc.PublishedCleared):
			self.complete(lc.Aborted())

# Register with runtime.
lc.bind(publisher)

# Process entry-point.
if __name__ == '__main__':
	lc.create(publisher)
