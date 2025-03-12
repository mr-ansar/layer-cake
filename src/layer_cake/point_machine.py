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

import re

from .virtual_memory import *
from .message_memory import *
from .convert_signature import *
from .convert_type import *
from .virtual_runtime import *
from .point_runtime import *
from .virtual_point import *

__all__ = [
	'Stateless',
	'StateMachine',
	'DEFAULT',
]

class DEFAULT: pass

# Find the state and message embedded within a function name.
state_message = re.compile('(?P<state>[A-Z][A-Z0-9]*(_[A-Z0-9]+)*)_(?P<message>[A-Z][A-Za-z0-9]*)')

unknown = install_hint(Unknown)

class Stateless(Machine):
	"""Base for simple machines that maintain no formal state.

	Messages are received by an assigned thread and dispatched to
	handlers according to the type of the received message.
	"""
	def __init__(self):
		Machine.__init__(self)

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
		shift, messaging = pf.value

		def transition():
			art = getattr(message, '__art__', None)
			if art:
				m = message
				p = lookup_signature(art.path)
			elif isinstance(message, tuple):
				m = message[0]
				p = message[1]
			else:
				raise ValueError(f'machine "{pf.path}" cannot identify message ({message})')

			f = shift.get(id(p), None)			# Explicit match.
			if f:
				return m, p, f

			if art:
				for c, f in messaging.items():
					if isinstance(m, c):		# Base-derived match.
						return m, p, f

			f = shift.get(id(unknown), None)	# Catch-all.
			return m, p, f

		m, p, f = transition()
		if f is None:
			if pf.execution_trace:
				t = portable_to_tag(p)
				if isinstance(m, Faulted):
					f = str(m)
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>, %s' % (t, return_address[-1], f))
				else:
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>' % (t, return_address[-1]))
			return

		if pf.execution_trace:
			t = portable_to_tag(p)
			if isinstance(m, Faulted):
				f = str(m)
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>, %s' % (t, return_address[-1], f))
			else:
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>' % (t, return_address[-1]))

		self.message_type = p
		f(self, m)
		self.previous_message = m

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
		shift, messaging = pf.value

		def transition(state):
			art = getattr(message, '__art__', None)
			if art:
				m = message
				p = lookup_signature(art.path)
			elif isinstance(message, tuple):
				m = message[0]
				p = message[1]
			else:
				raise ValueError(f'machine "{pf.path}" cannot identify message ({message})')

			shifted = shift.get(state, None)
			if shifted is None:
				raise ValueError(f'machine "{pf.path}" shifted to nowhere')

			f = shifted.get(id(p), None)				# Explicit match.
			if f:
				return m, p, f

			if art:
				messaged = messaging.get(state, None)
				if messaged:
					for c, f in messaged.items():
						if isinstance(m, c):			# Base-derived match.
							return m, p, f

			f = shifted.get(id(unknown), None)			# Catch-all.
			return m, p, f

		m, p, f = transition(self.current_state)
		if f is None:
			if pf.execution_trace:
				t = portable_to_tag(p)
				if isinstance(message, Faulted):
					f = str(message)
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>, %s' % (t, return_address[-1], f))
				else:
					self.log(USER_TAG.RECEIVED, 'Dropped %s from <%08x>' % (t, return_address[-1]))
			return

		if pf.execution_trace:
			t = portable_to_tag(p)
			if isinstance(message, Faulted):
				f = str(message)
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>, %s' % (t, return_address[-1], f))
			else:
				self.log(USER_TAG.RECEIVED, 'Received %s from <%08x>' % (t, return_address[-1]))

		self.message_type = p
		self.current_state = f(self, m)
		self.previous_message = m
