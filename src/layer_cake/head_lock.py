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

"""Making an exclusive claim for a persisted name.

"""
__docformat__ = 'restructuredtext'

from .virtual_runtime import *
from .virtual_point import *
from .point_runtime import *
from .virtual_memory import *
from .message_memory import *
from .routine_point import *
from .file_object import *
from .bind_type import *

__all__ = [
	'lock_file',
	'unlock_file',
	'LockUp',
	'LockedOut',
	'head_lock',
]

#
#
class LockedOut(object):
	"""Other process already working in same space."""
	def __init__(self, path: str=None, pid: int=None, group_pid: int=None):
		self.path = path
		self.pid = pid
		self.group_pid = group_pid

	def __str__(self):
		if self.path is None or self.pid is None or self.group_pid is None:
			return 'locked out and missing details'
		s = f'locked out of "{self.path}" by <{self.pid}>({self.group_pid})'
		return s

bind_message(LockedOut, copy_before_sending=False)

# Posix based file locking (Linux, Ubuntu, MacOS, etc.)
# Only allows locking on writable files, might cause
# strange results for reading.

try:
	import fcntl
	import os

	def lock_file(f):
		# Will throw OSError if file is not writable
		# or someone else has already locked it.
		fcntl.lockf(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

	def unlock_file(f):
		fcntl.lockf(f.fileno(), fcntl.LOCK_UN)

except ModuleNotFoundError:
	import msvcrt
	import os

	def file_size(f):
		return os.path.getsize(os.path.realpath(f.name))

	def lock_file(f):
		msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, file_size(f))

	def unlock_file(f):
		msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, file_size(f))


# Class for ensuring that all file operations are atomic, treat
# initialization like a standard call to 'open' that happens to be atomic.
# This file opener *must* be used in a "with" block.


class LockUp:
	def __init__(self, path, *args, group_pid=None, **kwargs):
		self.file = open(path, *args, **kwargs)
		lock_file(self.file)
		f = File(path, UserDefined(LockedOut))
		lo = LockedOut()
		lo.path = path
		lo.pid = os.getpid()
		lo.group_pid = group_pid
		f.store(lo)

	def __enter__(self, *args, **kwargs):
		return self.file

	def __exit__(self, exc_type=None, exc_value=None, traceback=None):
		# Flush to make sure all buffered contents are written to file.
		self.file.flush()
		os.fsync(self.file.fileno())

		# Release the lock on the file.
		unlock_file(self.file)
		self.file.close()

		# Handle exceptions that may have come up during execution, by
		# default any exceptions are raised to the user.
		if (exc_type is not None):
			return False
		return True

#
#
def head_lock(self, path, name, group_pid=None):
	lock = os.path.join(path, name)
	try:
		with LockUp(lock, "w", group_pid=group_pid) as k:
			self.send(Ready(), self.parent_address)
			self.select(Stop)
		return None
	except OSError:
		# Address a not needed in completion code.
		f = File(lock, UserDefined(LockedOut))
		lo = f.recover()
		return lo

bind_routine(head_lock)
