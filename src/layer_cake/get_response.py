# Author: Scott Woods <scott.18.ansar@gmail.com>
# MIT License
#
# Copyright (c) 2025 Scott Woods
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Concurrency and support of same.

Objects and classes that allow for the construction of
complex distributed operations.
"""
__docformat__ = 'restructuredtext'

from .message_memory import *
from .convert_type import *
from .virtual_memory import *
from .virtual_point import *
from .virtual_runtime import *
from .point_runtime import *
from .point_machine import *
from .bind_type import *

__all__ = [
	'CreateFrame',
	'GetResponse',
	'Delay',
	'Concurrently',
	'Sequentially',
]

#
class CreateFrame(object):
	"""Capture values needed for async object creation.

	:param object_type: type to be created
	:type object_type: :ref:`object type<lc-object-type>`
	:param args: positional args to be passed on creation
	:param kw: named values to be passed on creation
	"""
	def __init__(self, object_type, *args, **kw):
		self.object_type = object_type
		self.args = args
		self.kw = kw

#
class GetResponse(Point, Stateless):
	"""
	Delegated request-response.

	Send the request to the given address and expect a
	response. Pass the response back as the return value
	for this object.

	:param request: message to be sent
	:type request: :ref:`message<lc-message>`
	:param server_address: where to send the message
	:param seconds: acceptable delay
	"""
	def __init__(self, request, server_address: Address, seconds: float=None):
		Point.__init__(self)
		Stateless.__init__(self)
		self.request = request
		self.server_address = server_address
		self.seconds = seconds

def GetResponse_Start(self, message):
	self.send(self.request, self.server_address)	# Request.
	if self.seconds is not None:
		self.start(T1, self.seconds)

def GetResponse_T1(self, message):						# Too slow.
	self.complete(TimedOut(message))

def GetResponse_Stop(self, message):					# Interruption.
	self.complete(Aborted())

def GetResponse_Unknown(self, message):	# Assumed to be response. Use as completion.
	m = cast_to(message, self.received_type)
	self.complete(m)

GET_RESPONSE_DISPATCH = [
	Start,
	T1,
	Stop,
	Unknown,
]

bind_stateless(GetResponse, GET_RESPONSE_DISPATCH, thread='get-response', return_type=Any())

#
class Delay(Point, Stateless):
	"""Object that does nothing for the specified number of seconds."""
	def __init__(self, seconds=None):
		Point.__init__(self)
		Stateless.__init__(self)
		self.seconds = seconds

def Delay_Start(self, message):
	self.start(T1, self.seconds)

def Delay_T1(self, message):						# Too slow.
	self.complete(TimedOut(message))

def Delay_Stop(self, message):					# Interruption.
	self.complete(Aborted())

DELAY_DISPATCH = [
	Start,
	T1,
	Stop,
]

bind_stateless(Delay, DELAY_DISPATCH, thread='delay')

#
class Concurrently(Point, Stateless):
	"""
	Delegated, multi-way request-response.

	Manage one or more concurrent requests. Terminate on completion of full set, or	a timer.
	Accepts a mixed tuple, i.e. either request-address pairs or :class:`~.CreateFrame` objects.

	:param get: a list of request-address pairs or frames
	:type get: tuple
	:param seconds: acceptable delay
	"""
	def __init__(self, *get, seconds: float=None):
		Point.__init__(self)
		Stateless.__init__(self)
		self.get = get		# List of object descriptions.
		self.count = len(get)		# Save for countdown.
		self.seconds = seconds
		self.orderly = [None] * self.count	# Prepare the completion list.

def Concurrently_Start(self, message):
	if self.count < 1:
		self.complete(self.orderly)		# Nothing to do.

	def collate(self, response, kv):			# Place the completion in its proper slot.
		i = kv.i
		self.orderly[i] = cast_to(response, self.returned_type)
		self.count -= 1
		if self.count < 1:
			self.complete(self.orderly)

	# Create an object for each slot. Allow full object spec
	# or the request-address tuple.
	for i, p in enumerate(self.get):
		if isinstance(p, CreateFrame):
			a = self.create(p.object_type, *p.args,	**p.kw)
		elif isinstance(p, tuple) and len(p) == 2:
			r, s = p
			a = self.create(GetResponse, r, s)		# Provide the object for simple request-response exchange.
		else:
			self.complete(Faulted(f'unexpected frame/request [{i}]'))

		self.on_return(a, collate, i=i)

	if self.seconds is not None:
		self.start(T1, self.seconds)

def Concurrently_T1(self, message):
	self.abort(TimedOut(message))

def Concurrently_Stop(self, message):
	self.abort(Aborted())

def Concurrently_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(self, message)
		return
	
	self.complete(Faulted(f'unexpected get completion'))

CONCURRENTLY_DISPATCH = [
	Start,
	Returned,
	T1,
	Stop,
]

bind_stateless(Concurrently, CONCURRENTLY_DISPATCH, thread='concurrently', return_type=VectorOf(Any()))


#
class Sequentially(Point, Stateless):
	"""Object that iterates multiple objects and produces list of completions."""
	def __init__(self, *get, seconds=None):
		Point.__init__(self)
		Stateless.__init__(self)
		self.get = get
		self.pointer = iter(self.get)
		self.seconds = seconds
		self.orderly = []

	def next_step(self):
		try:
			p = next(self.pointer)
		except StopIteration:
			self.complete(self.orderly)

		if isinstance(p, CreateFrame):
			a = self.create(p.object_type, *p.args,	**p.kw)
		elif isinstance(p, tuple) and len(p) == 2:
			r, s = p
			a = self.create(GetResponse, r, s)		# Provide the object for simple request-response exchange.
		else:
			i = len(self.orderly)
			self.complete(Faulted(f'unexpected sequence item [{i}]'))
		return a

def Sequentially_Start(self, message):
	def step(self, value, kv):
		if isinstance(value, Faulted):
			self.complete(value)
		self.orderly.append(value)

		a = self.next_step()
		self.on_return(a, step)

	if self.seconds is not None:
		self.start(T1, self.seconds)

	a = self.next_step()
	self.on_return(a, step)

def Sequentially_T1(self, message):
	self.abort(TimedOut(message))

def Sequentially_Stop(self, message):
	self.abort(Aborted())

def Sequentially_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(self, message)
		return

	self.complete(Faulted(f'unexpected sequence completion'))

SEQUENTIALLY_DISPATCH = [
	Start,
	T1,
	Stop,
	Returned,
]

bind_stateless(Sequentially, SEQUENTIALLY_DISPATCH, thread='sequentially')
