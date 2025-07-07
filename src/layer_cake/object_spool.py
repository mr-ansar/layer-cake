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
from .process_object import *
from .get_response import *

__all__ = [
	'JoinSpool',
	'LeaveSpool',
	'ObjectSpool',
]

#
#
class JoinSpool(object):
	def __init__(self, worker_address: Address=None, role_name: str=None):
		self.worker_address = worker_address
		self.role_name = role_name

class LeaveSpool(object):
	def __init__(self, worker_address: Address=None, role_name: str=None):
		self.worker_address = worker_address
		self.role_name = role_name

bind(JoinSpool)
bind(LeaveSpool)

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
	def __init__(self, object_type, *args, role_name=None, object_count=8, size_of_queue=None, responsiveness=None, busy_fraction=10, stand_down=30.0, **settings):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.object_type = object_type
		self.args = args
		self.role_name = role_name
		self.object_count = object_count
		self.size_of_queue = size_of_queue
		self.responsiveness = responsiveness
		self.busy_fraction = busy_fraction
		self.stand_down = stand_down
		self.settings = settings

		self.idle_object = deque()
		self.pending_request = deque()
		self.forgetten_object = set()
		self.span = deque()
		self.total_span = 0.0
		self.average = 0.0
		self.shard = 0

	def submit_request(self, message, forward_response, return_address, presented):
		if self.responsiveness is None:
			pass
		elif self.average < self.responsiveness:
			pass
		else:
			self.shard += 1
			if self.shard % self.busy_fraction:
				self.send(Busy(f'message rejected by spool (average response time {self.average:.2f})'), return_address)
				return

		idle = self.idle_object.popleft()
		r = self.create(GetResponse, message, idle)
		self.on_return(r, forward_response, idle=idle, return_address=return_address, started=presented)

def ObjectSpool_INITIAL_Start(self, message):
	oc = self.object_count
	sos = self.size_of_queue
	r = self.responsiveness
	sd = self.stand_down

	if oc < 1 or (sos is not None and sos < 1) or (r is not None and r < 0.5) or (sd is not None and sd < 2.0):
		self.complete(Faulted(f'unexpected parameters (count={oc}, size={sos}, responsiveness={r}), stand_down={sd})'))

	if self.object_type is None:
		return SPOOLING

	role_name = self.role_name

	for i in range(oc):
		if self.object_type == ProcessObject:
			if not role_name:
				role_name = 'spool-{i}'
			r = role_name.format(i=i)
			a = self.create(self.object_type, *self.args, role_name=r, **self.settings)
		else:
			r = i
			a = self.create(self.object_type, *self.args, **self.settings)
		self.assign(a, r)
		self.idle_object.append(a)

	return SPOOLING

def forward_response(self, value, kv):
	# Completion of a request/responsesequence.
	# Record the idle process.
	forgetten_object = True
	try:
		self.forgetten_object.remove(kv.idle)
	except KeyError:
		forgetten_object = False
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
	if forgetten_object:
		return
	if not self.pending_request:
		return
	message, return_address, presented = self.pending_request.popleft()

	# There is a request-to-go and an available process.
	self.submit_request(message, forward_response, return_address, presented)

def ObjectSpool_SPOOLING_JoinSpool(self, message):
	self.idle_object.append(message.worker_address)
	if not self.pending_request:
		return SPOOLING
	message, return_address, presented = self.pending_request.popleft()

	# There is a request-to-go and an available process.
	self.submit_request(message, forward_response, return_address, presented)
	return SPOOLING

def ObjectSpool_SPOOLING_LeaveSpool(self, message):
	a = message.worker_address
	try:
		self.idle_object.remove(a)
	except ValueError:
		self.forgetten_object.add(a)

	# WHAT ABOUT ACTIVE GETRESPONSE!!!
	return SPOOLING

def ObjectSpool_SPOOLING_Unknown(self, message):
	m = cast_to(message, self.received_type)
	t = clock_now()
	if not self.idle_object:
		len_pending = len(self.pending_request)
		if self.size_of_queue is None or len_pending < self.size_of_queue:
			self.pending_request.append((m, self.return_address, t))
			return SPOOLING
		self.reply(Overloaded(f'message rejected by spool (overloaded, {len_pending} pending)'))
		return SPOOLING

	# There is a request-to-go and an available process.
	self.submit_request(m, forward_response, self.return_address, t)
	return SPOOLING

def ObjectSpool_SPOOLING_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(self, message)
		return SPOOLING

	if self.object_type is None:
		return SPOOLING

	self.trace(f'Spool process termination', returned_value=message.value)

	stand_down = self.stand_down
	if stand_down is None:
		self.abort()
		return CLEARING
	seconds = spread_out(stand_down)

	def restart(self, value, args):
		role_name = args.role_name
		if self.role_name:
			a = self.create(self.object_type, *self.args, role_name=role_name, **self.settings)
		else:
			a = self.create(self.object_type, *self.args, **self.settings)
		self.assign(a, role_name)
		self.idle_object.append(a)

	# Run a no-op with the desired timeout.
	a = self.create(GetResponse, Enquiry(), NO_SUCH_ADDRESS, seconds=seconds)
	self.on_return(a, restart, role_name=d)
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
		(JoinSpool, LeaveSpool, Unknown, Returned, Stop),
		()
	),
	CLEARING: (
		(Returned,),
		()
	),
}

bind(ObjectSpool, OBJECT_SPOOL_DISPATCH, thread='object-spool')
