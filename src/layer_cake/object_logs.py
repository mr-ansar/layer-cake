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
"""Logging methods available within the async runtime.

"""
__docformat__ = 'restructuredtext'

import os
import sys
import time

__all__ = [
	'PID',
	'log_to_nowhere',
	'log_to_stderr',
	'select_logs',
]

# Some essential logging options.
PID = os.getpid()

def log_to_nowhere(log):
	pass

def log_to_stderr(log):
	second = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(log.stamp))
	fraction = '%.3f' % (log.stamp,)
	fraction = fraction[-3:]
	mark = '%s.%s' % (second, fraction)
	name = log.name.split('.')[-1]
	state = log.state
	if state is None:
		p = '[%08d] %s %s <%08x>%s - %s\n' % (PID, mark, log.tag.value, log.address[-1], name, log.text)
	else:
		p = '[%08d] %s %s <%08x>%s[%s] - %s\n' % (PID, mark, log.tag.value, log.address[-1], name, state, log.text)
	sys.stderr.write(p)
	sys.stderr.flush()

def select_logs(tag):
	def log_by_number(log):
		if tag.value > log.tag.value:
			return
		log_to_stderr(log)
	return log_by_number
