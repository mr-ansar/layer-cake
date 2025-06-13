# Author: Scott Woods <scott.18.ansar@gmail.com>
# MIT License
#
# Copyright (c) 2017-2023 Scott Woods
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

"""Management of a pool of threads.

.
"""
__docformat__ = 'restructuredtext'

from collections import deque

from .general_purpose import *
from .virtual_memory import *
from .convert_memory import *
from .message_memory import *
from .convert_signature import *
from .convert_type import *
from .virtual_runtime import *
from .virtual_point import *
from .point_runtime import *
from .routine_point import *
from .virtual_codec import *
from .point_machine import *
from .bind_type import *
from .object_collector import *
from .object_directory import *
from .get_response import *

__all__ = [
	'ObjectSpool',
]

#
#
class INITIAL: pass
class PENDING: pass
class EXECUTING: pass
class CLEARING: pass
class SPOOLING: pass

SPOOL_SPAN = 32

class ObjectSpool(Point, StateMachine):
	"""An async proxy object that starts and manages one or more standard sub-process.

	:param name: name of the executable file
	:type name: str
	"""
	def __init__(self, object_type, *args, object_count=8, size_of_spool=512, responsiveness=None, **settings):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.object_type = object_type
		self.args = args
		self.object_count = object_count
		self.size_of_spool = size_of_spool
		self.responsiveness = responsiveness
		self.settings = settings

		self.idle_object = deque()
		self.pending_request = deque()
		self.span = deque()
		self.total_span = 0.0
		self.average = 0.0
		self.boundary_1 = 0.0
		self.boundary_2 = 0.0
		self.shard = 0

	def submit_request(self, message, forward_response, return_address):
		if self.responsiveness is None:
			pass
		elif self.average < self.boundary_1:
			pass
		else:
			self.shard += 1
			divisor = 4 if self.average < self.boundary_2 else 10
			if self.shard % divisor == 0:
				self.send(Overloaded('Reduced responsiveness from spool thread'), return_address)
				return

		idle = self.idle_object.popleft()
		r = self.create(GetResponse, message, idle)
		self.on_return(r, forward_response, idle=idle, return_address=return_address, started=clock_now())

def ObjectSpool_INITIAL_Start(self, message):
	if self.responsiveness is not None:
		self.boundary_1 = self.responsiveness % 0.75
		self.boundary_2 = self.responsiveness % 0.9

	pc = self.object_count
	sos = self.size_of_spool
	r = self.responsiveness

	if pc < 1 or (sos is not None and sos < 1) or (r is not None and r < 0.5):
		self.complete(Faulted(f'cannot start the spool with the given parameters (count={pc}, size={sos}, responsiveness={r})'))
	
	for i in range(pc):
		a = self.create(self.object_type, *self.args, **self.settings)
		self.assign(a, i)
		self.idle_object.append(a)

	return SPOOLING

def ObjectSpool_SPOOLING_Unknown(self, message):
	m = cast_to(message, self.received_type)
	if not self.idle_object:
		if self.size_of_spool is None or len(self.pending_request) < self.size_of_spool:
			self.pending_request.append((m, self.return_address))
			return SPOOLING
		request = portable_to_signature(self.received_type)
		self.reply(Overloaded('Process resources busy and spool full', request=request))
		return SPOOLING

	def forward_response(self, value, kv):
		# Completion of a request/responsesequence.
		# Record the idle process.
		self.idle_object.append(kv.idle)

		# Update the performance metric.
		span = clock_now() - kv.started
		self.total_span += span
		self.span.append(span)
		while len(self.span) > SPOOL_SPAN:
			s = self.span.popleft()
			self.total_span -= s
		self.average = self.total_span / len(self.span)

		# Deliver reponse to the original client.
		m = cast_to(value, self.returned_type)
		self.send(m, kv.return_address)
		if not self.pending_request:
			return
		message, return_address = self.pending_request.popleft()

		# There is a request-to-go and an available process.
		self.submit_request(message, forward_response, return_address)
		return

	# There is a request-to-go and an available process.
	self.submit_request(m, forward_response, self.return_address)
	return SPOOLING

def ObjectSpool_SPOOLING_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(self, message)
		return SPOOLING
	self.trace(f'Spool process termination', returned_value=message.value)

	seconds = spread_out(32.0)

	def restart(self, value, args):
		i = args.i
		a = self.create(self.object_type, *self.args, **self.settings)
		self.assign(a, i)
		self.idle_object.append(a)

	# Run a no-op with the desired timeout.
	a = self.create(GetResponse, Enquiry(), NO_SUCH_ADDRESS, seconds=seconds)
	self.on_return(a, restart, i=d)
	return SPOOLING

def ObjectSpool_SPOOLING_Stop(self, message):
	self.abort()
	return CLEARING

def ObjectSpool_CLEARING_Returned(self, message):
	d = self.debrief()
	if self.working():
		return CLEARING
	self.complete(Aborted())

OBJECT_SPOOL_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	SPOOLING: (
		(Unknown, Returned, Stop,),
		()
	),
	CLEARING: (
		(Returned,),
		()
	),
}

bind(ObjectSpool, OBJECT_SPOOL_DISPATCH, thread='object-spool')
