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
"""Format startup and shutdown of the async runtime.

Ensure that the support for async operation is in place when the process
needs it. Ensure that support is cleared out during process termination.
"""
__docformat__ = 'restructuredtext'

import os
import threading
import atexit
from .object_space import *
from .virtual_runtime import *
from .virtual_point import *
from .point_runtime import *
from .general_purpose import *
from .object_logs import *

__all__ = [
	'PB',
	'AddOn',
	'QuietChannel',
	'start_up',
	'tear_down',
	'open_channel',
	'drop_channel',
	'channel',
]

PB = Gas(
	root=None,					# The top of the hierarchy.
	thread_dispatch={},
	add_ons=[],
	exit_status=None,
)

DEFAULT_HOME = '.layer-cake'

# Register create and stop functions for some
# point-based singleton.
class AddOn(object):
	def __init__(self, create, stop):
		cs = (create, stop)
		PB.add_ons.append(cs)

# A silent intermediary between the worlds of sync and
# async.
class QuietChannel(Channel):
	def __init__(self):
		Channel.__init__(self)

bind_point(QuietChannel, lifecycle=False, message_trail=False, execution_trace=False, user_logs=USER_LOG.NONE)

# A non-logging channel.
root_lock = threading.RLock()

def start_up(logs=log_to_nowhere):
	"""Start the async runtime. Return the root object.

	This is the function that actually creates the threads and objects
	that are needed to support Point operations, e.g. timers. It also
	arranges for automated cleanup using atexit.

	It first checks to see if the runtime is already up, in a thread-safe
	way. Only the first call has any effect.

	:param logs: an object expecting to receive log objects
	:type logs: a callable object
	:rtype: channel
	"""
	global root_lock
	try:
		root_lock.acquire()
		root = PB.root
		if root is None:
			atexit.register(tear_down)

			nowhere = Point()
			root = nowhere.create(QuietChannel)
			PB.root = root
			#PRA.log_address = root.create(LogAgent, logs)
			#PRA.timer_address = root.create(cotems():
			#	t = root.create(object_dispatch)
			#	for c in s:
			#		set_queue(c, t)
			#	PB.thread_dispatch[k] = t
			#for cs in PB.add_ons:
			#	cs[0](root)
	finally:
		root_lock.release()
	return root

def tear_down():
	"""End the async runtime. Returns nothing.

	:rtype: None
	"""
	global root_lock
	try:
		root_lock.acquire()
		root = PB.root
		if root:
			s = Stop()
			'''
			for cs in reversed(PB.add_ons):
				cs[1](root)
			for _, t in PB.thread_dispatch.items():
				root.send(s, t)
				root.select(Completed)
			bg = get_queue_address(None)
			root.send(s, bg)
			root.select(Completed)
			halt(PRA.circuit_address)
			root.select(Completed)co
			root.select(Completed)
			drop_channel(root)
			'''
			root = None
	finally:
		root_lock.release()

	exit_status = PB.exit_status
	if exit_status is not None:
		os._exit(exit_status)

# Access to async from sync section of an
# application.
def open_channel():
	"""Start the runtime for a non-standard executable. Return a unique async object.

	Create a new async object for the purposes of initiating
	async activity, typically from within a non-async section of
	code. Registers a cleanup function with the process, to execute
	on process termination.

	:rtype: Point-based object
	"""
	root = start_up()
	channel = root.create(Channel)
	return channel

def drop_channel(c):
	"""End the runtime for a non-standard executable. Return nothing.

	Tear down the runtime created by ``open_channel()``, i.e. ``boot_up()``.

	:param c: a channel returned by open_channel()
	:type c: Point-based object
	:rtype: none
	"""
	if c.__art__.lifecycle:
		c.log(USER_TAG.DESTROYED, 'Destroyed')
	destroy_an_object(c.address)

#
#
class channel(object):
	"""A context to automate the opening and closing of a channel.

	Typically used in a traditional, sync application to access the async
	features of ansar. May be used anywhere within an application. Each
	instance creates a unique channel. The parameter provides for control
	over the fate of logs. This only has an effect on the first use of
	the class.

	:param logs: an object expecting to receive log objects
	:type logs: a callable object
	"""
	def __init__(self):
		self.channel = open_channel()

	def __enter__(self):
		return self.channel

	def __exit__(self, exc_type=None, exc_value=None, traceback=None):
		drop_channel(self.channel)

		# Handle exceptions that may have come up during execution, by
		# default any exceptions are raised to the user.
		if exc_type is not None:
			return False
		return True
