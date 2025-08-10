# test_publisher_machine.py
import layer_cake as lc

from test_api import *
from test_function import *

# A bare-bones, machine-based implementation of a published network service.
DEFAULT_NAME = 'acme'

class Publisher(lc.Point, lc.Stateless):
	def __init__(self, name: str=None):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.name = name or DEFAULT_NAME

def Publisher_Start(self, message):
	lc.publish(self, self.name)		# Register this object under the given name.

def Publisher_Xy(self, message):
	t = texture(self, x=message.x, y=message.y)
	m = lc.cast_to(t, table_type)
	self.reply(m)					# Respond to client.

def Publisher_Faulted(self, message):	# All faults routed here including
	self.complete(message)				# failure of publish().

def Publisher_Stop(self, message):
	self.complete(lc.Aborted())			# Leave all the housekeeping to the framework.

lc.bind(Publisher, (lc.Start, Xy, lc.Faulted, lc.Stop), entry_point=[Xy,])

if __name__ == '__main__':		# Process entry-point.
	lc.create(Publisher)
