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

"""Any general-purpose class or function that does not belong elsewhere.

"""

__docformat__ = 'restructuredtext'

import os
import sys
import random
from enum import Enum

from .virtual_memory import *
from .convert_memory import *
from .message_memory import *

__all__ = [
	'Gas',
	'breakpath',
	'output_line',
	'short_delta',
	'CreateFrame',
	'spread_out',
]

random.seed()


#
#
class Gas(object):
	"""Build an object from the specified k-v args, suitable as a global context.

	:param kv: map of names and value
	"""
	def __init__(self, **kv):
		"""Convert the named values into object attributes."""
		for k, v in kv.items():
			setattr(self, k, v)

#
#
def breakpath(p):
	"""Break apart the full path into folder, file and extent (3-tuple)."""
	p, f = os.path.split(p)
	name, e = os.path.splitext(f)
	return p, name, e

#
#
def output_line(line, tab=0, newline=True, **kv):
	if kv:
		line = line.format(**kv)

	if tab:
		sys.stdout.write('+   ' * tab)

	sys.stdout.write(line)
	if newline:
		sys.stdout.write('\n')

#
def short_delta(d):
	t = span_to_text(d.total_seconds())
	i = t.find('d')
	if i != -1:
		j = t.find('h')
		if j != -1:
			return t[:j + 1]
		return t[:i + 1]
	i = t.find('h')
	if i != -1:
		j = t.find('m')
		if j != -1:
			return t[:j + 1]
		return t[:i + 1]

	# Minutes or seconds only.
	i = t.find('.')
	if i != -1:
		i += 1
		j = t.find('s')
		if j != -1:
			e = j - i
			e = min(1, e)
			return t[:i + e] + 's'
		return t[:i] + 's'
	return t

#
class CreateFrame(object):
	"""
	Capture values needed for async object creation.

	:param object_type: type to be created
	:type object_type: :ref:`object type<layer-cake-object-type>`
	"""
	def __init__(self, object_type, *args, **kw):
		self.object_type = object_type
		self.args = args
		self.kw = kw

def spread_out(period: float, delta: int=25):
	'''
	Adjust a base value in a random way. Return a float.
	

	:param period: base time period
	:param delta: range of adjustment as percent denominator
	'''
	lo = 100 - delta
	hi = 100 + delta
	cf = random.randrange(lo, hi) / 100
	return period * cf
