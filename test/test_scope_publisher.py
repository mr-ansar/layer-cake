# test_publisher.py
import layer_cake as lc

from test_api import *
from test_function import *

# A bare-bones implementation of a published network service.
DEFAULT_NAME = 'acme'

def publisher(self, name: str=None, scope: lc.ScopeOfDirectory=None):
	'''Establish a named service, wait for clients and their enquiries. Return nothing.'''
	name = name or DEFAULT_NAME
	scope = scope or lc.ScopeOfDirectory.GROUP

	lc.publish(self, name, scope=scope)		# Register this object under the given name.

	m = self.input()
	if isinstance(m, lc.Published):		# Name registered with directory.
		pass

	elif isinstance(m, lc.Faulted):		# Any fault, e.g. NotPublished.
		self.complete(m)

	# Run a live directory service. Framework notifications and
	# client requests.
	while True:
		m = self.input()
		if isinstance(m, (lc.Delivered, lc.Dropped)):	# Subscribers coming and going.
			continue

		elif isinstance(m, Xy):
			t = texture(self, x=m.x, y=m.y)
			m = lc.cast_to(t, table_type)
			self.reply(m)					# Respond to client.

		elif isinstance(m, lc.Stop):
			self.complete(lc.Aborted())

lc.bind(publisher)				# Register with framework.

if __name__ == '__main__':		# Process entry-point.
	lc.create(publisher)
