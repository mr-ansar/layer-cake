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

"""Status and control settings bound to objects and messages.

The flags, enumerations and other values used to control handling
and behaviour and a class to hold this collection of administrative
details.

.. autoclass:: Runtime
"""

__docformat__ = 'restructuredtext'

from enum import Enum

__all__ = [
	'USER_LOG',
	'USER_TAG',
	'tag_to_log',
	'TAG_LOG',
	'Runtime',
	'type_schema',
	'PointConstructionError',
	'PlatformRequirementError',
]

# Logging levels. Moderate the quantity
# of logging by its designated significance.
class USER_LOG(Enum):
	NONE = 100		# No user logs at all.
	FAULT = 6		# A definite problem that will compromise the service.
	WARNING = 5		# Something unexpected that may compromise the service.
	CONSOLE = 4		# An operational milestone worthy of note.
	OBJECT = 3		# Async operation.
	TRACE = 2		# Progress of the service. Suitable for public viewing.
	DEBUG = 1		# Not suitable for customer or support.

# Async operation.
class USER_TAG(Enum):
	CREATED = '+'
	DESTROYED = 'X'	# Provides completion type.
	SENT = '>'	# Type.
	RECEIVED = '<'	# ..
	STARTED = '('	# Sub-process running.
	ENDED = ')'	# Exited.

	# Operational significance.
	FAULT = '!'	# Compromised.
	WARNING = '?'	# May be compromised.
	CONSOLE = '^'	# Application milestone.

	TRACE = '~'	# Technical, networks, files and devices.
	DEBUG = '_'	# Developer, raw.

	SAMPLE = '&'	# Sample of local data.
	CHECK = '='	# Check a condition.

TAG_LOG = {
	USER_TAG.FAULT.value: USER_LOG.FAULT,
	USER_TAG.WARNING.value: USER_LOG.WARNING, USER_TAG.CHECK.value: USER_LOG.WARNING,
	USER_TAG.CONSOLE.value: USER_LOG.CONSOLE,
	USER_TAG.SAMPLE.value: USER_LOG.TRACE,
	USER_TAG.CREATED.value: USER_LOG.OBJECT, USER_TAG.DESTROYED.value: USER_LOG.OBJECT,
	USER_TAG.SENT.value: USER_LOG.OBJECT, USER_TAG.RECEIVED.value: USER_LOG.OBJECT,
	USER_TAG.STARTED.value: USER_LOG.OBJECT, USER_TAG.ENDED.value: USER_LOG.OBJECT,
	USER_TAG.TRACE.value: USER_LOG.TRACE,
	USER_TAG.DEBUG.value: USER_LOG.DEBUG
}

def tag_to_log(tag):
	"""Convert tag to level. Return int."""
	number = TAG_LOG[tag.value]
	return number

class Runtime(object):
	"""Settings to control logging and other behaviour, for objects and messages."""

	def __init__(self,
			name, module,
			lifecycle=True, message_trail=True,
			execution_trace=True,
			copy_before_sending=True,
			not_portable=False,
			user_logs=USER_LOG.DEBUG):
		"""Construct the settings.

		:param name: the name of the class being registered
		:type name: str
		:param module: the name of the module the class is located in
		:type module: str
		:param value: the application value, e.g. a function
		:type value: any
		:param lifecycle: enable logging of created, destroyed
		:type lifecycle: bool
		:param message_trail: enable logging of sent
		:type message_trail: bool
		:param execution_trace: enable logging of received
		:type execution_trace: bool
		:param copy_before_sending: enable auto-copy before send
		:type copy_before_sending: bool
		:param not_portable: prevent inappropriate send
		:type not_portable: bool
		:param user_logs: log level
		:type user_logs: int
		"""
		self.name = name		# Last component of dotted name.
		self.module = module	# Full path up to the name.

		self.lifecycle = lifecycle			  # Create, destroy objects
		self.message_trail = message_trail	  # Sending
		self.execution_trace = execution_trace  # Receiving
		self.copy_before_sending = copy_before_sending
		self.not_portable = not_portable
		self.user_logs = user_logs			  # Object trace, warning...

		self.path = '%s.%s' % (module, name)

def type_schema(p):
	try:
		return p.__art__.schema
	except (TypeError, AttributeError) as e:
		return None

#
#
class PointConstructionError(Exception):
	"""Exception indicating poor construction of an async entity."""

	def __init__(self, identify_and_help):
		"""Construct the exception.

		:param identity_and_help: description of the problem and a suggestion
		:type name: str
		"""
		Exception.__init__(self, identify_and_help)

#
#
class PlatformRequirementError(Exception):
	"""Exception indicating that the underlying platform is not meeting its end of the deal."""

	def __init__(self, identify_and_help):
		"""Construct the exception.

		:param identity_and_help: the problem and a suggestion
		:type name: str
		"""
		Exception.__init__(self, identify_and_help)
