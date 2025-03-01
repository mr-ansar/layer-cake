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

"""Registration of routines.


.. autofunction:: bind_routine
"""

__docformat__ = 'restructuredtext'

import typing
from .virtual_memory import *
from .convert_hints import *
from .virtual_runtime import *
from .message_memory import *

__all__ = [
	'bind_routine',
	'RoutineRuntime',
]

class RoutineRuntime(Runtime):
	"""Settings to control logging and other behaviour, for objects and messages."""

	def __init__(self,
			name, module, schema, return_type,
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
		self.schema = schema
		self.return_type = return_type

#
#
def bind_routine(routine, return_type=None, lifecycle=True, message_trail=True, execution_trace=True, user_logs=USER_LOG.DEBUG, **explicit_schema):
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
	rt = RoutineRuntime(routine.__name__, routine.__module__, None, None,
		lifecycle=lifecycle,
		message_trail=message_trail,
		execution_trace=execution_trace,
		user_logs=user_logs)

	setattr(routine, '__art__', rt)

	fix_schema(rt.name, explicit_schema)
	for k, v in explicit_schema.items():
		lookup_type(v)

	hints = typing.get_type_hints(routine)
	routine_hints, routine_return = hints_to_memory(hints)

	if return_type:
		routine_return = fix_expression(return_type, {})

	r = {}
	for k, a in explicit_schema.items():
		if k in routine_hints:
			pass
		routine_hints[k] = a	# Add or override existing.

	rt.schema, rt.return_type = routine_hints, routine_return
