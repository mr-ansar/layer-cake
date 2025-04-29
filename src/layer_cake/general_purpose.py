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
import random
from enum import Enum

from .virtual_memory import *
from .message_memory import *

__all__ = [
	'Gas',
	'breakpath',
	'CreateFrame',
	'spread_out',
]

random.seed()


#
#
class Gas(object):
	"""Build an object from the specified k-v args, suitable as a global context.

	:param kv: map of names and value
	:type path: dict
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
class CreateFrame(object):
	"""Capture values needed for async object creation.

	:param object_type: type to be created
	:type object_type: function or Point-based class
	:param args: positional parameters
	:type args: tuple
	:param kw: named parameters
	:type kw: dict
	"""
	def __init__(self, object_type, *args, **kw):
		self.object_type = object_type
		self.args = args
		self.kw = kw

def spread_out(period, delta=25):
	'''Adjust a base value in a random way. Return a float.'''
	lo = 100 - delta
	hi = 100 + delta
	cf = random.randrange(lo, hi) / 100
	return period * cf
