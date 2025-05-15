# test_server.py
import layer_cake as lc

# A bare-bones implementation of a traditional network server that
# demonstrates the different function-calling options.

def thing(self, publish_as, subscribe_to, seconds=None):
	lc.publish(self, publish_as, scope=lc.ScopeOfDirectory.PROCESS)
	lc.subscribe(self, subscribe_to, scope=lc.ScopeOfDirectory.PROCESS)

	if seconds:
		self.start(lc.T1, seconds)

	published, i = self.select(lc.Published, saving=lc.Subscribed)	# Published...
	subscribed, i = self.select(lc.Subscribed, saving=lc.Published)

	while True:
		m = self.input()
		if not isinstance(m, (lc.Available, lc.Delivered, lc.Dropped)):
			break

	lc.clear_published(self, published)
	self.input()							# PublishedCleared

	lc.clear_subscribed(self, subscribed)
	self.input()							# SubscribedCleared

	return None

lc.bind(thing)

def abc(self, server_address: lc.HostPort=None, flooding: int=64, soaking: int=100):
	a = self.create(thing, "a", "c")
	b = self.create(thing, "b", "a", seconds=5.0)
	c = self.create(thing, "c", "b")

	self.assign(a, 0)
	self.assign(b, 1)
	self.assign(c, 2)

	m = self.input()
	while True:
		if isinstance(m, lc.Stop):
			self.abort()

		elif isinstance(m, lc.Returned):
			self.debrief()
			m = self.input()
			continue

		else:
			continue

		while self.working():
			self.input()
			self.debrief()

		return None
		
	return None

lc.bind(abc)	# Register with the framework.

if __name__ == '__main__':	# Process entry-point.
	lc.create(abc)
