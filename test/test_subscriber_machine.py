# test_subscriber.py
import layer_cake as lc

from test_api import *

# A bare-bones implementation of a client subscribing to a network service.
DEFAULT_SEARCH = 'acme'

class Subscriber(lc.Point, lc.Stateless):
	def __init__(self, search: str=None, seconds: float=None, enduring: bool=False):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.search = search or DEFAULT_SEARCH
		self.seconds = seconds
		self.enduring = enduring

def Subscriber_Start(self, message):
	lc.subscribe(self, self.search)		# Connect this object with the named object.
	if self.seconds is not None:
		self.start(lc.T1, 5.0)			# Expect resolution with a few seconds.

def Subscriber_Available(self, message):
	self.send(Xy(x=2, y=2), self.return_address)

def Subscriber_list_list_float(self, message):
	if self.enduring:
		return
	self.complete(message)

def Subscriber_T1(self, message):
	self.complete(lc.TimedOut(message))

def Subscriber_Faulted(self, message):		# All faults routed here including
	self.complete(message)					# failure of subscribe().

def Subscriber_Stop(self, message):
	self.complete(lc.Aborted())			# Leave all the housekeeping to the framework.

lc.bind(Subscriber, (lc.Start, lc.Available, table_type, lc.T1, lc.Faulted, lc.Stop), return_type=table_type)


if __name__ == '__main__':		# Process entry-point.
	lc.create(Subscriber)
