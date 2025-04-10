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

"""Definition of the fundamental async object.

Async objects are created and then send messages to each other. There are
also timers to implement, and automated logging. There is also assistance
for managing async scenarios.
"""

__docformat__ = 'restructuredtext'

import os
import inspect
from copy import deepcopy
import types
import typing
from collections import deque
from queue import Empty
from time import time
from .general_purpose import *
from .virtual_memory import *
from .convert_memory import *
from .message_memory import *
from .convert_signature import *
from .convert_type import *
from .virtual_runtime import *
from .point_runtime import *
from .running_routine import *
from .routine_point import *
from .object_space import *
from .message_pump import *


__all__ = [
	'VP',
	'SelectTimer',
	'Point',
	'T1', 'T2', 'T3', 'T4',
	'StartTimer',
	'CancelTimer',
	'PointLog',
	'OnReturned',
	'returned_object',
	'Threaded',
	'Channel',
	'Machine',
	'threaded_object',
	'object_dispatch',
	'no_ending',
	'halt',
]

# Point Runtime Addresses
# Initialized during startup or default
# to null, i.e. not available or no effect.
VP = Gas(log_address=NO_SUCH_ADDRESS,
	timer_address=NO_SUCH_ADDRESS,
	test_address=NO_SUCH_ADDRESS,
	circuit_address=NO_SUCH_ADDRESS,
	thread_classes={})

# Timing facility, i.e. Point.start().
class T1(object):
	"""Predeclared timer class.

	A class suitable for passing to Point.start(). The library
	provides the T1, T2, T3 and T4 timer classes for general use.
	"""
	pass

class T2(object): pass
class T3(object): pass
class T4(object): pass

bind_message(T1, copy_before_sending=False)
bind_message(T2, copy_before_sending=False)
bind_message(T3, copy_before_sending=False)
bind_message(T4, copy_before_sending=False)

class StartTimer(object):
	"""Message from point to clock service, requesting a timer."""
	def __init__(self, timer=None, seconds=1, repeating=False):
		self.timer = timer
		self.seconds = seconds
		self.repeating = repeating

class CancelTimer(object):
	"""Message from point to clock service, canceling a pending timer."""
	def __init__(self, timer=None):
		self.timer = timer

bind_message(StartTimer, copy_before_sending=False,
	timer=Type(),
	seconds=Float8(),
	repeating=Boolean(),
)
bind_message(CancelTimer, copy_before_sending=False, timer=Type())

# Logging facility, i.e. Point.log(), Point.console().
class PointLog(object):
	"""Object that records a moment in time and other details.

	:param stamp: the moment the log was created
	:type stamp: epoch float
	:param tag: an enumeration of the log level
	:type tag: a single-character string
	:param address: address of the async object
	:type address: tuple of int
	:param name: name of the class or function.
	:type name: str
	:param state: name of the current FSM state or None
	:type state: str
	:param text: free format text
	:type text: str
	"""
	def __init__(self, stamp=0.0, tag=None, address=None, name=None, state=None, text=None):
		self.stamp = stamp
		self.tag = tag
		self.address = address or NO_SUCH_ADDRESS
		self.name = name
		self.state = state
		self.text = text

bind_message(PointLog, copy_before_sending=False,
	message_trail=False, execution_trace=False,
	stamp=Float8(),
	tag=Enumeration(USER_TAG),
	address=Address(),
	name=Unicode(),
	state=Unicode(),
	text=Unicode(),
)

# Async unit test facility, i.e. Point.test()
class PointTest(object):
	"""Results of a Point.test().

	Captures the details of a check on runtime values.

	:param stamp: the moment the test was performed
	:type stamp: epoch float
	:param name: name of the class or function
	:type name: str
	:param condition: pass or fail
	:type condition: bool
	:param source: name of the module containing the test
	:type source: str
	:param line: line in the module
	:type line: int
	:param text: free format text
	:type text: str
	"""
	def __init__(self, stamp=None, name=None, condition=None, source=None, line=None, text=None):
		self.stamp = stamp
		self.name = name
		self.condition = condition
		self.source = source
		self.line = line
		self.text = text

bind_message(PointTest, copy_before_sending=False,
	message_trail=False, execution_trace=False,
	stamp=WorldTime(),
	name=Unicode(),
	condition=Boolean(),
	source=Unicode(),
	line=Integer8(),
	text=Unicode(),
)

def check_line():
	s = inspect.stack()[2]
	sf = s[1]	# Source file.
	ln = s[2]	# Line number.
	fn = s[3]	# Function name.
	if sf.find('tmp') == 1:
		_, sf = os.path.split(sf)
	if '<module>' in fn:
		fn = None
	return sf, ln, fn

# Low level control over behaviour of terminating
# object, i.e. some go quietly.
def returned_object(value, parent, address, object_type):
	send_a_message(Returned(value, object_type), parent, address)

# Automation of response to completion.
class OnReturned(object):
	"""Capture values needed for response to object completion.

	:param routine: type to be created
	:type routine: function or Point-based class
	:param args: positional parameters
	:type args: tuple
	:param kw: named parameters
	:type kw: dict
	"""
	def __init__(self, routine, args):
		self.routine = routine
		self.args = args

	def __call__(self, returned):
		return self.routine(returned.value, self.args)	# Make the call.

#
#
class Point(object):
	"""The essential async object.

	Methods of this class are the user entry-point for SDL primitives such
	as send() and start(). There are also methods associated with logging
	and child object management.
	"""
	def __init__(self):
		self.object_address = NO_SUCH_ADDRESS	# Identity of this object.
		self.queue_address = NO_SUCH_ADDRESS	# Where are messages processed.
		self.parent_address = NO_SUCH_ADDRESS	# Who created this object.
		self.to_address = NO_SUCH_ADDRESS		# Delivery address on current message.
		self.return_address = NO_SUCH_ADDRESS	# Who sent the current message.
		self.assigned_queue = None				# Parent queue for non-threaded machine.
		self.object_ending = None

		self.returned_type = None
		self.received_type = None
		self.current_state = None

		self.address_job = {}
		self.aborted_value = None

	def create(self, object_type, *args, object_ending=returned_object, **kw):
		"""Create a child instance of `object_type`. Return the address of the new object.

		:param object_type: async type to instantiate
		:type object_type: function or Point-based class
		:param args: arguments passed to the new object
		:type args: positional arguments tuple
		:param kw: arguments passed to the new object
		:type kw: name arguments dict
		:rtype: an ansar address or the actual object (e.g. Channel)
		"""
		return create_a_point(object_type, object_ending, self.object_address, args, kw)

	def send(self, m, to):
		"""Transfer a message to an address.

		Message delivery is not guaranteed and non-delivery is not
		notified. There are multiple reasons delivery can fail, e.g. the
		destination address no longer exists. Unless the reason is a
		fault within the sending machinery, failure to deliver is not
		considered an error. Refer to application logs for details on
		why a particular message failed to reach its intended
		destination.

		A copy of the message is taken for every actual transfer, i.e.
		by default remote objects always receive a copy of the message
		originally presented to ``send()``. Obviously this is behaviour
		motivated by the multi-threaded runtime context but where it
		is deemed unnecessary, copying can be disabled on a per-message-type
		basis. :func:`~.bind.bind_any` for more details.

		:param m: the message to be sent
		:type m: instance of a registered message
		:param to: the intended receiver of the message
		:type to: ansar address
		"""
		pf = self.__art__
		try:
			mf = getattr(m, '__art__')
		except AttributeError:
			mf = None
		if mf:
			xf = m.timer.__art__ if isinstance(m, (StartTimer, CancelTimer)) else mf
			if pf.message_trail and xf.message_trail:
				self.log(USER_TAG.SENT, 'Sent %s to <%08x>' % (mf.name, to[-1]))
			if mf.copy_before_sending:
				c = deepcopy(m)
				send_a_message(c, to, self.object_address)
				return
		send_a_message(m, to, self.object_address)

	def reply(self, m):
		"""Send a response to the sender of the current message.

		This is a shorthand for ``self.send(m, self.return_address)``. Reduces
		keystrokes and risk of typos.

		:param m: the message to be sent
		:type m: instance of a registered message
		"""
		self.send(m, self.return_address)

	def forward(self, m, to, return_address):
		"""Send a message to an address, as if it came from a 3rd party.

		Send a message but override the return address with the address of
		another arbitrary object. To the receiver the message appears to
		have come from the arbitrary object.

		Useful when building relationships between objects. This allows objects
		to "drop out" of 3-way conversations, leaving simpler and faster 2-way
		conversations behind.

		:param m: the message to send
		:type m: instance of a registered message
		:param to: the intended receiver of the message
		:type to: ansar address
		:param return_address: the other object
		:type return_address: ansar address
		"""
		pf = self.__art__
		try:
			mf = getattr(m, '__art__')
			xf = m.timer.__art__ if isinstance(m, (StartTimer, CancelTimer)) else mf
		except AttributeError:
			mf = None

		if mf:
			if pf.message_trail and xf.message_trail:
				self.log(USER_TAG.SENT, 'Forward %s to <%08x> (from <%08x>)' % (mf.name, to[-1], return_address[-1]))
			if mf.copy_before_sending:
				c = deepcopy(m)
				send_a_message(c, to, return_address)
				return
		send_a_message(m, to, return_address)

	def start(self, timer, seconds, repeating=False):
		"""Start the specified timer for this object.

		An instance of the timer class will be sent to this address after the
		given number of seconds. Any registered message can be used as a timer.
		Ansar provides the standard timers T1, T2, T3, and T4 for convenience
		and to reduce duplication.

		Timers are private to each async object and there is no limit to the
		number of pending timers an object may have. Starting a timer with the
		same class is not an error, the timeout for that timer is reset to the
		new number of seconds. It is also not an error to terminate an object
		with outstanding timers - they fall on the floor.

		It is difficult to make guarantees about the order that messages will
		arrive at an object. In the case of timers, its possible to receive
		the timeout after the sending of a cancellation. Async objects are best
		written to cope with every possible receive ordering.

		:param timer: the type of the object that will be sent back on timeout
		:type timer: a registered class
		:param seconds: time span before expiry
		:type seconds: float
		"""
		self.send(StartTimer(timer, seconds, repeating), VP.timer_address)

	def cancel(self, timer):
		"""Abort the specified timer for this object.

		Discard the pending timer. It is not an error to find that there is
		no such pending timer. The timeout can still be received after a
		cancellation.

		:param timer: the pending timer
		:type timer: a registered class
		"""
		self.send(CancelTimer(timer), VP.timer_address)

	def complete(self, value=None):
		"""Cause an immediate termination. The method never returns.

		:param value: value to be returned to parent.
		:type value: any
		"""
		value = self.aborted_value or value
		raise Completion(value)

	def assign(self, address, job=True):
		"""The specified child object is working on the given job.

		:param address: the async object
		:type address: ansar address
		:param job: what the child object is doing on behalf of this object
		:type job: any
		"""
		self.address_job[address] = job

	def working(self):
		"""Check if there are child objects still active. Returns the count."""
		return len(self.address_job)

	def progress(self, address=None):
		"""Find the job for the specified address. Return the job or None.

		:param address: the async object
		:type address: ansar address
		:rtype: any or None
		"""
		a = address or self.return_address
		try:
			j = self.address_job[a]
		except KeyError:
			return None
		return j

	def running(self):
		"""Yield a sequence of job, address tuples."""
		for k, v in self.address_job.items():
			yield v, k

	def abort(self, aborted_value=None):
		"""Initiate the termination protocol for all pending jobs. Return the count of."""
		self.aborted_value = aborted_value
		for _, a in self.running():
			self.send(Stop(), a)
		n = len(self.address_job)
		return n

	def debrief(self, address=None):
		"""Find the job associated with the address. Return the job.

		If no address is provided the current return address is used.
		If a match is found the record is removed, decrementing the
		number of active jobs.

		:param address: the async object
		:type address: ansar address
		:rtype: any or None
		"""
		a = address or self.return_address
		c = self.address_job.pop(a, None)
		return c

	def callback(self, a, f, **kw):
		c = OnReturned(f, Gas(**kw))
		self.assign(a, c)

	def continuation(self, a, f, g):
		c = OnReturned(f, g)
		self.assign(a, c)

	def a_kv(self, a, kv):
		if len(a) > 0:
			note = ' '.join(a)
			if len(kv) > 0:
				eq = [f'{k}={v}'for k, v in kv.items()]
				t = ','.join(eq)
				text = f'{note} ({t})'
			else:
				text = note
		elif len(kv) > 0:
			eq = [f'{k}={v}'for k, v in kv.items()]
			text = ','.join(eq)
		else:
			text = None
		return text

	def log(self, tag, text):
		"""Generate a PointLog object at the specified level.

		This an internal function that should rarely be used directly
		by an application. Use debug(), trace(), etc instead.

		Forms a standard logging object and sends it to the logging
		service within the ansar runtime.

		:param tag: one of the logging enumerations
		:type tag: USER_LOG
		:param text: the message to log
		:type text: str
		"""
		e = PointLog()
		e.stamp = time()
		e.tag = tag
		e.address = self.object_address
		e.name = self.__art__.name
		# Hack-ish implementation.
		# Should be common base and derived impl's.
		if self.current_state is None:
			e.state = None
		else:
			e.state = self.current_state.__name__

		e.text = text
		send_a_message(e, VP.log_address, self.object_address)

	def pass_fail(self, condition, source, line, text):
		p = PointTest()
		p.stamp = world_now()
		p.name = self.__art__.name

		p.condition = condition
		p.source = source
		p.line = line

		encoded = text.encode('utf-8')
		decoded = encoded.decode('ascii', 'backslashreplace')
		p.text = decoded
		send_a_message(p, VP.test_address, self.object_address)

	def debug(self, *a, **kv):
		"""Generate a log at level DEBUG.

		:param a: the message to log
		:type a: tuple of positional arguments
		"""
		if self.__art__.user_logs.value > USER_LOG.DEBUG.value:
			return
		text = self.a_kv(a, kv)
		if text:
			self.log(USER_LOG.DEBUG, text)

	def trace(self, *a, **kv):
		"""Generate a log at level TRACE.

		:param a: the message to log
		:type a: tuple of positional arguments
		"""
		if self.__art__.user_logs.value > USER_LOG.TRACE.value:
			return
		text = self.a_kv(a, kv)
		if text:
			self.log(USER_TAG.TRACE, text)

	def console(self, *a, **kv):
		"""Generate a log at level CONSOLE.

		:param a: the message to log
		:type a: tuple of positional arguments
		"""
		if self.__art__.user_logs.value > USER_LOG.CONSOLE.value:
			return

		text = self.a_kv(a, kv)
		if text:
			self.log(USER_TAG.CONSOLE, text)

	def sample(self, **kv):
		"""Generate a log at level TRACE.

		A quick way to put runtime values in the logs. Also the basis
		for generating values for statistical analysis. Refer to
		ansar logging documentation.

		:param kv: the named arguments
		:type a: dict
		"""
		a = ()
		text = self.a_kv(a, kv)
		if text:
			self.log(USER_TAG.SAMPLE, text)

	def warning(self, *a, **kv):
		"""Generate a log at level WARNING.

		:param a: the message to log
		:type a: tuple of positional arguments
		"""
		if self.__art__.user_logs.value > USER_LOG.WARNING.value:
			return
		text = self.a_kv(a, kv)
		if text:
			self.log(USER_TAG.WARNING, text)

	def fault(self, *a, **kv):
		"""Generate a log at level FAULT.

		:param a: the message to log
		:type a: tuple of positional arguments
		"""
		if self.__art__.user_logs.value > USER_LOG.FAULT.value:
			return
		text = self.a_kv(a, kv)
		if text:
			self.log(USER_TAG.FAULT, text)

	def test(self, condition, note):
		"""Generate a log at level WARNING, dependent on the condition.

		A ``PointTest`` is also sent to an internal collection point, for
		later recovery, e.g. by test applications. This is sent for both
		pass and fail.

		:param condition: pass or fail
		:type condition: bool
		:param note: a simple string of text
		:type note: str
		"""
		s, l, _ = check_line()
		b = bool(condition)
		self.pass_fail(b, s, l, note)
		if b:
			return condition
		self.log(USER_TAG.CHECK, f'{note} ({s}:{l})')
		return condition

def halt(address):
	"""Mark the object at the specified address as halted.

	:param address: an async object
	:type address: ansar address
	"""
	with OpenAddress(address) as c:
		if isinstance(c, Channel):
			c.halted = True

# Augmented input process, deriving straight
# from SDL.
MAXIMUM_REPLAYS = 8

class Player(object):
	"""Base for objects intending to operate message buffering with replay."""

	def __init__(self):
		"""Construct an instance of Player."""
		self.pending = deque()		# Recently saved.
		self.replaying = deque()	# Active replay
		self.get_frame = None

	def pull(self):
		"""Get the next replay message or a fresh message from the queue."""
		if self.replaying:
			mtr = self.replaying.popleft()
		else:
			mtr = self.get()
			if len(mtr) == 3:
				mtr.append(0)
			if self.pending:
				# Only replay those pending on the same address.
				other = deque()
				for p in self.pending:
					if p[1][-1] == mtr[1][-1]:
						self.replaying.append(p)
					else:
						other.append(p)
				self.pending = other
		self.get_frame = mtr
		return mtr[0], mtr[1], mtr[2]

	def pushback(self, m):
		"""Retain the [message, to, return] triplet for later replay."""
		mtr = self.get_frame
		if id(m) != id(mtr[0]):
			return
		mtr[3] += 1
		if mtr[3] < MAXIMUM_REPLAYS:
			self.pending.append(mtr)

	def flush(self):
		try:
			while True:
				self.message_queue.get_nowait()
		except Empty:
			pass
		self.replaying.clear()
		self.pending.clear()

# Dedicated timer for managed messaging.
class SelectTimer(object):
	"""Timer for managed input."""
	pass

class Other(object):
	"""Capture un-declared input."""
	def __init__(self, value=None):
		self.value = value

bind_message(SelectTimer)
bind_message(Other, value=Any())

class Dispatching(Player):
	"""Provides input mechanism for any machine with its own queue."""

	def __init__(self):
		Player.__init__(self)
		"""Construct an instance of Dispatching."""

	def input(self):
		"""Get a message from replay buffer or fresh from queue. Return message triplet."""
		m, t, r = self.pull()
		self.to_address = t
		self.return_address = r
		m, p, a = cast_back(m)
		if a:
			if self.__art__.execution_trace and a.execution_trace:
				self.log(USER_TAG.RECEIVED, "Received %s from <%08x>" % (a.name, r[-1]))
		self.received_type = p
		return m

	def undo(self, m):
		"""Retain the [message, to, return] triplet, using values saved during input."""
		self.pushback(m)

class Buffering(Player):
	"""Base for any object intending to perform sophisticated I/O, i.e. channels and routines."""

	def __init__(self):
		Player.__init__(self)
		"""Construct an instance of Buffering."""

	def save(self, m):
		"""Retain the [message, to, return] triplet, using values saved during input.

		:param m: message to be saved
		:type m: message object
		"""
		self.pushback(m)

	def input(self):
		"""Get the next message while transparently buffering.

		:rtype: message object
		"""
		m, t, r = self.pull()
		self.to_address = t
		self.return_address = r
		m, p, a = cast_back(m)
		if a:
			if self.__art__.execution_trace and a.execution_trace:
				self.log(USER_TAG.RECEIVED, "Received %s from <%08x>" % (a.name, r[-1]))
		self.received_type = p
		return m

	def select(self, *matching, saving=None, seconds=0):
		"""Expect one of the listed messages, with optional saving and timeout.

		:param matching: message types to be accepted
		:type matching: the positional arguments tuple
		:param saving: message types to be deferred
		:type saving: tuple
		:param seconds: waiting period
		:type seconds: float
		:rtype: message object
		"""
		if len(matching) == 0:
			if seconds:
				matching += (Unknown, SelectTimer)
			else:
				matching = (Unknown,)
			matching = select_list_adhoc(*matching)
		elif isinstance(matching[0], SelectTable):
			matching = matching[0]
		else:
			matching = select_list_adhoc(*matching)

		if saving is None:
			pass
		elif isinstance(saving, SelectTable):
			pass
		elif isinstance(saving, tuple):
			saving = select_list_adhoc(*saving)
		else:
			saving = select_list_adhoc(saving)

		if seconds:
			matching += (SelectTimer,)
			self.start(SelectTimer, seconds)

		qf = self.__art__
		while True:
			mtr = self.pull()
			m = mtr[0]
			self.to_address = mtr[1]
			self.return_address = mtr[2]
			a = self.return_address[-1]

			r = matching.find(m)
			if r is not None:
				if seconds:
					self.cancel(SelectTimer)
				if qf.execution_trace:
					t = portable_to_tag(r[2])
					self.log(USER_TAG.RECEIVED, f'Received "{t}" from <{a}>')
				self.received_type = r[2]
				return r[1], r[0]

			if saving and saving.find(m):
				self.save(m)
				continue

			if qf.execution_trace:
				if r:
					t = portable_to_tag(r[2])
				else:
					t = type(m)
				self.log(USER_TAG.RECEIVED, f'Dropped "{t}" from <{a}>')

	def ask(self, q, r, a, saving=None, seconds=None):
		"""Query for a response while allowing reordering, with optional timer.


		:param q: query to be sent
		:type q: registered message
		:param r: response types to be detected and returned
		:type r: tuple
		:param a: async object to be queried
		:type a: ansar address
		:param saving: response types to be detected and buffered
		:type saving: tuple
		:param seconds: waiting period
		:type seconds: float
		:rtype: message object
		"""
		self.send(q, a)
		if not isinstance(r, tuple):
			return self.select(r, saving=saving, seconds=seconds)
		return self.select(*r, saving=saving, seconds=seconds)

	def stop(self, a, r=(Returned,), saving=None, seconds=None):
		"""Request the termination of an object.

		:param a: async object to be queried
		:type a: ansar address
		:param r: response types to be detected and returned
		:type r: tuple
		:param saving: response types to be detected and buffered
		:type saving: tuple
		:param seconds: waiting period
		:type seconds: float
		:rtype: message object
		"""
		return self.ask(Stop(), r, a, saving=saving, seconds=seconds)

class Threaded(Pump, Point, Dispatching):
	"""Base class for async machines that require dedicated threads.

	:param blocking: block on queue full
	:type blocking: bool
	:param maximum_size: number of pending messages
	:type maximum_size: int
	"""
	def __init__(self, blocking=False, maximum_size=PEAK_BEFORE_DROPPED):
		Pump.__init__(self, blocking=blocking, maximum_size=maximum_size)
		Point.__init__(self)
		Dispatching.__init__(self)

class Channel(Pump, Point, Buffering):
	"""A sync object.

	Used by sync code to access async features. An instance of a channel
	is created by ansar on behalf of each "function" object, i.e. each instance
	of a function object gets a thread and a channel. The thread accesses
	async services through it private channel object. Also used by the
	OpenChannel context object.
	"""
	def __init__(self):
		Pump.__init__(self)
		Point.__init__(self)
		Buffering.__init__(self)
		self.halted = False

class Machine(object):
	"""Base for machines, providing for presentation of messages and save."""

	def __init__(self):
		"""Construct an instance of Machine."""

	def save(self, m):
		"""Retain the [message, to, return] triplet, i.e. call the parent queue."""
		self.assigned_queue.undo(m)

	def received(self, queue, message, return_address):
		"""A placeholder for erroneous use. Raises a ``PointConstructionError`` exception."""
		raise PointConstructionError('Message received by virtual base. Use Stateless or StateMachine.')

# Standard routines for running the
# message handlers for async class instances.
def threaded_object(queue):
	"""The thread object silently allocated to machines with dedicated threads."""
	a = queue.object_address
	queue.received(queue, Start(), queue.parent_address)
	while True:
		mtr = queue.pull()
		m = mtr[0]
		t = mtr[1]
		r = mtr[2]
		if t[-1] == a[-1]:
			queue.to_address = t
			queue.return_address = r
			queue.received(queue, m, r)

	# Termination occurs by raising of Completion exception
	# from within the received() method. The exception is
	# caught by the running_in_thread() function.

def object_dispatch(queue):
	"""The thread object that executes transitions for one or more machines."""
	a = queue.object_address
	while True:
		mtr = queue.pull()
		m = mtr[0]
		t = mtr[1]
		r = mtr[2]
		if t[-1] == a[-1]:
			if isinstance(m, Stop):	 # [1]
				return True
			continue

		p = find_object(t)
		if not p:
			continue

		try:
			p.to_address = t
			p.return_address = r
			p.received(queue, m, r)	 # [2]
			continue
		# Necessary replication of exceptions in
		# running_in_thread.
		except KeyboardInterrupt:
			s = 'unexpected keyboard interrrupt'
			p.fault(s)
			value = Faulted('object compromised', s)
		except SystemExit:
			s = 'unexpected system exit'
			p.fault(s)
			value = Faulted('object compromised', s)
		except Completion as c:
			value = c.value
		except Exception as e:
			s = str(e)
			s = f'unhandled exception ({s})'
			p.fault(s)
			value = Faulted('object faulted', s)
		except:
			s = 'unhandled opaque exception'
			p.fault(s)
			value = Faulted('object faulted', s)

		# Convert the exception to a message.
		if p.__art__.lifecycle:
			p.log(USER_TAG.DESTROYED, 'Destroyed')
		s = p.parent_address

		return_type = p.__art__.return_type
		if return_type is None:
			pass
		elif isinstance(return_type, Any):
			pass
		elif isinstance(return_type, Portable):
			if not hasattr(value, '__art__'):
				value = (value, return_type)
		else:
			value = Faulted(f'unexpected return type for machine "{p.__class__.__name__}"')

		ending = p.object_ending
		destroy_an_object(t)
		ending(value, s, t, type(p))

	# Termination of child objects occurs by raising of the
	# Completion exception from within the received() call [2].
	# The exception is caught and the termination protocol
	# concluded. Termination of the dispatcher [1] is the same
	# as for any object, by sending a Stop(). The running_in_thread
	# function concludes the protocol.

def no_ending(value, parent, address, object_type):
	pass

# Object creation.
#
def create_a_point(object_type, object_ending, parent_address, args, kw):
	if isinstance(object_type, types.FunctionType):
		return custom_routine(object_type, object_ending, parent_address, args, kw)
	elif issubclass(object_type, Point):
		if issubclass(object_type, Machine):
			if issubclass(object_type, Threaded):
				return object_and_thread(object_type, object_ending, parent_address, args, kw)
			else:
				return object_only(object_type, object_ending, parent_address, args, kw)
		if issubclass(object_type, Channel):
			return sync_object(object_type, parent_address, args, kw)
		else:
			raise PointConstructionError('Cannot create Point %r; not a machine or sync.' % (object_type,))
	else:
		raise PointConstructionError('Cannot create %r; not a function or Point.' % (object_type,))

def custom_routine(routine, object_ending, parent_address, args, kw):
	"""Create an async object around the supplied function.

	:param routine: the function to run within its own thread
	:type routine: function
	:param parent_address: object that called create()
	:type parent_address: ansar address
	:param args: positional args to be forwarded to the function
	:type args: tuple
	:param kw: key-value args to be forwarded to the function
	:type kw: dict
	:rtype: ansar address
	"""
	# A rude little adjustment to force the object over
	# to the input() system intended for dispatching.
	if routine == object_dispatch:
		object_type = Threaded   # Input and save.
	else:
		object_type = Channel	 # Input, select, ask and save.
	a, q = create_an_object(object_type, object_ending, parent_address, (), {})
	# Overlay the class runtime with the function runtime, i.e. at instance level.
	q.__art__ = routine.__art__
	if q.__art__.lifecycle:
		q.log(USER_TAG.CREATED, 'Created by <%08x>' % (parent_address[-1],))
	start_a_thread(q, routine, args, kw)
	return a

def object_and_thread(object_type, object_ending, parent_address, args, kw):
	"""Create an async object and thread around the supplied type.

	:param object_type: async object expecting its own thread
	:type object_type: registered class
	:param parent_address: object that called create()
	:type parent_address: ansar address
	:param args: positional args to be forwarded to the function
	:type args: tuple
	:param kw: key-value args to be forwarded to the function
	:type kw: dict
	:rtype: ansar address
	"""
	a, q = create_an_object(object_type, object_ending, parent_address, args, kw)
	# Assume the class context, i.e. a derived application class.
	if q.__art__.lifecycle:
		q.log(USER_TAG.CREATED, 'Created by <%08x>' % (parent_address[-1],))
	start_a_thread(q, threaded_object, (), {})
	# The threaded_object routine provides the Start message.
	return a

def object_only(object_type, object_ending, parent_address, args, kw):
	"""Create an async object of the supplied type.

	:param object_type: async object
	:type object_type: registered class
	:param parent_address: object that called create()
	:type parent_address: ansar address
	:param args: positional args to be forwarded to the function
	:type args: tuple
	:param kw: key-value args to be forwarded to the function
	:type kw: dict
	:rtype: ansar address
	"""
	a, q = create_an_object(object_type, object_ending, parent_address, args, kw)
	# Assume the object context.
	if q.__art__.lifecycle:
		q.log(USER_TAG.CREATED, 'Created by <%08x>' % (parent_address[-1],))
	send_a_message(Start(), a, parent_address)
	return a

def sync_object(object_type, parent_address, args, kw):
	"""Create a synchronous object in the midst of async objects.

	:param object_type: async object
	:type object_type: registered class
	:param parent_address: object that called create()
	:type parent_address: ansar address
	:param args: positional args to be forwarded to the function
	:type args: tuple
	:param kw: key-value args to be forwarded to the function
	:type kw: dict
	:rtype: async object
	"""
	a, q = create_an_object(object_type, no_ending, parent_address, args, kw)
	# Assume the object context
	if q.__art__.lifecycle:
		q.log(USER_TAG.CREATED, 'Created by <%08x>' % (parent_address[-1],))
	return q
