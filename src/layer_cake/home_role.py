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
"""Management of the async runtime.

Ensure that the support for async operation is in place when the process
needs it. Ensure that support is cleared out during process termination.
"""
__docformat__ = 'restructuredtext'

import threading
import tempfile
from .general_purpose import *
from .virtual_runtime import *
from .command_line import *
from .folder_object import *

__all__ = [
	'HR',
	'resource',
	'model',
	'tmp',
]

HR = Gas(home_path=None, role_name=None,
	home_role=None,
	edit_role=None,
	temp_dir=None,
	model=None,	tmp=None, resource=None)

# File storage areas for an instance of a process object.
# Specifically deals with both group and solo (CLI) contexts.
# Resource - read-only, persistent, shared by all instances of same executable.
# Model - read-write, persistent, private to each instance.
# Tmp - read-write, empty on start, private.

# Set in create_role(), open_role() and create_memory_role().
def resource():
	return HR.resource

def model():
	return HR.model

# For the CLI context (create_memory_role) the resource member must
# be set (--resource-path) or its null, and the model member is set
# (--model-path) or defaults to '.' (cwd). The tmp member is always null.
# This is a lazy creation of a tmp folder. CLI objects that dont
# make use of a tmp folder never create one.
tmp_lock = threading.RLock()

def tmp():
	with tmp_lock:
		if not HR.tmp:
			# Cleanup in create()
			HR.temp_dir = tempfile.TemporaryDirectory()
			HR.tmp = Folder(HR.temp_dir.name)
	return HR.tmp
