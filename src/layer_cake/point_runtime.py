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
"""Define the standard messages within the async runtime.

.

.. autoclass:: Start
.. autoclass:: Returned
.. autoclass:: Stop
"""

from .virtual_memory import *
from .message_memory import *
from .convert_signature import *
from .convert_type import *

__docformat__ = 'restructuredtext'

__all__ = [
	'Start',
	'Returned',
	'Stop',
	'Pause',
	'Resume',
	'Ready',
	'NotReady',
	'Ping',
	'Enquiry',
	'Discover',
	'Inspect',
	'Ack',
	'Nak',
	'Anything',
	'Faulted',
	'Aborted',
	'TimedOut',
	'TemporarilyUnavailable',
	'Busy',
	'Overloaded',
	'OutOfService',
	'ToBeConfirmed',
	'SelectTable',
	'select_list',
	'select_list_adhoc'
]

#
#
class Start(object):
	"""Notification sent to new object, from parent."""
	pass

class Returned(object):
	"""
	Notification sent to parent, from terminating object.

	:type message: message returned to the parent
	:type message: :ref:`message<lc-message>`
	"""
	def __init__(self, message: Any=None):
		self.message = message
	
	def value(self):
		"""
		Extract the Python value from the returned message.

		:rtype: the expected, application data
		"""
		m, p, a = cast_back(self.message)
		return m
	
	def cast_back(self):
		m, p, a = cast_back(self.message)
		return m, p

bind_message(Start)
bind_message(Returned)

#
#
class Stop(object):
	"""Initiate termination in the receiving object."""
	pass

class Pause(object):
	"""Suspend operation in the receiving object."""
	pass

class Resume(object):
	"""Resume operation in the receiving object."""
	pass

bind_message(Stop)
bind_message(Pause)
bind_message(Resume)

#
#
class Ready(object):
	"""Report a state of readiness."""
	pass

class NotReady(object):
	"""Report that currently not ready."""
	pass

bind_message(Ready, copy_before_sending=False)
bind_message(NotReady, copy_before_sending=False)

#
#
class Ping(object):
	"""Test for reachability and presence."""
	pass

class Enquiry(object):
	"""Prompt an action from receiver."""
	pass

class Discover(object):
	"""Request for capabilities."""
	pass

class Inspect(object):
	"""Request for operational status."""
	pass

class Ack(object):
	"""Report in the positive."""
	pass

class Nak(object):
	"""Report in the negative."""
	pass

bind_message(Ping, copy_before_sending=False)
bind_message(Enquiry, copy_before_sending=False)
bind_message(Discover, copy_before_sending=False)
bind_message(Inspect, copy_before_sending=False)
bind_message(Ack, copy_before_sending=False)
bind_message(Nak, copy_before_sending=False)

#
class Anything(object):
	def __init__(self, thing=None):
		self.thing = thing

bind_message(Anything, copy_before_sending=False,
	thing=Any(),
)

#
#
class Faulted(object):
	"""
	Generic error signal to interested party.
	
	:param condition: description of fault
	:param explanation: description of cause
	:param error_code: internal error code
	:param exit_status: recommended exit status
	"""
	def __init__(self, condition: str=None, explanation: str=None, error_code: int=None, exit_status: int=None):
		self.condition = condition or 'fault'
		self.explanation = explanation
		self.error_code = error_code
		self.exit_status = exit_status

	def __str__(self):
		if self.explanation:
			return f'{self.condition} ({self.explanation})'
		return self.condition

bind_message(Faulted)

class Aborted(Faulted):
	"""
	Asynchronous object received a :class:`~.Stop`. Terminating.
	
	Derived from :class:`~.Faulted`.
	"""
	def __init__(self):
		Faulted.__init__(self, 'aborted', 'user or software interrupt')

class TimedOut(Faulted):
	"""
	Asynchronous object received a timer message.
	
	Derived from :class:`~.Faulted`.

	:param timer: timer that was exceeded
	:type timer: :ref:`object type<lc-object-type>`
	"""
	def __init__(self, timer=None):
		if timer and hasattr(timer, '__art__'):
			t = timer.__art__.name
		else:
			t = 'ding'
		self.timer = timer
		Faulted.__init__(self, 'timed out', f'"{t}" exceeded')

class TemporarilyUnavailable(Faulted):
	"""
	Temporarily unable to deliver normal service.
	
	Derived from :class:`~.Faulted`.

	:param text: description of reason
	:param unavailable: names of unavailable services
	"""
	def __init__(self, text: str=None, unavailable: list[str]=None):
		Faulted.__init__(self, text)
		self.unavailable = unavailable or []

class Busy(Faulted):
	"""
	Experiencing heavy load, recovery expected. Request is rejected.
	
	Derived from :class:`~.Faulted`.

	:param condition: description of load
	:param explanation: description of cause
	"""
	def __init__(self, condition: str=None, explanation: str=None):
		Faulted.__init__(self, condition, explanation)

class Overloaded(Faulted):
	"""
	Experiencing heavy load, recovery unknown. Request is rejected.
	
	Derived from :class:`~.Faulted`.

	:param text: description of condition
	"""
	def __init__(self, text: str=None):
		Faulted.__init__(self, text)

class OutOfService(Faulted):
	"""
	Service not available until further notice. Request is rejected.
	
	Derived from :class:`~.Faulted`.

	:param text: description of load
	"""
	def __init__(self, text: str=None):
		Faulted.__init__(self, text)

class ToBeConfirmed(Faulted):
	"""
	An exchange is incomplete. An update is expected.
	
	Derived from :class:`~.Faulted`.

	:param text: description of the delay
	"""
	def __init__(self, text: str=None):
		Faulted.__init__(self, text)

bind_message(Aborted,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
)

bind_message(TimedOut,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	timer=Any(),
)

bind_message(TemporarilyUnavailable,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	unavailable=VectorOf(Unicode()),
)

bind_message(Busy,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
)

bind_message(Overloaded,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	request=Unicode(),
)

bind_message(OutOfService,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	request=Unicode(),
)

bind_message(ToBeConfirmed,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	request=Unicode(),
)

#
unknown = portable_to_signature(UserDefined(Unknown))

class SelectTable(object):
	def __init__(self, unique, messaging):
		self.unique = unique
		self.messaging = messaging

	def find(self, message):
		m, p, a = cast_back(message)
		s = portable_to_signature(p)
		f = self.unique.get(s, None)		# Explicit match.
		if f:
			return f[0], m, f[1]

		if a:
			for c, f in self.messaging.items():
				if isinstance(m, c):			# Base-derived match.
					return f[0], m, f[1]

		f = self.unique.get(unknown, None)	# Catch-all.
		if f:
			return f[0], m, p
		return None

def select_list(*selection):
	'''.'''
	unique = {}
	messaging = {}
	for i, t in enumerate(selection):
		p = install_type(t)
		s = portable_to_signature(p)
		unique[s] = (i, p)
		if isinstance(p, UserDefined):
			messaging[p.element] = (i, p)
	return SelectTable(unique, messaging)

def select_list_adhoc(*selection):
	'''.'''
	unique = {}
	messaging = {}
	for i, t in enumerate(selection):
		p = lookup_type(t)
		s = portable_to_signature(p)
		unique[s] = (i, p)
		if isinstance(p, UserDefined):
			messaging[p.element] = (i, p)
	return SelectTable(unique, messaging)
