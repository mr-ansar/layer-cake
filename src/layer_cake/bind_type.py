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
__docformat__ = 'restructuredtext'

import sys
import types
import typing

from .virtual_memory import *
from .message_memory import *
from .convert_type import *
from .convert_signature import *
from .virtual_runtime import *
from .virtual_point import *
from .point_machine import *

__all__ = [
	'PointRuntime',
	'bind_routine',
	'bind_point',
	'bind_stateless',
	'bind_statemachine',
	'bind',
]

#
class PointRuntime(Runtime):
	"""Settings to control logging and other behaviour, for a Point."""

	def __init__(self,
			name, module, return_type=None, api=None,
			**flags):
		"""Construct the settings.

		:param name: the name of the class being registered
		:type name: str
		:param module: the name of the module the class is located in
		:type module: str
		:param value: the application value, e.g. a function
		:type value: any
		:param lifecycle: enable logging of created, destroyed
		:type lifecycle: bool
		:param message_trail: enable logging of sent
		:type message_trail: bool
		:param execution_trace: enable logging of received
		:type execution_trace: bool
		:param copy_before_sending: enable auto-copy before send
		:type copy_before_sending: bool
		:param not_portable: prevent inappropriate send
		:type not_portable: bool
		:param user_logs: log level
		:type user_logs: int
		"""
		super().__init__(name, module, **flags)
		self.return_type = return_type
		self.api = api
		self.value = None

#
def bind_routine(routine, return_type=None, api=None, lifecycle=True, message_trail=True, execution_trace=True, user_logs=USER_LOG.DEBUG, **explicit_schema):
	"""Set the runtime flags for the given async function.

	:param routine: an async function.
	:type routine: function
	:param lifecycle: log all create() and complete() events
	:type lifecycle: bool
	:param message_trail: log all send() events
	:type message_trail: bool
	:param execution_trace: log all receive events
	:type execution_trace: bool
	:param user_logs: the logging level for this object type
	:type user_logs: enumeration
	"""
	rt = PointRuntime(routine.__name__, routine.__module__,
		lifecycle=lifecycle,
		message_trail=message_trail,
		execution_trace=execution_trace,
		user_logs=user_logs)

	setattr(routine, '__art__', rt)

	# Replace with identity object, installing as required.
	explicit_schema = {k: install_portable(v) for k, v in explicit_schema.items()}

	hints = typing.get_type_hints(routine)
	routine_hints, routine_return = install_hints(hints)

	if return_type:
		routine_return = install_type(return_type)

	r = {}
	for k, a in explicit_schema.items():
		routine_hints[k] = a	# Add or override existing.

	if api is not None:
		api = [install_type(a) for a in api]

	rt.schema = routine_hints
	rt.return_type = routine_return
	rt.api = api

def bind_point(point, return_type=None, api=None, thread=None, lifecycle=True, message_trail=True, execution_trace=True, user_logs=USER_LOG.DEBUG, **explicit_schema):
	"""Set the runtime flags for the given async object type.

	:param point: a class derived from ``Point``.
	:type point: class
	:param lifecycle: log all create() and complete() events
	:type lifecycle: bool
	:param message_trail: log all send() events
	:type message_trail: bool
	:param execution_trace: log all receive events
	:type execution_trace: bool
	:param user_logs: the logging level for this object type
	:type user_logs: enumeration
	"""
	rt = PointRuntime(point.__name__, point.__module__,
		lifecycle=lifecycle,
		message_trail=message_trail,
		execution_trace=execution_trace,
		user_logs=user_logs)

	setattr(point, '__art__', rt)

	explicit_schema = {k: install_portable(v) for k, v in explicit_schema.items()}

	hints = typing.get_type_hints(point.__init__)
	point_hints, _ = install_hints(hints)

	if return_type:
		return_type = install_portable(return_type)

	r = {}
	for k, a in explicit_schema.items():
		point_hints[k] = a	# Add or override existing.

	if api is not None:
		api = [install_hint(a) for a in api]

	rt.schema = point_hints
	rt.return_type = return_type
	rt.api = api

	if thread:
		try:
			q = VP.thread_classes[thread]
		except KeyError:
			q = set()
			VP.thread_classes[thread] = q
		q.add(point)

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

def bind_stateless(machine, dispatch, return_type=None, api=None, **kw_args):
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
	bind_point(machine, return_type=return_type, api=api, **kw_args)
	if dispatch is None:
		return

	shift = {}
	messaging = {}
	for s in unfold(dispatch):
		p = install_type(s)
		x = portable_to_signature(p)
		d = isinstance(p, UserDefined)
		if d:
			tag = p.element.__name__
		else:
			tag = portable_to_tag(p)
		name = f'{machine.__name__}_{tag}'
		
		f = message_handler(name)
		if f is None:
			raise PointConstructionError(f'function "{name}" not found ({machine.__art__.path})')

		shift[x] = f
		if d and s is not Unknown:
			messaging[p.element] = f

	machine.__art__.value = (shift, messaging)

def bind_statemachine(machine, dispatch, return_type=None, api=None, **kw_args):
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
	bind_point(machine, return_type=return_type, api=api, **kw_args)
	if dispatch is None:
		return
	shift = {}
	messaging = {}
	for state, v in dispatch.items():
		if not isinstance(v, tuple) or len(v) != 2:
			raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] dispatch is not a tuple or is not length 2')
		matching, saving = v

		if not isinstance(matching, tuple):
			raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] (matching) is not a tuple')
		if not isinstance(saving, tuple):
			raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] (saving) is not a tuple')

		for m in matching:
			p = install_type(m)
			x = portable_to_signature(p)
			d = isinstance(p, UserDefined)
			e = isinstance(p, Enumeration)
			if d or e:
				tag = p.element.__name__
			else:
				tag = portable_to_tag(p)
			name = '%s_%s_%s' % (machine.__name__, state.__name__, tag)
			f = message_handler(name)
			if f is None:
				raise PointConstructionError(f'function "{name}" not found ({machine.__art__.path})')

			r = shift.get(state, None)
			if r is None:
				r = {}
				shift[state] = r
			r[x] = f

			if d:
				r = messaging.get(state, None)
				if r is None:
					r = {}
					messaging[state] = r
				r[p.element] = f

		for s in saving:
			p = install_type(s)
			x = portable_to_signature(p)
			r = shift.get(state, None)
			if r is None:
				r = {}
				shift[state] = r
			if x in r:
				raise PointConstructionError(f'FSM {machine.__name__}[{state.__name__}] has "{m.__name__}" in both matching and saving')
			r[x] = statemachine_save

			if isinstance(p, UserDefined):
				r = messaging.get(state, None)
				if r is None:
					r = {}
					messaging[state] = r
				r[p.element] = f

	machine.__art__.value = (shift, messaging)

def bind(object_type, *args, **kw_args):
	"""
	Forwards all arguments on to a custom bind function
	according to the type of the first argument.

	Refer to **ansar.encode** for registration of messages;

	- :func:`~.point.bind_function`
	- :func:`~.machine.bind_stateless`
	- :func:`~.machine.bind_statemachine`

	:param object_type: type of async entity
	:type object_type: message class, function or Point-based class
	:param args: arguments passed to the object instance
	:type args: positional argument tuple
	:param kw_args: named arguments passed to the object instance
	:type kw_args: named arguments dict
	"""
	# Damn line length constraint.
	if isinstance(object_type, types.FunctionType):
		bind_routine(object_type, *args, **kw_args)
	elif issubclass(object_type, Point):
		if issubclass(object_type, Machine):
			if issubclass(object_type, Stateless):
				bind_stateless(object_type, *args, **kw_args)
			elif issubclass(object_type, StateMachine):
				bind_statemachine(object_type, *args, **kw_args)
			else:
				pce = f'cannot bind {object_type} - unknown machine type'
				raise PointConstructionError(pce)
		else:
			bind_point(object_type, *args, **kw_args)
	elif not is_message_class(object_type):
		bind_message(object_type, *args, **kw_args)

bind_point(Channel)

bind_routine(threaded_object, lifecycle=False, message_trail=False, execution_trace=False, user_logs=USER_LOG.NONE)
bind_routine(object_dispatch, lifecycle=False, message_trail=False, execution_trace=False, user_logs=USER_LOG.NONE)
