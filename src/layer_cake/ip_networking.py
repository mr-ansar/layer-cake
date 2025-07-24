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

""".

"""
__docformat__ = 'restructuredtext'

import re
from enum import Enum

from .virtual_memory import *
from .message_memory import *

__all__ = [
	'LOCAL_HOST',
	'HostPort',
	'equal_ipp',
	'LocalPort',
	'ScopeOfHost',
	'local_private_other',
]

#
LOCAL_HOST = '127.0.0.1'

class HostPort(object):
	"""Combination of an IP address or name, and a port number.

	:param host: IP address or name
	:param port: network port
	"""
	def __init__(self, host: str=None, port: int=None):
		self.host = host
		self.port = port

	def __str__(self):
		return f'{self.host}:{self.port}'

	def inet(self):
		return (self.host, self.port)

def equal_ipp(lhs, rhs):
	return lhs.host == rhs.host and lhs.port == rhs.port

class LocalPort(HostPort):
	def __init__(self, port: int=None):
		HostPort.__init__(self, LOCAL_HOST, port)

bind_message(HostPort)
bind_message(LocalPort, host=Unicode())

#
#
DOTTED_IP = re.compile(r'(\d+)\.(\d+)\.(\d+)\.(\d+)')

class ScopeOfHost(Enum):
	LOCAL=1
	PRIVATE=2
	OTHER=3

def local_private_other(ip):
	if ip is None:
		return ScopeOfHost.OTHER
	m = DOTTED_IP.match(ip)
	if m is None:
		return ScopeOfHost.OTHER
	# Have complete verification of dotted layout
	b0 = int(m.groups()[0])
	b1 = int(m.groups()[1])

	# Not dotted -------- None
	# 127.x.x.x --------- 0, localhost
	# 10.x.x.x ---------- 1, private
	# 192.168.x.x ------- 1, private
	# 172.[16-31].x.x --- 1, private
	# else -------------- 2, public

	if b0 == 127:
		return ScopeOfHost.LOCAL
	elif b0 == 10:
		return ScopeOfHost.PRIVATE
	elif b0 == 192 and b1 == 168:
		return ScopeOfHost.PRIVATE
	elif b0 == 172 and (b1 > 15 and b1 < 32):
		return ScopeOfHost.PRIVATE
	return ScopeOfHost.OTHER
