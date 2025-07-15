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
	'resource_folder',
	'model_folder',
	'tmp_folder',
	'resource_path',
	'model_path',
	'tmp_path',
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
def resource_folder():
	"""Application access to the shared, per-executable file space. Return a folder.

	Static, read-only file data associated with the running executable. This is
	intended to be the folder managed by the :ref:`resource<layer-cake-command-reference-resource>`
	command but may be explicitly set on the command-line using ``--resource-path``, or it
	is ``None``.

	:rtype: Folder
	"""
	return HR.resource

def model_folder():
	"""Application access to the operational, per-role file space. Return a folder.

	Private, persistent, read-write file data associated with the operational role. This is
	intended to be the folder managed by the :ref:`model<layer-cake-command-reference-model>`
	command but may be explicitly set on the command-line using ``--model-path``, or it
	is the current working folder.

	:rtype: Folder
	"""
	return HR.model

tmp_lock = threading.RLock()

def tmp_folder():
	"""Application access to the transient, per-role file space. Return a folder.

	Private, transient, read-write file data associated with the operational *role*. This is
	a space arranged by the framework, where temporary files can be freely added, modified
	and deleted. It is part of the *home* folder hierarchy, or - when the process is running
	from the command-line - it is a folder created within the folders managed by the host
	platform. The folder is guaranteed to be empty at the startup of every application.

	:rtype: Folder
	"""
	with tmp_lock:
		if not HR.tmp:
			# Cleanup in create()
			HR.temp_dir = tempfile.TemporaryDirectory()
			HR.tmp = Folder(HR.temp_dir.name)
	return HR.tmp

def resource_path():
	"""Application access to the shared, per-executable file space. Return the path or None.

	:rtype: str
	"""
	f = resource_folder()
	if isinstance(f, Folder):
		return f.path
	return None

def model_path():
	"""Application access to the operational, per-role file space. Return the path.

	:rtype: str
	"""
	f = model_folder()
	if isinstance(f, Folder):
		return f.path
	return None

def tmp_path():
	"""Application access to the transient, per-role file space. Return the path.

	:rtype: str
	"""
	f = tmp_folder()
	if isinstance(f, Folder):
		return f.path
	return None
