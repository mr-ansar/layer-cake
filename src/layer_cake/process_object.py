# Author: Scott Woods <scott.18.ansar@gmail.com>
# MIT License
#
# Copyright (c) 2017-2023 Scott Woods
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

"""Platform processes as objects.

The ProcessObject machine creates and manages a platform process. Arguments
are passed to the new process and a value extracted from standard output is
repurposed as the return value.

If an API is defined for the object, a listen port is provided to the new
process as an argument and the framework arranges for a connection from the
ProcessObject to the object created inside the sub-process (see publish() and
subscribe()).
"""
__docformat__ = 'restructuredtext'

import sys
import os
import signal
import shutil
from subprocess import Popen, PIPE
from collections import deque

from .general_purpose import *
from .virtual_memory import *
from .convert_memory import *
from .message_memory import *
from .convert_signature import *
from .convert_type import *
from .virtual_runtime import *
from .virtual_point import *
from .point_runtime import *
from .routine_point import *
from .virtual_codec import *
from .json_codec import *
from .noop_codec import *
from .point_machine import *
from .object_runtime import *
from .command_line import *
from .command_startup import *
from .object_startup import *
from .home_role import *
from .bind_type import *
from .object_collector import *
from .object_directory import *
from .process_directory import *
from .ip_networking import *
from .get_response import *

__all__ = [
	'ProcessObject',
	'Utility'
]

PO = Gas(collector=None)

# Managed creation of processes.
def create_processes(root):
	PO.collector = root.create(ObjectCollector)

def stop_processes(root):
	root.send(Stop(), PO.collector)
	root.select()

AddOn(create_processes, stop_processes)

# A thread dedicated to the blocking task of
# waiting for termination of a process.
class CodePage(object):
	def __init__(self, code: int=None, page: str=None):
		self.code = code
		self.page = page

bind(CodePage)

def wait(self, p, piping):
	if piping:
		out, err = p.communicate()
		return CodePage(p.returncode, out)
	else:
		code = p.wait()
		return CodePage(code, None)

bind(wait)

# The ProcessObject class
# A platform process that accepts a set of fully-typed arguments
# and returns a fully-typed result.
class INITIAL: pass
class PENDING: pass
class EXECUTING: pass
class CLEARING: pass
class SPOOLING: pass

# Control over the family of processes that can result from the initiation
# of a single one. This was quite difficult to get right and requires the
# proper use of a ProcessObject object (paramters origin and debug) to preserve
# the correct behaviour from one component to the next.

class ProcessObject(Point, StateMachine):
	"""
	An async proxy object that starts and manages a platform sub-process.

	:param object_or_name: object to run as a process or the executable file name
	:type object_or_name: :ref:`object type<lc-object-type>` or str
	:param args: positional arguments to be passed to the process
	:param origin: processing context
	:param home_path: location of a composite process
	:param role_name: name within the composite process
	:param top_role: enable top-level behaviour
	:param object_api: enable private library behaviour for named process (str)
	:param extra_types: force loading of library types
	:param remainder_args: forward unknown command-line args to process
	:param settings: named arguments to be encoded for the process
	"""
	def __init__(self, object_or_name, *args, origin: ProcessOrigin=None,
			home_path: str=None, role_name: str=None, top_role: bool=False,
			object_api: list=None, extra_types: list=None,
			remainder_args: list=None, **settings):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.args = args
		self.object_or_name = object_or_name
		self.origin = origin
		self.home_path = home_path
		self.role_name = role_name
		self.top_role = top_role
		self.object_api = object_api
		self.extra_types = extra_types
		self.remainder_args = remainder_args
		self.settings = settings

		self.module_path = None
		self.script_path = None
		self.origin_path = None
		self.api = None
		self.listening_for_directories = None
		self.p = None

		self.published = None
		self.subscribed = None
		self.queue = deque()

	def load_image(self, rt):
		# Start the new process.
		# Derive the home/role context using the globals defined for
		# this process, plus the values describing the new process.

		if self.origin:
			origin = self.origin
		else:
			origin = CL.origin
			if origin in (ProcessOrigin.RUN, ProcessOrigin.RUN_CHILD):
				origin = ProcessOrigin.RUN_CHILD
			elif origin in (ProcessOrigin.START, ProcessOrigin.START_CHILD):
				origin = ProcessOrigin.START_CHILD

		self.role_name = self.role_name or breakpath(self.module_path)[1]
		self.home_path = self.home_path or CL.home_path
		if CL.role_name and not self.top_role:
			self.role_name = f'{CL.role_name}.{self.role_name}'

		s = os.path.splitext(self.module_path)
		dot_py = s[1] and s[1] == '.py'

		# Build the command line.
		command = []
		if dot_py:
			interpreter = sys.executable
			command.append(interpreter)
		command.append(self.module_path)

		if self.args:
			for a in self.args:
				command.append(str(a))

		if self.remainder_args:
			command.extend(remaining_arguments(self.remainder_args))

		try:
			c = CodecNoop()
			if self.listening_for_directories:
				e = self.settings.get('encrypted_process', None)
				encrypted_process = e == True

				v = encode_argument(c, self.listening_for_directories, UserDefined(HostPort))
				b = encode_argument(c, encrypted_process, Boolean())
				command.append(f'--directory-scope=LIBRARY')
				command.append(f'--connect-to-directory={v}')
				command.append(f'--encrypted-process={b}')

				subscribe(self, self.role_name, scope=ScopeOfDirectory.PROCESS)

			# Generate the proper argument strings.
			if rt:
				schema = rt.schema | CommandLine.__art__.schema
			else:
				schema = CommandLine.__art__.schema

			for k, v in self.settings.items():
				if v is None:
					continue
				name = k
				e = schema.get(k, None)
				if e:
					k = k.replace('_', '-')
					v = encode_argument(c, v, e)
				else:
					v = str(v)
				command.append(f'--{k}={v}')
		except CodecError as e:
			e = str(e)
			s = e.replace('cannot encode', f'cannot encode value for argument "{name}", {self.module_path}')
			self.complete(Faulted(s))

		if origin:
			command.append(f'--origin={origin.name}')

		command.append(f'--child-process')
		command.append(f'--full-output')

		if self.home_path:
			command.append(f'--home-path={self.home_path}')
		command.append(f'--role-name={self.role_name}')

		if CL.debug_level is not None and origin not in (ProcessOrigin.START, ProcessOrigin.START_CHILD):
			command.append(f'--debug-level={CL.debug_level.name}')

		if CL.keep_logs:
			command.append(f'--keep-logs')


		if self.script_path or self.origin_path:
			environ = os.environ.copy()
			existing_path = environ.get('PYTHONPATH', None)

			path = []
			if self.script_path:
				path.append(self.script_path)
			if self.origin_path:
				path.append(self.origin_path)
			if existing_path:
				path.append(existing_path)

			python_path = ':'.join(path)
			environ['PYTHONPATH'] = python_path
		else:
			environ = None

		c = ' '.join(command)
		self.console(c)
		try:
			start_new_session = CL.child_process
			self.p = Popen(command,
				#start_new_session=start_new_session,
				stdin=None, stdout=PIPE, stderr=sys.stderr,
				text=True, encoding='utf-8', errors='strict',
				env=environ)
				#**self.kw)
		except OSError as e:
			s = f'cannot start process "{self.module_path}" ({e})'
			self.complete(Faulted(s))

		self.log(USER_TAG.STARTED, f'Started process ({self.p.pid})')
		self.create(wait, self.p, True)

		# Good to go. Next event should be Returned.
		self.send(AddObject(self.object_address), PO.collector)

def find_module(name_py):
	if CL.home_path and CL.role_name:
		# Deployed script.
		candidate = os.path.join(CL.home_path, 'script', name_py)
		if os.path.isfile(candidate):
			return candidate

		# Common ancestry.
		home_role = os.path.join(CL.home_path, CL.role_name)
		resource_path = os.path.join(CL.home_path, 'resource')
		role = open_role(home_role, resource_path)
		if role:
			executable_file = role.executable_file()
			split = os.path.split(executable_file)
			if split[0]:
				candidate = os.path.join(split[0], name_py)
				if os.path.isfile(candidate):
					return candidate

	cwd = os.getcwd()
	candidate = os.path.join(cwd, name_py)
	if os.path.isfile(candidate):
		return candidate

	return None

def find_role(executable_file, home_path):
	script_path = os.path.join(home_path, 'script')

	split = os.path.split(executable_file)
	candidate = os.path.join(script_path, split[1])
	if os.path.isfile(candidate):
		return candidate

	if os.path.isfile(executable_file):
		return executable_file

	return None

def ProcessObject_INITIAL_Start(self, message):
	# Either its a module name, e.g. "test_directory", or its a function/machine
	# to be executed.
	rt = None
	if isinstance(self.object_or_name, str):
		s = os.path.splitext(self.object_or_name)
		if not s[1]:
			self.module_path = shutil.which(s[0])
		elif s[1] == '.py':
			self.module_path = find_module(self.object_or_name)
		else:
			self.complete(Faulted(f'cannot execute {self.object_or_name} (unknown extension?)'))

		if self.module_path is None:
			self.complete(Faulted(f'cannot execute {self.object_or_name} (not found)'))

		if self.object_api is not None and len(self.object_api) > 0:
			self.api = self.object_api
			self.send(Enquiry(), PD.directory)
			return PENDING

	elif isinstance(self.object_or_name, HomeRole):
		executable_file = self.object_or_name.executable_file()
		if not self.home_path:
			self.complete(Faulted(f'cannot execute {executable_file} (no home_path)'))

		self.module_path = find_role(executable_file, self.home_path)
		if self.module_path is None:
			self.complete(Faulted(f'cannot execute {executable_file} (no role script)'))

		split = os.path.split(executable_file)
		origin_path = split[0]
		script_path = os.path.join(self.home_path, 'script')
		if os.path.isdir(origin_path):
			self.origin_path = origin_path
		if os.path.isdir(script_path):
			self.script_path = script_path

	else:
		rt = getattr(self.object_or_name, '__art__', None)
		if rt is None:
			self.complete(Faulted(f'cannot execute {self.object_or_name} (not registered)'))

		imported_module = self.object_or_name.__module__
		module = sys.modules[imported_module]
		self.module_path = module.__file__

		if rt.api is not None and len(rt.api) > 0:
			self.api = rt.api
			self.send(Enquiry(), PD.directory)
			return PENDING

	self.load_image(rt)
	return EXECUTING

def ProcessObject_PENDING_Unknown(self, message):
	message = cast_to(message, self.received_type)
	q = (message, self.return_address)
	self.queue.append(q)
	return PENDING

def ProcessObject_PENDING_HostPort(self, message):
	self.listening_for_directories = message
	rt = getattr(self.object_or_name, '__art__', None)
	self.load_image(rt)
	return EXECUTING

def ProcessObject_EXECUTING_Available(self, message):
	self.published = self.return_address
	for q in self.queue:
		self.forward(q[0], self.published, q[1])
	self.queue = deque()
	return EXECUTING

def ProcessObject_EXECUTING_Subscribed(self, message):
	self.subscribed = message
	return EXECUTING

def ProcessObject_EXECUTING_Unknown(self, message):
	if self.published is None:
		message = cast_to(message, self.received_type)
		q = (message, self.return_address)
		self.queue.append(q)
		return EXECUTING
	self.forward(message, self.published, self.return_address)
	return EXECUTING

def ProcessObject_EXECUTING_Returned(self, message):
	if self.subscribed:
		clear_subscribed(self, self.subscribed)
	self.send(RemoveObject(self.object_address), PO.collector)

	# Wait thread has returned
	# Forward the result.
	code, page = message.value.code, message.value.page

	self.log(USER_TAG.ENDED, f'Process ({self.p.pid}) ended with {code}')

	if not page:
		output = None
	else:
		encoding = CodecJson()
		try:
			output = encoding.decode(page, Any())
		except CodecError as e:
			s = str(e)
			self.complete(Faulted(f'cannot decode output ({s}) not a standard executable?'))

	# If 0 then everything working according to plans. Also
	# catch the case where the framework sets a special non-zero
	# exit status for faults in CLI scenarios.
	if code == 0 or (code == FAULTY_EXIT and isinstance(output, Faulted)):
		self.complete(output)

	# This is outside normal framework operation.
	t = '<empty>' if output is None else output.__class__.__name__
	p = '<empty>' if len(page) < 1 else page[:32]
	self.complete(Faulted(f'non-standard process exit - code={code}, output={t}, page="{p}..."'))

def ProcessObject_EXECUTING_Stop(self, message):
	pid = self.p.pid
	try:
		os.kill(pid, signal.SIGINT)
	except OSError as e:
		self.complete(Faulted(f'cannot relay local Stop to "{pid}" as SIGINT'))
	return CLEARING

def ProcessObject_CLEARING_Stop(self, message):
	# Additional redundant hint. Ignored.
	return CLEARING

def ProcessObject_CLEARING_Returned(self, message):
	if self.subscribed:
		clear_subscribed(self, self.subscribed)
	self.send(RemoveObject(self.object_address), PO.collector)

	# Wait thread has returned
	# Forward the result.
	code, page = message.value.code, message.value.page

	self.log(USER_TAG.ENDED, f'Process aborted [{self.p.pid}] (code {code})')
	self.complete(Aborted())

PROCESS_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	PENDING: (
		(HostPort, Unknown),
		()
	),
	EXECUTING: (
		(Available, Subscribed, Unknown, Returned, Stop),
		()
	),
	CLEARING: (
		(Returned, Stop),
		()
	),
}

bind_statemachine(ProcessObject, PROCESS_DISPATCH, thread='process-object')

#
#
class Punctuation(object):
	"""A collection of strings for custom decoration of a command line.

	:param dash: string to place before a short-form flag
	:type dash: str
	:param double_dash: string to place before a long-form name
	:type double_dash: str
	:param list_ends: left-end and right-end characters bounding a list
	:type list_ends: str, len of 2
	:param list_separator: string to place between list elements
	:type list_separator: str
	:param dict_ends: left-end and right-end characters bounding a dict
	:type dict_ends: str, len of 2
	:param dict_separator: string to place between dict elements
	:type dict_separator: str
	:param dict_colon: str to place between name and value of dict pair
	:type dict_colon: str
	:param message_ends: left-end and right-end characters bounding a message
	:type message_ends: str, len of 2
	:param message_separator: string to place between message elements
	:type message_separator: str
	:param message_colon: str to place between name and value of dict pair
	:type message_colon: str
	:param true_false: strings to encode as representations for true and false
	:type true_false: list of 2 str
	:param no_value: string to encode as a None value
	:type no_value: str
	:param flag_value_separator: string to place between flag and value
	:type flag_value_separator: str
	:param any_separator: string to place between elements of an Any representation
	:type any_separator: str
	"""
	def __init__(self, dash=None, double_dash=None,
			list_ends=None, list_separator=None,
			dict_ends=None, dict_separator=None, dict_colon=None,
			message_ends=None, message_separator=None, message_colon=None,
			true_false=None, no_value=None,
			flag_value_separator=None, any_separator=None):
		self.dash = dash or '-'
		self.double_dash = double_dash or '--'
		self.list_ends = list_ends or [None, None]
		self.list_separator = list_separator or ','
		self.dict_ends = dict_ends or [None, None]
		self.dict_separator = dict_separator or ','
		self.dict_colon = dict_colon or ':'
		self.message_ends = message_ends or [None, None]
		self.message_separator = message_separator or ','
		self.message_colon = message_colon or ':'
		self.true_false = true_false or ['true', 'false']
		self.no_value = no_value or 'null'
		self.flag_value_separator = flag_value_separator or '='
		self.any_separator = any_separator or '/'

class Utility(Point, StateMachine):
	"""An async proxy object that starts and manages a non-standard sub-process.

	The named executable is started and the machine waits for termination. If stdin
	is a ``str`` the contents are written to an input pipe. If stdout is ``str`` (i.e. the class)
	the object will return the text received on the output pipe, in the :class:`~.lifecycle.Completed`
	message.

	Parameters are passed from the calling process to the child process by translating the
	positional parameters according to a few rules;

	* Each parameter (i.e. ``args[i]``) should be a tuple where the first element is
	  the name of the parameter and the second element is the runtime value of that name.
	* A 3-tuple can also be used where the middle element contains the separator to used
	  on the command line, between the name and the value.
	* Values are Python values and these are encoded in a best-guess fashion, e.g. a Python
	  int will be converted to the proper sequence of digits. A Python str will be
	  passed verbatim.
	* Explicit type information can be passed in ``args_schema``. This is a name-type dict
	  where the type value is used to control the encoding process, e.g. a Python float
	  can be described as a ``ar.ClockTime`` and the float will be converted to a full ISO
	  format string on the command line.
	* By default the command line is decorated with dashes and equals signs. Passing a
	  :class:`~.processing.Punctuation` parameter takes explicit control over those decorations.

	:param name: name of the executable file
	:type name: str
	:param args: positional args
	:type args: tuple
	:param args_schema: explicit type information about args
	:type args_schema: dict of ansar type expressions
	:param punctuation: override standard decoration of command line
	:type punctuation: :class:`~.processing.Punctuation`
	:param stdin: text to pass to child
	:type stdin: str or None
	:param stdout: type of expected output, e.g. str
	:type stdout: type
	:param stderr: type of expected output, e.g. str
	:type stderr: type
	:param text: nature of pipe content - text or binary
	:type text: bool
	:param encoding: control encoding of text, passed to ``Popen()``
	:type encoding: str
	:param errors: control encoding errors, passed to ``Popen()``
	:type errors: str
	:param cwd: where to locate the sub-process
	:type cwd: str
	:param kw: additional parameters passed to ``Popen()``
	:type kw: named parameters dict
	"""
	def __init__(self, name, *args,
			args_schema=None, punctuation=None,
			stdin=None, stdout=None, stderr=None,
			text=False, encoding=None, errors=None,
			cwd=None,
			**kw):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.name = name
		self.args = args
		self.args_schema = args_schema
		self.punctuation = punctuation or Punctuation()
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.text = text
		self.encoding = encoding
		self.errors = errors
		self.cwd = cwd
		self.input = None
		self.piping = False
		self.kw = kw
		self.p = None

def Utility_INITIAL_Start(self, message):
	# If no home has been loaded, path will resolve to
	# none, i.e. the default.
	executable = shutil.which(self.name)
	if executable is None:
		cwd = os.getcwd()
		self.complete(Faulted(f'cannot resolve executable "{self.name}" from "{cwd}"'))

	try:
		args = process_args(self.args, self.args_schema, self.punctuation)
	except ValueError as e:
		s = str(e)
		self.complete(Faulted(f'cannot process arguments for "{self.name}", {s}'))

	# Pipe work
	# 1. ACTION - nothing in, nothing out (default)
	# 2. SINK - something in, nothing out
	# 3. SOURCE - nothing in, something out
	# 4. FILTER - something in, something out

	stdin = self.stdin
	if isinstance(stdin, str):
		self.input = stdin
		self.stdin = PIPE
		self.text = True
	elif isinstance(stdin, (bytes, bytearray)):	# Block
		self.input = stdin
		self.stdin = PIPE
		self.text = False

	stdout = self.stdout
	if stdout == str:	 # Unicode
		if stdin and not self.text:
			raise ValueError('cannot support different input/output/error pipes')
		self.stdout = PIPE
		self.text = True
	elif stdout in (bytes, bytearray):	# Block
		if stdin and self.text:
			raise ValueError('cannot support different input/output/error pipes')
		self.stdout = PIPE
		self.text = False

	stderr = self.stderr
	if stderr == str:	 # Unicode
		if (stdin or stdout) and not self.text:
			raise ValueError('cannot support different input/output/error pipes')
		self.stderr = PIPE
		self.text = True
	elif stderr in (bytes, bytearray):	# Block
		if (stdin or stdout) and self.text:
			raise ValueError('cannot support different input/output pipes')
		self.stderr = PIPE
		self.text = False

	self.piping = stdin or stdout or stderr

	line = [executable]
	line.extend(args)

	c = ' '.join(line)
	self.console(c)
	try:
		start_new_session = CL.child_process
		self.p = Popen(line,
			start_new_session=True,
			stdin=self.stdin, stdout=self.stdout, stderr=sys.stderr,
			text=True, encoding='utf-8', errors='strict')
			#**self.kw)
	except OSError as e:
		s = f'cannot start process "{self.module_path}" ({e})'
		self.complete(Faulted(s))

	#self.log(USER_TAG.STARTED, f'Started process ({self.p.pid})')
	self.create(wait, self.p, True)

	return EXECUTING

def Utility_EXECUTING_Returned(self, message):
	code, page = message.value.code, message.value.page

	if code == 0:
		if not page:
			self.complete(None)
		output = cast_to(page, bytes_type)
		self.complete(output)
	self.complete(Faulted(f'child exit code {code}', 'expecting 0 (zero)'))

def Utility_EXECUTING_Stop(self, message):
	self.p.terminate()
	return CLEARING

def Utility_CLEARING_Returned(self, message):
	self.complete(Aborted())

UTILITY_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	EXECUTING: (
		(Returned, Stop),
		()
	),
	CLEARING: (
		(Returned,),
		()
	),
}

bind_statemachine(Utility, UTILITY_DISPATCH)


#
#
NoneType = type(None)

def write_if(r, s):
	if s:
		r.write(s)

def write_if_else(r, b, ie):
	if b:
		r.write(ie[0])
	else:
		r.write(ie[1])

def dash_style(name, punctuation):
	if len(name) == 1:
		return punctuation.dash
	return punctuation.double_dash

def resolve(name, value, schema, punctuation):
	if value is None:
		return None
	return str(value)

def process_args(args, schema, punctuation=None):
	punctuation = punctuation or Punctuation()
	line = []
	for i, a in enumerate(args):
		if isinstance(a, tuple):
			n = len(a)
			if not (n in [2, 3]):
				raise ValueError('tuple flag [%d] with unexpected length %d' % (i, n))

			name = a[0]
			if not isinstance(name, str):
				raise ValueError('tuple flag [%d] with strange name %r' % (i, name))

			separator = punctuation.flag_value_separator
			dash = dash_style(name, punctuation)
			if len(a) == 2:
				value = resolve(name, a[1], schema, punctuation)
			else:
				separator = a[1]
				value = resolve(name, a[2], schema, punctuation)

			if value is None:
				line.append('%s%s' % (dash, name))
			elif separator is None:
				line.append('%s%s' % (dash, name))
				line.append('%s' % (value,))
			else:
				line.append('%s%s%s%s' % (dash, name, separator, value))
		else:
			value = resolve(i, a, schema, punctuation)
			line.append('%s' % (value,))
	return line
