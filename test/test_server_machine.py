# test_server_machine.py
import random
import layer_cake as lc

from test_api import *
from test_function import *
from test_library_machine import *


# A bare-bones, machine-based implementation of a traditional network server that
# demonstrates the different function-calling options.
DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)

class Server(lc.Point, lc.Stateless):
	def __init__(self, server_address: lc.HostPort=None, flooding: int=64, soaking: int=100):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.server_address = server_address or DEFAULT_ADDRESS
		self.flooding = flooding
		self.soaking = soaking

def Server_Start(self, message):
	lc.listen(self, self.server_address)
	self.library = self.create(lc.ProcessObject, Library, role_name='library')
	self.spool = self.create(lc.ProcessObjectSpool, Library, role_name='spool', process_count=32)

def Server_Xy(self, message):
	convention = message.convention
	return_address = self.return_address

	# Callback for the more complex operations.
	def respond(self, value, kv):
		m = lc.cast_to(value, self.returned_type)
		self.send(m, kv.return_address)

	# Demonstrate the selected behaviour.
	if convention == CallingConvention.CALL:
		t = texture(self, x=message.x, y=message.y)
		self.reply(lc.cast_to(t, table_type))

	elif convention == CallingConvention.THREAD:
		a = self.create(texture, x=message.x, y=message.y)
		self.callback(a, respond, return_address=return_address)

	elif convention == CallingConvention.PROCESS:
		a = self.create(lc.ProcessObject, texture, x=message.x, y=message.y)
		self.callback(a, respond, return_address=return_address)

	elif convention == CallingConvention.LIBRARY:
		a = self.create(lc.GetResponse, message, self.library)
		self.callback(a, respond, return_address=return_address)

	elif convention == CallingConvention.SPOOL:
		a = self.create(lc.GetResponse, message, self.spool)
		self.callback(a, respond, return_address=return_address)

	elif convention == CallingConvention.FLOOD:
		f = self.create(flood, self.spool, message, self.flooding)
		self.callback(f, respond, return_address=return_address)

	elif convention == CallingConvention.SOAK:
		s = self.create(soak, self.spool, message, self.flooding, self.soaking)
		self.callback(s, respond, return_address=return_address)
	
	else:
		self.complete(lc.Faulted('No such convention'))

def Server_Returned(self, message):
	d = self.debrief()
	if isinstance(d, lc.OnReturned):
		d(self, message)				# A callback.
		return
	self.complete(message)				# Library or spool has terminated.

def Server_Faulted(self, message):		# All faults routed here including
	self.complete(message)				# failure of listen().

def Server_Stop(self, message):
	self.complete(lc.Aborted())			# Leave all the housekeeping to the framework.

lc.bind(Server, (lc.Start, Xy, lc.Returned, lc.Faulted, lc.Stop), api=(Xy,))


# Supporting functions and async objects for the more
# complex operations.
random.seed()

def delay(period):
	'''Calculate a short break. Something random around the given length.'''
	cf = random.randrange(75, 125) / 100
	return period * cf

def flood(self, spool, request, flooding) -> list[list[float]]:
	'''Generate a burst of requests. Wait for related responses.'''
	for i in range(flooding):
		self.send(request, spool)

	for i in range(flooding):
		response = self.input()
		if isinstance(response, lc.Faulted):
			return response
		elif isinstance(response, lc.Stop):
			return lc.Aborted()

	return response

lc.bind(flood)

def soak(self, spool, request, flooding, soaking) -> list[list[float]]:
	# Repetitions of flood (i.e. above).
	for i in range(soaking):
		for j in range(flooding):
			self.send(request, spool)

		for j in range(flooding):
			response = self.input()
			if isinstance(response, lc.Faulted):
				return response
			elif isinstance(response, lc.Stop):
				return lc.Aborted()

		self.start(lc.T1, delay(2.0))
		b = self.input()
		if isinstance(b, lc.Faulted):
			return b
		if isinstance(b, lc.Stop):
			return lc.Aborted()

	return response

lc.bind(soak)

if __name__ == '__main__':	# Process entry-point.
	lc.create(Server)
