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
""" Dedicated collector for objects.

Objects register themselves with a collector during their start process
and deregister during teardown. Addresses still in the collector at
termination are signaled directly - the collector waits for all objects
to clear themselves.

Originally developed for garbage collection of ProcessObjects.
"""
__docformat__ = 'restructuredtext'

from queue import Queue, Full, Empty
from collections import deque

from .virtual_memory import *
from .message_memory import *
from .virtual_runtime import *
from .point_runtime import *
from .virtual_point import *
from .point_machine import *
from .bind_type import *

__all__ = [
	'AddObject',
	'RemoveObject',
	'ObjectCollector',
]

# Register and deregister.
class AddObject(object):
	def __init__(self, address: Address=None):
		self.address = address or NO_SUCH_ADDRESS

class RemoveObject(object):
	def __init__(self, address: Address=None):
		self.address = address or NO_SUCH_ADDRESS

bind(AddObject)
bind(RemoveObject)

class INITIAL: pass
class READY: pass
class CLEARING: pass

class ObjectCollector(Threaded, StateMachine):
	def __init__(self, grace: float=10.0):
		Threaded.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.grace = grace
		self.collected = set()

def ObjectCollector_INITIAL_Start(self, message):
	return READY

def ObjectCollector_READY_AddObject(self, message):
	self.collected.add(message.address)
	return READY

def ObjectCollector_READY_RemoveObject(self, message):
	self.collected.discard(message.address)
	return READY

def ObjectCollector_READY_Stop(self, message):
	if len(self.collected) < 1:
		self.complete()
	for c in self.collected:
		self.send(message, c)
	self.start(T1, self.grace)
	return CLEARING

def ObjectCollector_CLEARING_AddObject(self, message):
	self.collected.add(message.address)
	self.send(Stop(), message.address)
	return READY

def ObjectCollector_CLEARING_RemoveObject(self, message):
	self.collected.discard(message.address)
	if len(self.collected) < 1:
		self.complete()
	return READY

def ObjectCollector_CLEARING_T1(self, message):
	self.complete()

OBJECT_COLLECTOR_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	READY: (
		(AddObject, RemoveObject, Stop,),
		()
	),
	CLEARING: (
		(AddObject, RemoveObject, T1,),
		()
	),
}

bind(ObjectCollector, OBJECT_COLLECTOR_DISPATCH)
