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

"""Machines send messages and dispatch received machines to functions.

Purest async objects. Capable of sharing a thread.
"""
__docformat__ = 'restructuredtext'

import types
import re
import sys

from .virtual_runtime import *
from .point_runtime import *
from .virtual_point import *
from .message_memory import *

__all__ = [
	'Stateless',
	'StateMachine',
	'bind_stateless',
	'bind_statemachine',
	'DEFAULT',
]

class DEFAULT: pass

# Find the state and message embedded within a function name.
state_message = re.compile('(?P<state>[A-Z][A-Z0-9]*(_[A-Z0-9]+)*)_(?P<message>[A-Z][A-Za-z0-9]*)')


class Stateless(Machine):
	"""Base for simple machines that maintain no formal state.

	Messages are received by an assigned thread and dispatched to
	handlers according to the type of the received message.
	"""
	def __init__(self):
		Machine.__init__(self)

	def received_old(self, queue, message, return_address):
		"""Dispatch message to the appropriate handler.

		:parm queue: instance of a Queue-based async object
		:type queue: a Queue-based async class
		:parm message: the received massage
		:type message: instance of a registered class
		:parm return_address: origin of the message
		:type return_address: object address
		:rtype: none
		"""
		pf = self.__art__
		mf = message.__art__	# Could go straight to __class__.

		shift = pf.value
		try:
			k = message.__class__
			f = shift[k]
		except KeyError:
			# Obvious dispatch failed. Provide a
			# default clause.
			try:
				k = Unknown
				f = shift[k]
			except KeyError:
				if pf.execution_trace and mf.execution_trace:
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>' % (mf.name, return_address[-1]))
				return

		if pf.execution_trace and mf.execution_trace:
			self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>' % (mf.name, return_address[-1]))
		f(self, message)
		self.previous_message = message

	def received(self, queue, message, return_address):
		"""Dispatch message to the appropriate handler.

		:parm queue: instance of a Queue-based async object
		:type queue: a Queue-based async class
		:parm message: the received massage
		:type message: instance of a registered class
		:parm return_address: origin of the message
		:type return_address: object address
		:rtype: none
		"""
		pf = self.__art__
		mf = message.__art__	# Could go straight to __class__.
		mc = message.__class__

		shift = pf.value
		def transition():
			f = shift.get(mc, None)
			if f:
				return f

			for c, f in shift.items():
				if isinstance(message, c):
					return f

			return shift.get(Unknown, None)

		t = transition()
		if t is None:
			if pf.execution_trace and mf.execution_trace:
				if isinstance(message, Faulted):
					f = str(message)
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>, %s' % (mf.name, return_address[-1], f))
				else:
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>' % (mf.name, return_address[-1]))
			return

		if pf.execution_trace and mf.execution_trace:
			if isinstance(message, Faulted):
				f = str(message)
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>, %s' % (mf.name, return_address[-1], f))
			else:
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>' % (mf.name, return_address[-1]))

		t(self, message)
		self.previous_message = message

class StateMachine(Machine):
	"""Base for machines that maintain a formal state.

	Messages are received by an assigned thread and dispatched to
	handlers according to the current state and the type of the
	received message.

	:param initial: Start state for all instances of derived class
	:type initial: class
	"""
	def __init__(self, initial):
		Machine.__init__(self)
		self.current_state = initial

	def received(self, queue, message, return_address):
		"""Dispatch message to the appropriate handler.

		:parm queue: instance of a Queue-based async object
		:type queue: a Queue-based async class
		:parm message: the received massage
		:type message: instance of a registered class
		:parm return_address: origin of the message
		:type return_address: object address
		:rtype: none
		"""
		pf = self.__art__
		mf = message.__art__	# Could go straight to __class__.
		mc = message.__class__

		shift = pf.value
		def transition(state):
			r = shift.get(state, None)
			if r is None:
				return None

			f = r.get(mc, None)
			if f:
				return f

			for c, f in r.items():
				if isinstance(message, c):
					return f

			return r.get(Unknown, None)

		t = transition(self.current_state)
		if t is None:
			t = transition(DEFAULT)
			if t is None:
				if pf.execution_trace and mf.execution_trace:
					if isinstance(message, Faulted):
						f = str(message)
						self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>, %s' % (mf.name, return_address[-1], f))
					else:
						self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>' % (mf.name, return_address[-1]))
				return

		if pf.execution_trace and mf.execution_trace:
			if isinstance(message, Faulted):
				f = str(message)
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>, %s' % (mf.name, return_address[-1], f))
			else:
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>' % (mf.name, return_address[-1]))
		self.current_state = t(self, message)
		self.previous_message = message

#
#
def message_handler(name):
	# Cornered into unusual iteration by test framework.
	# Collection of tests fails with "dict changed its size".
	for k in list(sys.modules):
		v = sys.modules[k]
		if isinstance(v, types.ModuleType):
			try:
				f = v.__dict__[name]
				if isinstance(f, types.FunctionType):
					return f
			except KeyError:
				pass
	return None

def statemachine_save(self, message):
	self.save(message)
	return self.current_state

def unfold(folded):
	for f in folded:
		if isinstance(f, (tuple, list)):
			yield from unfold(f)
		else:
			yield f

def bind_stateless(machine, dispatch, *args, **kw_args):
	"""Sets the runtime environment for the given stateless machine. Returns nothing.

	This function (optionally) auto-constructs the message
	dispatch table and also saves control values.

	The dispatch is a simple list of the expected
	messages::

		dispatch = (Start, Job, Stop)

	Using this list and a naming convention the ``bind``
	function searches the application for the matching
	functions and installs them in the appropriate
	dispatch entry. The naming convention is;

		<`machine name`>_<`expected message`>

	The control values are the same as for Points (see
	:func:`~.point.bind_point`). This function actually
	calls the ``bind_point`` function to ensure consistent
	initialization.

	:param machine: class derived from ``machine.Stateless``
	:type machine: a class
	:param dispatch: the list of expected messages
	:type dispatch: a tuple
	:param args: the positional arguments to be forwarded
	:type args: a tuple
	:param kw_args: the named arguments to be forwarded
	:type kw_args: a dict
	"""
	bind_point(machine, *args, **kw_args)
	if dispatch is None:
		return
	shift = {}
	for s in unfold(dispatch):
		name = '%s_%s' % (machine.__name__, s.__name__)
		f = message_handler(name)
		if f:
			shift[s] = f
		else:
			raise PointConstructionError('Stateless function "%s" not found' % (name,))

	machine.__art__.value = shift

def bind_statemachine(machine, dispatch, *args, **kw_args):
	"""Sets the runtime environment for the given FSM. Returns nothing.

	This function (optionally) auto-constructs the message
	dispatch table and also saves control values.

	The dispatch is a description of states, expected
	messages and messages that deserve saving::

		dispatch = {
			STATE_1: (Start, ()),
			STATE_2: ((Job, Pause, UnPause, Stop), (Check,)),
			STATE_3: ((Stop, ()),
		}

	Consider ``STATE_2``; The machine will accept 4 messages and
	will save an additional message, ``Check``.

	Using this list and a naming convention the ``bind``
	function searches the application for the matching
	functions and installs them in the appropriate
	dispatch entry. The naming convention is;

		<`machine name`>_<`state`>_<`expected message`>

	The control values available are the same as for Points
	(see :func:`~.point.bind_point`). This function
	actually calls the ``bind_point`` function to ensure
	consistent initialization.

	:param machine: class derived from ``machine.StateMachine``
	:type machine: a class
	:param dispatch: specification of a FSM
	:type dispatch: a dict of tuples
	:param args: the positional arguments to be forwarded
	:type args: a tuple
	:param kw_args: the named arguments to be forwarded
	:type kw_args: a dict
	"""
	bind_point(machine, *args, **kw_args)
	if dispatch is None:
		return
	shift = {}
	for state, v in dispatch.items():
		if not isinstance(v, tuple) or len(v) != 2:
			raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] dispatch is not a tuple or is not length 2')
		matching, saving = v

		if not isinstance(matching, tuple):
			raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] (matching) is not a tuple')
		if not isinstance(saving, tuple):
			raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] (saving) is not a tuple')

		for m in matching:
			if m in saving:
				raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] has "{m.__name__}" in both matching and saving')
			name = '%s_%s_%s' % (machine.__name__, state.__name__, m.__name__)
			f = message_handler(name)
			if f:
				r = shift.get(state, None)
				if r is None:
					r = {}
					shift[state] = r
				r[m] = f
			else:
				raise PointConstructionError(f'FSM function "{name}" not found')

		for s in saving:
			r = shift.get(state, None)
			if r is None:
				r = {}
				shift[state] = r
			r[s] = statemachine_save

	machine.__art__.value = shift
