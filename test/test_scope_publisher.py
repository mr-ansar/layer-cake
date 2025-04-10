# test_publisher.py
# Demonstrate the publish side of pub-sub networking.
# Call lc.publish() to declare a name within the directory namespace.
# Matching use of lc.subscribe() in a client process will result
# in a network transport between the processes and session
# notifications at each end, i.e. Delivered.
import layer_cake as lc

def publisher(self, name: str=None, scope: lc.ScopeOfDirectory=None):
	'''Establish a named service, wait for clients and their enquiries. Return nothing.'''
	name = name or 'acme'
	scope = scope or lc.ScopeOfDirectory.GROUP
	published = None

	# Declare the name for matching subscribers.
	lc.publish(self, name, scope=scope)

	m = self.input()
	if isinstance(m, lc.Published):			# Name registered with directory.
		published = m
		self.console(f'Published', published_id=published.published_id)

	elif isinstance(m, lc.NotPublished):	# Faulted.
		self.complete(m)

	# Now a part of the pub/sub framework. Wait for session notifications
	# and application messages.
	while True:
		m = self.input()
		# Start of a session.
		if isinstance(m, lc.Delivered):
			self.console(f'Delivered', route_id=m.route_id, subscribed_id=m.subscribed_id)
			continue

		# Subscriber has opened an exchange.
		elif isinstance(m, lc.Enquiry):
			self.reply(lc.Ack())			# Complete the exchange.

		# End of a session. Subscriber has cleared, process has terminated
		# or the network connection was lost.
		elif isinstance(m, lc.Dropped):
			self.console(f'Dropped', route_id=m.route_id, subscribed_id=m.subscribed_id)
			continue

		# Intervention, e.g. control-c or inter-process signaling.
		# Delete the name.
		elif isinstance(m, lc.Stop):
			lc.clear_published(self, published)
			break

	# Wait for confirmation.
	m = self.input()
	if not isinstance(m, lc.PublishedCleared):
		self.complete(m)
	self.complete(lc.Aborted())

# Register with runtime.
lc.bind(publisher)

# Process entry-point.
if __name__ == '__main__':
	lc.create(publisher)
