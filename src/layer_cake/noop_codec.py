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

"""Implementation of a passthru codec.

"""

__docformat__ = 'restructuredtext'

from .virtual_memory import *
from .convert_memory import *
from .virtual_runtime import *
from .message_memory import *
from .virtual_codec import *


__all__ = [
	'word_to_noop',
	'noop_to_word',
	'CodecNoop'
]

def word_to_noop(c, w):
	return w

def noop_to_word(c, s):
	return s

class CodecNoop(Codec):
	EXTENSION = 'noop'

	def __init__(self, return_proxy=None, local_termination=None, pretty_format=False, decorate_names=True):
		Codec.__init__(self,
			CodecNoop.EXTENSION,
			word_to_noop,
			noop_to_word,
			return_proxy, local_termination, pretty_format, decorate_names)
