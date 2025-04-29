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
"""Derive the proper signal handling for the current host.

"""
__docformat__ = 'restructuredtext'

import os
import platform
import signal
from .virtual_runtime import *
from .general_purpose import *
from .command_line import *
from .object_runtime import *

__all__ = [
	'PS',
]

# Construct platform-independent materials here. This is
# intentionally low ambition. Test rigs for multi-os dev
# just not practical.
# Slightly confusing set of criteria available. Save them
# all for diagnostic but base operation on one.
def catch_interrupt(number, frame):
	PS.signal_received = number

def interrupt_alias(number, frame):
	root = start_up(None)
	root.log(USER_TAG.TRACE, f'Accepting signal {number} as SIGINT alias')
	PS.signal_received = signal.SIGINT

def ignore_signal(number, frame):
	pass

def log_signal(number, frame):
	root = start_up(None)
	# Skip the filtering.
	root.log(USER_TAG.WARNING, 'Unexpected signal {number}'.format(number=number))

system = platform.system()

#
PS = Gas(os_name=os.name,
	platform_release=platform.release(),
	platform_system=system,
	platform_signal=None,
	platform_kill=None,
	signal_received=None)

if system.startswith('Linux'):
	def platform_signal():
		signal.signal(signal.SIGINT, catch_interrupt)
		signal.signal(signal.SIGQUIT, interrupt_alias)
		signal.signal(signal.SIGHUP, interrupt_alias)
		signal.signal(signal.SIGTERM, interrupt_alias)

		signal.signal(signal.SIGCHLD, ignore_signal)
		signal.signal(signal.SIGTRAP, log_signal)
		signal.signal(signal.SIGABRT, log_signal)
		#signal.signal(signal.SIGKILL, log_signal)	... cant be caught.

		signal.signal(signal.SIGPIPE, log_signal)
		signal.signal(signal.SIGUSR1, catch_interrupt)
		signal.signal(signal.SIGUSR2, catch_interrupt)
		signal.signal(signal.SIGALRM, log_signal)
		signal.signal(signal.SIGTTIN, log_signal)
		#signal.signal(signal.SIGSTOP, log_signal)	... ditto.
		signal.signal(signal.SIGTSTP, log_signal)
		signal.signal(signal.SIGPWR, log_signal)
	PS.platform_kill = signal.SIGKILL
	PS.platform_signal = platform_signal
elif system == 'Darwin':
	def platform_signal():
		signal.signal(signal.SIGINT, catch_interrupt)
		signal.signal(signal.SIGQUIT, interrupt_alias)
		signal.signal(signal.SIGHUP, interrupt_alias)
		signal.signal(signal.SIGTERM, interrupt_alias)

		signal.signal(signal.SIGCHLD, ignore_signal)
		signal.signal(signal.SIGTRAP, log_signal)
		signal.signal(signal.SIGABRT, log_signal)
		#signal.signal(signal.SIGKILL, log_signal)	... cant be caught.

		signal.signal(signal.SIGPIPE, log_signal)
		signal.signal(signal.SIGUSR1, catch_interrupt)
		signal.signal(signal.SIGUSR2, catch_interrupt)
		signal.signal(signal.SIGALRM, log_signal)
		signal.signal(signal.SIGTTIN, log_signal)
		#signal.signal(signal.SIGSTOP, log_signal)	... ditto.
		signal.signal(signal.SIGTSTP, log_signal)
		#signal.signal(signal.SIGPWR, log_signal)
	PS.platform_kill = signal.SIGKILL
	PS.platform_signal = platform_signal
elif system == 'Windows':
	def platform_signal():
		signal.signal(signal.SIGINT, catch_interrupt)
		# Available but unusable. Result in termination of process.
		#signal.signal(signal.SIGTERM, interrupt_alias)
		#signal.signal(signal.SIGABRT, log_signal)
	PS.platform_kill = signal.SIGBREAK
	PS.platform_signal = platform_signal
else:
	pass
