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

"""Temporary, thread-safe buffering of sent messages and how to get messages with reordering.

A collection of classes to be inherited by different points. Most notably
synchronous channels, and the 2 different machine types.
"""
__docformat__ = 'restructuredtext'

from queue import Queue, Full, Empty
from collections import deque

from .virtual_memory import *
from .message_memory import *
from .virtual_runtime import *
from .point_runtime import *

__all__ = [
	'PEAK_BEFORE_DROPPED',
	'Pump',
]

PEAK_BEFORE_DROPPED = 16384
GRACE_PERIOD = 5

# The buffering between senders and receivers. Firstly this is a
# wrapper around the system queue. Then there are several flavours
# of access to that wrapper. One style about sync access and the
# other about message processing for machines. Both of them implementing
# the save-replay model from SDL.
class Pump(object):
	"""Base for any object intended to operate as a message queue.

	:param blocking: behaviour on queue full
	:type blocking: bool
	:param maximum_size: number of message to hold
	:type maximum_size: int
	"""

	def __init__(self, blocking=False, maximum_size=PEAK_BEFORE_DROPPED):
		"""Construct an instance of pump."""
		self.blocking = blocking
		self.message_queue = Queue(maxsize=maximum_size)
		self.thread_function = None
		self.assigned_thread = None

	def put(self, mtr):
		"""Append the [message, to, return] triple to the queue."""
		try:
			self.message_queue.put(mtr, self.blocking)
		except Full:
			# Silently FOTF.
			pass

	def get(self):
		"""Return the pending [message, to, return] triplet or block."""
		mtr = self.message_queue.get()
		return mtr
