# test_library_machine.py
import layer_cake as lc

from test_api import *
from test_function import *

# A bare-bones, machine implementation
# of test_library.py.
class Library(lc.Threaded, lc.Stateless):
	def __init__(self):
		lc.Threaded.__init__(self)
		lc.Stateless.__init__(self)

def Library_Start(self, message):
	pass

def Library_Xy(self, message):
	table = texture(self, x=message.x, y=message.y)
	self.send(lc.cast_to(table, table_type), self.return_address)

def Library_Stop(self, message):
	self.complete(lc.Aborted())

lc.bind(Library, (lc.Start, Xy, lc.Stop), entry_point=[Xy,])

if __name__ == '__main__':
	lc.create(Library)
