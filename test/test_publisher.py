# test_publisher.py
# Demonstrate the publish side of pub-sub networking.
# Call lc.publish() to declare a name within the library namespace.
# Matching use of lc.subscribe() in a client process will result
# in a network transport between the processes and session
# notifications at each end, i.e. Delivered.
import layer_cake as lc

def publisher(self, name: str=None):
	'''Establish a named service, wait for clients and their enquiries. Return nothing.'''
	name = name or 'abc'
	published = None

	# Declare the service.
	lc.publish(self, name)

	while True:
		m = self.input()
		if isinstance(m, lc.Published):	# Search registered with directory.
			published = m
		elif isinstance(m, (lc.Delivered, lc.Dropped)):	# Session notifications.
			continue
		if isinstance(m, lc.Enquiry):		# Client-service exchange.
			self.reply(lc.Ack())
		elif isinstance(m, lc.Stop):		# Intervention.
			#self.stop_publish(published)
			self.complete(lc.Aborted())

# Register with runtime.
lc.bind(publisher)

# Process entry-point.
if __name__ == '__main__':
	lc.create(publisher)
