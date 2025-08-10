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
	"""
	Settings to control logging and other behaviour, for a Point.

	:param name: the name of the class being registered
	:param module: the name of the module the class is located in
	:param return_type: hint/portable describing the return type
	:type return_type: :ref:`tip<type-reference>`
	:param entry_point: enable library loading with list of expected messages
	:param flags: named values passed on
	"""

	def __init__(self,
			name: str, module: str, return_type=None, entry_point: list=None,
			**flags):
		super().__init__(name, module, **flags)
		self.return_type = return_type
		self.entry_point = entry_point
		self.value = None

#
def bind_routine(routine, return_type=None, entry_point: list=None,
		lifecycle: bool=True, message_trail: bool=True, execution_trace: bool=True,
		user_logs: USER_LOG=USER_LOG.DEBUG, **explicit_schema):
	"""
	Set the type information and runtime controls for the function.

	Values assigned in this function affect the behaviour for all instances of
	the given type.

	:param routine: function to be registered as a routine
	:type routine: :ref:`object type<lc-object-type>`
	:param return_type: type expression for the return value
	:type return_type: :ref:`tip<type-reference>`
	:param entry_point: enable library loading with list of expected messages
	:param lifecycle: enable log at creation, ending...
	:param message_trail: enable log when message is sent
	:param execution_trace: enable log when message is received
	:param user_logs: the logging level for this message type
	"""
	rt = PointRuntime(routine.__name__, routine.__module__,
		lifecycle=lifecycle,
		message_trail=message_trail,
		execution_trace=execution_trace,
		user_logs=user_logs)

	setattr(routine, '__art__', rt)

	# Replace with identity object, installing as required.
	explicit_schema = {k: install_type(v) for k, v in explicit_schema.items()}

	hints = typing.get_type_hints(routine)
	routine_hints, routine_return = install_hints(hints)

	if return_type:
		routine_return = install_type(return_type)

	r = {}
	for k, a in explicit_schema.items():
		routine_hints[k] = a	# Add or override existing.

	if entry_point is not None:
		entry_point = [install_type(a) for a in entry_point]

	rt.schema = routine_hints
	rt.return_type = routine_return
	rt.entry_point = entry_point

	install_portable(UserDefined(routine))


def bind_point(point: Point, return_type=None, entry_point: list=None, thread: str=None,
		lifecycle: bool=True, message_trail: bool=True, execution_trace: bool=True,
		user_logs: USER_LOG=USER_LOG.DEBUG, **explicit_schema):
	"""
	Set the type information and runtime controls for the asynchronous object.

	Values assigned in this function affect the behaviour for all instances of
	the given type.

	:param point: instance of an asynchronous object
	:param return_type: type expression for the return value
	:type return_type: :ref:`tip<type-reference>`
	:param lifecycle: enable log when object is created or destroyed
	:param message_trail: enable log when message is sent
	:param execution_trace: enable log when message is received
	:param user_logs: the logging level for this object type
	"""
	rt = PointRuntime(point.__name__, point.__module__,
		lifecycle=lifecycle,
		message_trail=message_trail,
		execution_trace=execution_trace,
		user_logs=user_logs)

	setattr(point, '__art__', rt)

	explicit_schema = {k: install_type(v) for k, v in explicit_schema.items()}

	hints = typing.get_type_hints(point.__init__)
	point_hints, _ = install_hints(hints)

	if return_type:
		return_type = install_type(return_type)

	r = {}
	for k, a in explicit_schema.items():
		point_hints[k] = a	# Add or override existing.

	if entry_point is not None:
		entry_point = [install_hint(a) for a in entry_point]

	rt.schema = point_hints
	rt.return_type = return_type
	rt.entry_point = entry_point

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

def bind_stateless(machine: Stateless, dispatch: tuple, return_type=None, entry_point: list=None, **explicit_schema):
	"""
	Set the type information and runtime controls for the non-FSM machine.

	Values assigned in this function affect the behaviour for all instances of
	the given type.

	:param machine: class to be registered as a machine
	:param dispatch: list of expected messages
	:param return_type: type expression for the return value
	:type return_type: :ref:`tip<type-reference>`
	:param entry_point: enable library loading with list of expected messages
	"""
	bind_point(machine, return_type=return_type, entry_point=entry_point, **explicit_schema)
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

def bind_statemachine(machine: StateMachine, dispatch: dict, return_type=None, entry_point: list=None, **explicit_schema):
	"""
	Set the type information and runtime controls for the FSM machine.

	Values assigned in this function affect the behaviour for all instances of
	the given type.

	The dispatch is a description of states, expected
	messages and messages that deserve saving::

		dispatch = {
			STATE_1: (Start, ()),
			STATE_2: ((Job, Pause, UnPause, Stop), (Check,)),
			STATE_3: ((Stop, ()),
		}

	Consider ``STATE_2``; The machine will accept 4 messages and
	will save an additional message, ``Check``.

	:param machine: class to be registered as a machine
	:param dispatch: table of current state and expected messages
	:param return_type: type expression for the return value
	:type return_type: :ref:`tip<type-reference>`
	:param entry_point: enable library loading with list of expected messages
	"""
	bind_point(machine, return_type=return_type, entry_point=entry_point, **explicit_schema)
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

	- :func:`~.bind_message`
	- :func:`~.bind_routine`
	- :func:`~.bind_stateless`
	- :func:`~.bind_statemachine`

	:param object_type: type of async entity
	:type object_type: :ref:`object type<lc-object-type>`
	:param args: arguments passed to special bind function
	:type args: tuple
	:param kw_args: named arguments passed to special bind function
	:type kw_args: dict
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
			install_portable(UserDefined(object_type))
		else:
			bind_point(object_type, *args, **kw_args)
	elif not is_message_class(object_type):
		bind_message(object_type, *args, **kw_args)

bind_point(Channel)

bind_routine(threaded_object, lifecycle=False, message_trail=False, execution_trace=False, user_logs=USER_LOG.NONE)
bind_routine(object_dispatch, lifecycle=False, message_trail=False, execution_trace=False, user_logs=USER_LOG.NONE)
