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

"""Primitives and data structures supporting a thread-safe, object space.

"""
__docformat__ = 'restructuredtext'

import threading

from .virtual_memory import *
from .message_pump import *

__all__ = [
	'Completion',
	'create_an_object',
	'destroy_an_object',
	'find_object',
	'OpenAddress',
	'send_a_message',
	'set_queue',
	'get_queue',
	'get_queue_address',
]

# Mechanism for jumping out of non-thread objects, e.g. machines.
class Completion(Exception):
	def __init__(self, value=None):
		self.value = value

# THE BIG BANG STARTS HERE.
# Core async object management.
# Safe serial ids, type library, active objects and messaging.
serial_number = 1
serial_lock = threading.RLock()

def get_next_id():
	"""Thread-safe increment of serial id, return the original value.

	Used during object creation for assignment of unique ids.

	Returns:

	a previously unused, unique Ansar address, suitable for use as a
	send destination.
	"""
	global serial_number, serial_lock
	try:
		serial_lock.acquire()
		next = serial_number
		serial_number += 1
	finally:
		serial_lock.release()
	return (next,)

#
#
object_map  = {}
object_lock = threading.RLock()

def create_an_object(object_type, object_ending, parent_address, args, kw_args):
	"""
	Thread-safe construction of an async object, e.g. queue, thread or
	point. Returns address, object tuple.

	The object is instantiated using the args+kw_args supplied, if any. Then
	the object is pre-loaded with ansar internal information, before
	returning to caller.

	Parameters:

	- `object_type`: a class, the application class that derives from a
	combination of Ansar base classes.
	- `parent_address`: an Ansar address, the address of the object that
	is creating the new object.
	- `args`: tuple of values, the args forwarded on to the object
	__init__ call using `*args`.
	- `kw_args`: dict of named values, the named args forwarded on to the
	 object __init__ call using `**kw_args`.

	Returns:

	a 2-tuple of an Ansar address and an async object instance. The
	former being the unique id for the latter.
	"""
	global object_map, object_lock
	address = get_next_id()
	try:
		created = object_type(*args, **kw_args)
		created.object_ending = object_ending
	except TypeError as e:
		raise RuntimeError(str(e))

	# Some jiggery to resolve the queue for this object. Need the object
	# handle for the buffering and the address for processing of messages.
	# Cant deliver to a queue that may have been destroyed - must always
	# perform lookup during send.
	if issubclass(object_type, Pump):
		assigned_queue = created
	else:
		assigned_queue = get_queue(object_type)

	created.object_address = address
	created.assigned_queue = assigned_queue
	if assigned_queue is None:
		created.queue_address = NO_SUCH_ADDRESS
	else:
		created.queue_address = assigned_queue.object_address
	created.parent_address = parent_address

	try:
		object_lock.acquire()
		object_map[address[-1]] = created
	finally:
		object_lock.release()
	return address, created

def destroy_an_object(address):
	"""
	Thread-safe destruction of an async object. No return.

	Uses the specified address to remove all trace of the object
	from Ansar.

	Returns:

	Nothing.
	"""
	global object_map, object_lock
	try:
		object_lock.acquire()
		try:
			del object_map[address[-1]]
		except KeyError:
			pass
	finally:
		object_lock.release()

def find_object(address):
	"""
	Thread-safe object lookup by address.

	Uses the specified address to retrieve the associated, actual
	object.  This call is dangerous to anyone other than the thread
	object assigned to handle message processing. If the wrong thread
	calls this function the returned object could be deleted from under
	it.

	Parameters:

	- `address`: an Ansar address, the address of the object to be
	retrieved.

	Returns:

	an async object instance or None, if the underlying object no longer
	exists.
	"""
	global object_map, object_lock
	try:
		object_lock.acquire()
		try:
			matched = object_map[address[-1]]
		except KeyError:
			return None
	finally:
		object_lock.release()
	return matched

# Class for safe access to the object underlying an address.
# Used with real caution.
class OpenAddress:
	def __init__(self, address, *args, **kwargs):
		self.object_address = address

	def __enter__(self, *args, **kwargs):
		global object_map, object_lock
		object_lock.acquire()
		try:
			return object_map[self.object_address[-1]]
		except KeyError:
			return None

	def __exit__(self, exc_type=None, exc_value=None, traceback=None):
		global object_map, object_lock
		object_lock.release()
		if (exc_type is not None):
			return False
		return True

#
#
def send_a_message(message, to_address, return_address):
	"""
	Thread-safe transfer of a message between the given addresses. No
	return value and no failures.

	Abstractly messages are sent to a receiving async object.
	Technically that involves up to two lookups 1) find the target
	object and 2) find the queue assigned to that target object. In the
	special case where the target object is its own assigned queue then
	the latter is not necessary.

	The message is appended to the retrieved queue. There is the
	expectation that the assigned thread will take it from the queue and
	either consume it itself (i.e. its a custom object or sync object)
	or present it to one of the auto-dispatching machines (i.e.
	Stateless or StateMachine).

	If either of the two lookups fails - the destination object or the
	assigned queue object do not exist - the send fails silently. This
	is one of the code sites that implements the fall-on-the-floor
	handling of any message that cant be sent. See also the dispatch
	machines where there is no appropriate handler for a certain message
	type.

	Parameters:

	- `message`: a plain, old data object, the Message-based object to
	be transferred.
	- `to_address`: an Ansar address, the async object that will receive
	the message.
	- `return_address`: an Ansar address, the async object that called
	`send`.

	Returns:

	Nothing.
	"""
	global object_map, object_lock
	try:
		object_lock.acquire()
		try:
			to_object = object_map[to_address[-1]]
			if to_object.queue_address[-1] == to_address[-1]:	  # Dont need to lookup self.
				queue_object = to_object
			else:
				queue_object = object_map[to_object.queue_address[-1]]
			queue_object.put([message, to_address, return_address])
		except KeyError:			# No-such-address is not an error.
			pass
	finally:
		object_lock.release()

#
#
type_map = {}
type_lock = threading.RLock()

def set_queue(object_type, queue_address):
	"""
	"""
	global type_map, type_lock
	try:
		type_lock.acquire()
		try:
			queue = object_map[queue_address[-1]]
		except KeyError:
			return
		type_map[object_type] = queue
	finally:
		type_lock.release()

def get_queue(object_type):
	"""
	"""
	global type_map, type_lock
	assigned_queue = None

	try:
		type_lock.acquire()
		try:
			assigned_queue = type_map[object_type]  # Registered queue.
		except KeyError:
			assigned_queue = type_map[None]
	finally:
		type_lock.release()
	return assigned_queue

def get_queue_address(object_type):
	"""
	"""
	global type_map, type_lock
	assigned_queue = None

	try:
		type_lock.acquire()
		try:
			assigned_queue = type_map[object_type]  # Registered queue.
		except KeyError:
			assigned_queue = type_map[None]
		queue_address = assigned_queue.object_address
	finally:
		type_lock.release()
	return queue_address
