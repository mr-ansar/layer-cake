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
	'Ack',
	'Nak',
	'Anything',
	'Faulted',
	'Aborted',
	'TimedOut',
	'TemporarilyUnavailable',
	'Overloaded',
	'OutOfService',
]

#
#
class Start(object):
	"""First message received by every async machine, from creator to child."""
	pass

class Returned(object):
	"""Last message sent, from child to creator.

	:param value: return value for an async object
	:type value: any
	"""
	def __init__(self, value=None, created_type=None):
		self.value = value
		self.created_type = created_type

bind_message(Start)
bind_message(Returned, value=Any(), created_type=Type())

#
#
class Stop(object):
	"""Initiate teardown in the receiving object."""
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
	"""Report a positive state."""
	pass

class NotReady(object):
	"""Report a positive state."""
	pass

bind_message(Ready, copy_before_sending=False)
bind_message(NotReady, copy_before_sending=False)

#
#
class Ping(object):
	"""Test for reachability."""
	pass

class Enquiry(object):
	"""Prompt an action from receiver."""
	pass

class Ack(object):
	"""Report in the positive."""
	pass

class Nak(object):
	"""Report in the negative."""
	pass

bind_message(Ping, copy_before_sending=False)
bind_message(Enquiry, copy_before_sending=False)
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
	"""Generic error signal to interested party."""
	def __init__(self, condition=None, explanation=None, error_code=None, exit_status=None):
		self.condition = condition or 'fault'
		self.explanation = explanation
		self.error_code = error_code
		self.exit_status = exit_status

	def __str__(self):
		if self.explanation:
			return f'{self.condition} ({self.explanation})'
		return self.condition

bind_message(Faulted,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
)

class Aborted(Faulted):
	def __init__(self):
		Faulted.__init__(self, 'aborted', 'user or software interrupt')

class TimedOut(Faulted):
	def __init__(self, timer=None):
		if timer and hasattr(timer, '__art__'):
			t = timer.__art__.name
		else:
			t = 'ding'
		self.timer = timer
		Faulted.__init__(self, 'timed out', f'"{t}" exceeded')

class TemporarilyUnavailable(Faulted):
	def __init__(self, text=None, unavailable=None, request=None):
		Faulted.__init__(self, text)
		self.unavailable = unavailable or []
		self.request = request

class Overloaded(Faulted):
	def __init__(self, text=None, request=None):
		Faulted.__init__(self, text)
		self.request = request

class OutOfService(Faulted):
	def __init__(self, text=None, request=None):
		Faulted.__init__(self, text)
		self.request = request

bind_message(TimedOut,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	timer=Type(),
)

bind_message(TemporarilyUnavailable,
	condition=Unicode(),
	explanation=Unicode(),
	error_code=Integer8(),
	exit_status=Integer8(),
	unavailable=VectorOf(Unicode()),
	request=Unicode(),
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
