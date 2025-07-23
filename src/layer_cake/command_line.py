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
"""Capture the standard information from the command line.

An object that defines the values that may be gathered from sys.argv during
standard processing of the command line.
"""
__docformat__ = 'restructuredtext'

from enum import Enum
from .ip_networking import *
from .virtual_memory import *
from .message_memory import *
from .virtual_runtime import *

__all__ = [
	'ScopeOfDirectory',
	'ProcessOrigin',
	'CommandLine',
	'CL',
]

# Register service or interest in service.
class ScopeOfDirectory(Enum):
	"""
	Enumeration of the scopes within the layer cake directory.

	* LAN - local area network
	* HOST - networking limited to 127.0.0.0
	* GROUP - a composite process
	* PROCESS - a single process
	* LIBRARY - dynamically loaded process
	"""
	WAN=1
	LAN=2
	HOST=3
	GROUP=4
	PROCESS=5
	LIBRARY=6

class ProcessOrigin(Enum):
	"""
	Enumeration of context in the chain of processes.

	* SHELL - running from the command-line
	* RUN - run an entry in a composite process
	* RUN_CHILD - run as a subprocess of a composite entry
	* START - background run, entry in a composite process
	* START_CHILD - background run, subprocess of a composite entry
	"""
	RUN=1
	RUN_CHILD=2
	START=3
	START_CHILD=4

#
class CommandLine(object):
	"""
	Standard instructions to a new process.

	Communicate the context for the new process, e.g. daemon, home/role,
	settings and parent/child communications.

	:param origin: position in the process/sub-process chain
	:type origin: ProcessOrigin
	:param child_process: this process is a standard child of a standard parent
	:type child_process: bool
	:param full_output: enable full parent-child process integration
	:type full_output: bool
	:param debug_level: select the level of logs to display
	:type debug_level: enum
	:param home_path: location of the process group
	:type home_path: str
	:param role_name: role within a process group
	:type role_name: str
	:param resource_path: override the location of per-executable, read-only resources
	:type resource_path: str
	:param model_path: override the location of per-instance read-write materials
	:type model_path: str
	:param help: enable output of help page
	:type help: bool
	:param create_role: save the specified settings
	:type create_role: bool
	:param update_role: add/override the specified settings
	:type update_role: bool
	:param dump_role: enable output of current settings
	:type dump_role: bool
	:param edit_role: enable visual editing of the current settings
	:type edit_role: bool
	:param factory_reset: discard stored settings
	:type factory_reset: bool
	:param delete_role: remove persisted settings
	:type delete_role: bool
	:param role_file: use the settings in the specified file
	:type role_file: str
	:param dump_types: enable output of type table
	:type dump_types: bool
	:param output_file: place any output in the specified file
	:type output_file: str
	:param directory_scope: scope of this process
	:type directory_scope: ScopeOfDirectory
	:param connect_to_directory: IP and port of parent directory
	:type connect_to_directory: HostPort
	:param encrypted_process: enable encryption of connection to parent directory
	:type encrypted_process: bool
	:param accept_directories_at: IP and port where child directories are accepted
	:type accept_directories_at: HostPort
	"""
	def __init__(self,
			origin: ProcessOrigin=None,
			child_process: bool=False,
			full_output: bool=False,
			debug_level=None,
			home_path: str=None, role_name: str=None,
			resource_path: str=None, model_path: str=None,
			help: bool=False,
			create_role: bool=False, update_role: bool=False,
			factory_reset: bool=False,
			dump_role: bool=False,
			edit_role: bool=False,
			delete_role: bool=False,
			role_file: str=None,
			dump_types: bool=False,
			output_file: str=None,
			keep_logs: bool=False,
			directory_scope: ScopeOfDirectory=None,
			connect_to_directory: HostPort=None,
			accept_directories_at: HostPort=None,
			encrypted_process: bool=False):
		self.origin = origin
		self.child_process = child_process
		self.full_output = full_output
		self.debug_level = debug_level
		self.home_path = home_path
		self.role_name = role_name
		self.resource_path = resource_path
		self.model_path = model_path
		self.help = help
		self.create_role = create_role
		self.update_role = update_role
		self.factory_reset = factory_reset
		self.dump_role = dump_role
		self.edit_role = edit_role
		self.delete_role = delete_role
		self.role_file = role_file
		self.dump_types = dump_types
		self.output_file = output_file
		self.keep_logs = keep_logs
		self.directory_scope = directory_scope or ScopeOfDirectory.PROCESS
		self.connect_to_directory = connect_to_directory or HostPort()
		self.accept_directories_at = accept_directories_at or HostPort()
		self.encrypted_process = encrypted_process

bind_message(CommandLine,
	debug_level=Enumeration(USER_LOG),
)

CL = CommandLine()
