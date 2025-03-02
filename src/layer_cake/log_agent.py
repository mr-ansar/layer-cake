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
"""Logging methods available within the async runtime.

"""
__docformat__ = 'restructuredtext'

import os
import sys
import time

from .virtual_point import *
from .virtual_runtime import *
from .point_runtime import *
from .point_machine import *

__all__ = [
	'LogAgent',
]

__all__ = [
	'PEAK_BEFORE_BLOCKING',
	'LogAgent',
]

#
#
PEAK_BEFORE_BLOCKING = 1024 * 32

class LogAgent(Threaded, Stateless):
	"""
	A stateless, async object that accepts PointLog messages originating
	from calls to ``Point.`` ``debug``, ``trace``, ``console``,
	``warning`` and ``fault``, and presents them to a saved method that
	might be the default ``log_to_stderr`` or an application-defined
	method.

	The ``LogAgent`` derives from ``Queue``, i.e. it will enjoy its
	own dedicated thread. The result is that logs can originate from
	any runtime Ansar thread and will be collected/serialized at the
	sole LogAgent instance. The saved log method can enjoy the
	knowledge that all multi-threading issues are resolved and that
	logs are buffered in a reliable and robust fashion.

	A part of delivering on those promises is the custom initialization
	of the underlying Queue object. It is set to blocking of upstream
	sources and the size of the Queue is set to a generous, custom
	value.

	Note the complete disabling of all logging for ``LogAgent``. It
	doesnt make much sense for the logger to log to itself and
	certainly not during creation where at some point it exists
	but is not yet entered into Ansar tables. At such a moment
	send would fail - at best.
	"""

	def __init__(self, method):
		Threaded.__init__(self, blocking=True, maximum_size=PEAK_BEFORE_BLOCKING)
		Stateless.__init__(self)
		self.method = method
		self.tap = []

def LogAgent_Start(self, message):
	pass

def LogAgent_PointLog(self, message):
	try:
		line = self.method(message)
	except Exception as e:
		s = str(e)
		return

def LogAgent_RedirectLog(self, message):
	redirect = message.redirect
	try:
		redirect.from_previous(self.method)
	except AttributeError:
		pass
	self.method = redirect

def LogAgent_OpenTap(self, message):
	self.tap.append(self.return_address)

def LogAgent_CloseTap(self, message):
	try:
		self.tap.remove(self.return_address)
	except ValueError:
		pass

def LogAgent_Enquiry(self, message):
	"""
	A query from the ``tear_down`` function to ensure that all previous
	messages have been processed.
	"""
	self.reply(Ack())

def LogAgent_Stop(self, message):
	self.complete()

LOG_AGENT_DISPATCH = (Start,
	PointLog,
	Enquiry, Stop)

bind_stateless(LogAgent, dispatch = LOG_AGENT_DISPATCH,
	lifecycle=False, message_trail=False,
	execution_trace=False, user_logs=USER_LOG.NONE)
