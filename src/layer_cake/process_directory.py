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
"""The directory built in to every process. Default is inactive.

.
"""
__docformat__ = 'restructuredtext'

from enum import Enum
from collections import deque

from .general_purpose import *
from .point_runtime import *
from .virtual_point import *
from .object_runtime import *
from .object_directory import *

__all__ = [
	'PD',
	'publish',
	'subscribe',
]

PD = Gas(directory=None)

# Managed creation of the builtin directory.
def create_directory(root):
	PD.directory = root.create(ObjectDirectory)
	x = 1

def stop_directory(root):
	root.send(Stop(), PD.directory)
	root.select()

AddOn(create_directory, stop_directory)

#
def publish(self, name):
	p = PublishAsName(name, self.object_address)
	self.send(p, PD.directory)

def subscribe(self, name):
	p = SubscribeToName(name, self.object_address)
	self.send(p, PD.directory)
