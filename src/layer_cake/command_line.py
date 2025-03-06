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
from .virtual_memory import *
from .message_memory import *
from .virtual_runtime import *

__all__ = [
	'CommandLine',
	'CL',
]

#
class CommandLine(object):
	"""Capture the details of creating a process from an executable file.

	These are the values used to implement integration between parent and child
	processes. There are also values that are useful at the command-line, e.g.
	debug_level and help.

	:param background_daemon: enable full parent-child process integration
	:type background_daemon: bool
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
	:param help: enable output of help page
	:type help: bool
	:param create_settings: save the specified settings
	:type create_settings: bool
	:param update_settings: add/override the specified settings
	:type update_settings: bool
	:param dump_settings: enable output of current settings
	:type dump_settings: bool
	:param edit_settings: enable visual editing of the current settings
	:type edit_settings: bool
	:param factory_reset: discard stored settings
	:type factory_reset: bool
	:param settings_file: use the settings in the specified file
	:type settings_file: str
	:param output_file: place any output in the specified file
	:type output_file: str
	:param group_id: process id of the parent
	:type group_id: int
	:param group_listen: ephemeral port opened by the parent
	:type group_listen: int
	"""
	def __init__(self,
			background_daemon: bool=False,
			child_process: bool=False,
			full_output: bool=False,
			debug_level=None,
			home_path: str=None, role_name: str=None,
			help: bool=False,
			create_settings: bool=False, update_settings: bool=False,
			factory_reset: bool=False,
			dump_settings: bool=False,
			edit_settings: bool=False,
			settings_file: str=None, output_file: str=None,
			keep_logs: bool=False,
			group_pid: int=None, group_listen: int=None):
		self.background_daemon = background_daemon
		self.child_process = child_process
		self.full_output = full_output
		self.debug_level = debug_level
		self.home_path = home_path
		self.role_name = role_name
		self.help = help
		self.create_settings = create_settings
		self.update_settings = update_settings
		self.factory_reset = factory_reset
		self.dump_settings = dump_settings
		self.edit_settings = edit_settings
		self.settings_file = settings_file
		self.output_file = output_file
		self.keep_logs = keep_logs
		self.group_pid = group_pid
		self.group_listen = group_listen

bind_message(CommandLine,
	debug_level=Enumeration(USER_LOG),
)

CL = CommandLine()

def command_line_start():
	return not CL.background_daemon and not CL.child_process
