# test_publisher.py
# Demonstrate the publish side of pub-sub networking.
# Call lc.publish() to declare a name within the library namespace.
# Matching use of lc.subscribe() in a client process will result
# in a network transport between the processes and session
# notifications at each end, i.e. Delivered.
import layer_cake as lc

def publisher(self, name: str=None, scope: lc.ScopeOfDirectory=None):
	'''Establish a named service, wait for clients and their enquiries. Return nothing.'''
	name = name or 'abc'
	scope = scope or lc.ScopeOfDirectory.WAN
	published = None

	# Declare the service.
	lc.publish(self, name, scope=scope)

	while True:
		m = self.input()
		if isinstance(m, lc.Published):	# Search registered with directory.
			published = m
			self.console(f'Published', published_id=published.published_id)

		elif isinstance(m, lc.NotPublished):	# Search rejected.
			self.complete(m)

		elif isinstance(m, lc.Delivered):
			self.console(f'Delivered', route_id=m.route_id)
			continue
		elif isinstance(m, lc.Dropped):	
			self.console(f'Dropped', route_id=m.route_id)
			continue
		if isinstance(m, lc.Enquiry):		# Client-service exchange.
			self.reply(lc.Ack())

		elif isinstance(m, lc.Stop):		# Intervention.
			lc.clear_published(self, published)

		elif isinstance(m, lc.PublishedCleared):
			self.complete(lc.Aborted())

# Register with runtime.
lc.bind(publisher)

# Process entry-point.
if __name__ == '__main__':
	lc.create(publisher)
