# Author: Scott Woods <scott.18.ansar@gmail.com>
# MIT License
#
# Copyright (c) 2017-2023 Scott Woods
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

"""
This module defines the machinery that underpins the timer service
available at `Point.start`. There are three major parts:

- ``Tick``, a class deriving from Message, this is the metronome sent to
  countdown machine.
- ``CountdownTimer``, a class, runs in own thread this object accepts
  StartTimer messsages.
- ``timer_circuit``, a function, runs as custom routine, sends regular
  Ticks to CountdownTimer.
"""
__docformat__ = 'restructuredtext'

from time import sleep, monotonic

from .object_space import *
from .virtual_runtime import *
from .point_runtime import *
from .virtual_point import *
from .message_memory import *
from .routine_point import *
from .point_machine import *

__all__ = [
	'Tick',
	'CountdownTimer',
	'timer_circuit',
]

class Tick(object):
	pass

bind_message(Tick,
	message_trail=False, execution_trace=False, copy_before_sending=False)

# Handling of expression of time values
# and conversion to something that this
# module understands.
TICKS_PER_SECOND	= 4
TIME_QUANTUM		= 100 / TICKS_PER_SECOND
QUANTUM_LESS_1	  = TIME_QUANTUM - 1

class CountdownTimer(Threaded, Stateless):
	"""
	An async object running in its own thread. Available to all `Point`
	objects as pt.timer_address.

	This object accepts StartTimer messages, creating a record of each
	active timer as if there was a (sender_address, timer) unique,
	composite key. The record is initialized with the ticks before
	expiry.

	Ticks are received from the timer_circuit and are used to decrement
	the active record. If this decements to less than 1 the record is
	"expired". The timer message is sent and the record is removed.

	Most timer-related logging is necessarily disabled.
	"""
	def __init__(self):
		Threaded.__init__(self)
		Stateless.__init__(self)
		self.running = []

def CountdownTimer_Start(self, message):
	# Silence the "dropped" message.
	pass

def CountdownTimer_Tick(self, message):
	still_running = []
	now = monotonic()
	for c in self.running:
		if now >= c[4]:			# END OF A PERIOD
			who = c[0]			# Who requested it.
			what = c[1]()		# The timer instance.
			send_a_message(what, who, self.object_address)
			if c[3]:
				c[4] = monotonic() + c[2]
				still_running.append(c)
		else:
			still_running.append(c)

	if len(still_running) != len(self.running):
		self.running = still_running

def CountdownTimer_StartTimer(self, message):
	sender  = self.return_address
	timer   = message.timer
	for c in self.running:
		if c[0] == sender and c[1] == timer:	# An existing timer.
			c[2] = message.seconds				# Redefine its details.
			c[3] = message.repeating
			c[4] = monotonic() + c[2]			# Freshen up that expiry.
			return

	if message.seconds < 0.2:
		send_a_message(message.timer(), sender, self.object_address)
		return

	# A brand new timer block;
	# [0] address of requesting party
	# [1] class, e.g. ar.T1
	# [2] seconds of delay
	# [3] true if a repeating timer
	# [4] the moment of expiry.
	c = [
		sender,				# Who wants it.
		timer,				# Class of the timer.
		message.seconds,
		message.repeating,
		monotonic() + message.seconds
	]
	self.running.append(c)

def CountdownTimer_CancelTimer(self, message):
	return_address = self.return_address
	for i, c in enumerate(self.running):
		if c[0] == return_address and c[1] == message.timer:
			# Ok to modify cos immediate
			# return afterwards?
			self.running.pop(i)
			return

def CountdownTimer_Stop(self, message):
	self.complete()

bind_stateless(CountdownTimer,
	(Start, Tick, StartTimer, CancelTimer, Stop),
	lifecycle=False, message_trail=False,
	execution_trace=False, user_logs=USER_LOG.NONE)

# Control the rate of ticks
BETWEEN_TICKS = 1.0 / TICKS_PER_SECOND

def timer_circuit(queue, timer_address):
		t = Tick()
		while not queue.halted:
			send_a_message(t, timer_address, queue.object_address)
			sleep(BETWEEN_TICKS)
		t = Stop()

bind_routine(timer_circuit,
	lifecycle=False, message_trail=False, execution_trace=False, user_logs=USER_LOG.NONE)
