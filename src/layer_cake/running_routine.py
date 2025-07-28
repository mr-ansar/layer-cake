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

"""Running a function within its own thread.

"""
__docformat__ = 'restructuredtext'

import threading
import queue

from .virtual_memory import *
from .convert_memory import *
from .virtual_runtime import *
from .point_runtime import *
from .object_space import *

__all__ = [
	'start_a_thread',
	'running_in_thread',
]

#
#
def start_a_thread(queue, routine, args, kw_args):
	"""
	Start a platfrom thread that runs the given custom routine on the
	given queue. No return.

	This is the first part of arranging a function to run in its own
	dedicated thread, with its own unique id and a `self` parameter it
	can use to interact with the rest of the world. See
	`running_in_thread` for the second part.

	It is an error to call this function directly from an application.
	Instead this is a function that is called from ``Point`` methods
	such as ``custom_routine`` and ``object_and_thread``. An
	application that makes direct calls to this function will
	enjoy undefined behaviour.

	Parameters:

	- `queue`: an async object, a Queue-based machine or Channel.
	- `routine`: a plain, old function, the code that will execute
	within the new thread.
	- `args`: tuple of values, the args forwarded on to the routine(...)
	call.
	- `kw_args`: dict of named values, the named args forwarded on to the
	routine(...) call.

	Returns:

	Nothing.
	"""
	queue.thread_function = routine
	queue.assigned_thread = threading.Thread(target=running_in_thread, args=(routine, queue, args, kw_args))
	queue.assigned_thread.daemon = True
	queue.assigned_thread.start()

def running_in_thread(routine, queue, args, kw_args):
	"""
	First code to run inside new thread. Set up some Ansar
	admin information before passing control to the true
	tenant of this thread, i.e. the custom routine.

	Also serves as the wrapper for management of termination mechanisms.

	Parameters:

	- `routine`: a plain, old function, the code to be called.
	- `queue`: an async object, a Queue-based machine or Channel that
	becomes `self`.
	- `args`: tuple of values, the args forwarded on to the routine(...)
	call.
	- `kw_args`: dict of named values, the named args forwarded on to the
	routine(...) call.

	Returns:

	Nothing.
	"""
	address = queue.object_address
	parent = queue.parent_address

	value = None
	# Need to catch all exits from this application-provided
	# code, to help maintain integrity of object map. But also
	# need to allow system exceptions pass through.
	try:
		message = routine(queue, *args, **kw_args)
	# Necessary replication of exceptions in
	# object_dispatch.
	except KeyboardInterrupt:
		s = 'unexpected keyboard interrrupt'
		queue.fault(s)
		message = Faulted('object compromised', s)
	except SystemExit:
		s = 'unexpected system exit'
		queue.fault(s)
		message = Faulted('object compromised', s)
	except Completion as c:
		# From run_object (threads dedicated to machines), object_dispatch (e.g. class
		# threads) and all custom routines.
		message = c.message
	except Exception as e:
		s = str(e)
		s = f'unhandled exception ({s})'
		queue.fault(s)
		message = Faulted('object faulted', s)
	except:
		s = 'unhandled opaque exception'
		queue.fault(s)
		message = Faulted('object faulted', s)

	if queue.__art__.lifecycle:
		queue.log(USER_TAG.DESTROYED, 'Destroyed')

	return_type = routine.__art__.return_type
	if return_type is None:
		pass
	elif isinstance(return_type, Any):
		pass
	elif isinstance(return_type, Portable):
		if not hasattr(message, '__art__'):
			message = (message, return_type)
	else:
		message = Faulted(f'unexpected return type for routine "{routine.__name__}"')

	ending = queue.object_ending
	destroy_an_object(address)
	ending(message, parent, address)
