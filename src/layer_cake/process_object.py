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

The ProcessObjectSpool creates and manages 1 or more instances of ProcessObject.
Messages sent to the spool are forwarded to one of the sub-processes. Distribution
is round-robin. The spool also implements queueing, i.e. a spool with one process
and a queue size of one is still (minimally) useful.
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
	'ProcessObjectSpool',
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
	"""An async proxy object that starts and manages a standard sub-process.

	:param name: name of the executable file
	:type name: str
	:param input: object to be passed
	:type input: type expression
	:param input_type: explicit type
	:type input_type: type expression
	:param output: enable decoding of stdout
	:type output: bool
	:param forwarding: enable forwarding of parent stdin
	:type forwarding: bool
	:param settings: additional command line arguments
	:type settings: list of str
	:param origin: starting context, internal
	:type origin: enum
	:param debug: level
	:type debug: enum
	:param home_path: location of a home, internal
	:type home_path: str
	:param role_name: name within a home, internal
	:type role_name: str
	:param upgrade: version translation
	:type upgrade: function
	:param kw: addition args passed to Popen
	:type kw: named args dict
	"""
	def __init__(self, object_or_name, origin: ProcessOrigin=None, home_path=None, role_name=None, object_api=None, extra_types=None, **settings):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.object_or_name = object_or_name
		self.origin = origin
		self.home_path = home_path
		self.role_name = role_name
		self.object_api = object_api
		self.extra_types = extra_types
		self.settings = settings

		self.module_path = None
		self.dot_py = True
		self.script_path = None
		self.origin_path = None
		self.api = None
		self.listening_for_directories = None
		self.p = None

		self.published = None
		self.queue = deque()

	def fork_exec(self, rt):
		# Start the new process.
		# Derive the home/role context using the globals defined for
		# this process, plus the values describing the new process.

		if self.origin is not None:				# Override.
			origin = self.origin
		elif CL.origin == ProcessOrigin.RUN:	# Foreground.
			origin = ProcessOrigin.RUN_CHILD
		elif CL.origin == ProcessOrigin.START:	# Background.
			origin = ProcessOrigin.START_CHILD
		else:
			origin = ProcessOrigin.SHELL		# Default

		self.role_name = self.role_name or breakpath(self.module_path)[1]
		self.home_path = self.home_path or CL.home_path
		if CL.role_name:
			self.role_name = f'{CL.role_name}.{self.role_name}'

		# Build the command line.
		command = []
		if self.dot_py:
			interpreter = sys.executable
			command.append(interpreter)
			command.append(self.module_path)

		else:
			command.append(self.module_path)

		try:
			c = CodecNoop()
			if self.listening_for_directories:
				v = encode_argument(c, self.listening_for_directories, UserDefined(HostPort))
				command.append(f'--directory-scope=LIBRARY')
				command.append(f'--connect-to-directory={v}')

				subscribe(self, self.role_name, scope=ScopeOfDirectory.PROCESS)

			# Generate the proper argument strings.
			if rt:
				schema = rt.schema | CommandLine.__art__.schema
			else:
				schema = CommandLine.__art__.schema

			for k, v in self.settings.items():
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

		shell = origin == ProcessOrigin.SHELL
		if not shell:
			command.append(f'--origin={origin.name}')

		command.append(f'--child-process')
		command.append(f'--full-output')
		if CL.background_daemon:
			command.append(f'--background-daemon')

		if self.home_path:
			command.append(f'--home-path={self.home_path}')
		command.append(f'--role-name={self.role_name}')

		if CL.debug_level is not None:
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
		self.console(f'Command "{c}"')
		try:
			start_new_session = CL.child_process
			self.p = Popen(command,
				#start_new_session=start_new_session,
				stdin=None, stdout=PIPE, stderr=sys.stderr,
				text=True, encoding='utf-8', errors='strict',
				env=environ)
				#**self.kw)
		except OSError as e:
			s = f'Cannot start process "{self.module_path}" ({e})'
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
		role = open_role(home_role)
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
			self.dot_py = True
			self.module_path = find_module(self.object_or_name)
		else:
			self.complete(Faulted(f'Cannot execute {self.object_or_name} (unknown extension?)'))

		if self.module_path is None:
			self.complete(Faulted(f'Cannot execute {self.object_or_name} (not found)'))

		if self.object_api is not None and len(self.object_api) > 0:
			self.api = self.object_api
			self.send(Enquiry(), PD.directory)
			return PENDING

	elif isinstance(self.object_or_name, HomeRole):
		executable_file = self.object_or_name.executable_file()
		if not self.home_path:
			self.complete(Faulted(f'Cannot execute {executable_file} (no home_path)'))

		self.module_path = find_role(executable_file, self.home_path)
		if self.module_path is None:
			self.complete(Faulted(f'Cannot execute {executable_file} (no role script)'))

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
			self.complete(Faulted(f'Cannot execute {self.object_or_name} (not registered)'))

		imported_module = self.object_or_name.__module__
		module = sys.modules[imported_module]
		self.module_path = module.__file__

		if rt.api is not None and len(rt.api) > 0:
			self.api = rt.api
			self.send(Enquiry(), PD.directory)
			return PENDING

	self.fork_exec(rt)
	return EXECUTING

def ProcessObject_PENDING_Unknown(self, message):
	message = cast_to(message, self.received_type)
	q = (message, self.return_address)
	self.queue.append(q)
	return PENDING

def ProcessObject_PENDING_HostPort(self, message):
	self.listening_for_directories = message
	rt = getattr(self.object_or_name, '__art__', None)
	self.fork_exec(rt)
	return EXECUTING

def ProcessObject_EXECUTING_Available(self, message):
	self.published = self.return_address
	for q in self.queue:
		self.forward(q[0], self.published, q[1])
	self.queue = deque()
	return EXECUTING

def ProcessObject_EXECUTING_Subscribed(self, message):
	# Ignore.
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
	self.complete(Faulted(f'Non-standard process exit - code={code}, output={t}, page="{p}..."'))

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

bind_statemachine(ProcessObject, dispatch=PROCESS_DISPATCH, thread='process-object')

#
#
SPOOL_SPAN = 32

class ProcessObjectSpool(Point, StateMachine):
	"""An async proxy object that starts and manages one or more standard sub-process.

	:param name: name of the executable file
	:type name: str
	"""
	def __init__(self, object_or_name, role_name=None, process_count=8, size_of_spool=512, responsiveness=None, **settings):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.object_or_name = object_or_name
		self.role_name = role_name
		self.process_count = process_count
		self.size_of_spool = size_of_spool
		self.responsiveness = responsiveness
		self.settings = settings

		self.idle_process = deque()
		self.pending_request = deque()
		self.span = deque()
		self.total_span = 0.0
		self.average = 0.0
		self.boundary_1 = 0.0
		self.boundary_2 = 0.0
		self.shard = 0

	def submit_request(self, message, forward_response, return_address):
		if self.responsiveness is None:
			pass
		elif self.average < self.boundary_1:
			pass
		else:
			self.shard += 1
			divisor = 4 if self.average < self.boundary_2 else 10
			if self.shard % divisor == 0:
				self.send(Overloaded('Reduced responsiveness from spool processes'), return_address)
				return

		idle = self.idle_process.popleft()
		r = self.create(GetResponse, message, idle)
		self.callback(r, forward_response, idle=idle, return_address=return_address, started=clock_now())

def ProcessObjectSpool_INITIAL_Start(self, message):
	if self.responsiveness is not None:
		self.boundary_1 = self.responsiveness % 0.75
		self.boundary_2 = self.responsiveness % 0.9

	pc = self.process_count
	sos = self.size_of_spool
	r = self.responsiveness

	if pc < 1 or (sos is not None and sos < 1) or (r is not None and r < 0.5):
		self.complete(Faulted(f'Cannot start the spool with the given parameters (count={pc}, size={sos}, responsiveness={r})'))
	
	role_name = self.role_name or 'spool'

	for i in range(pc):
		r = f'{role_name}-{i}'
		a = self.create(ProcessObject, self.object_or_name, role_name=r, **self.settings)
		self.assign(a, i)
		self.idle_process.append(a)

	return SPOOLING

def ProcessObjectSpool_SPOOLING_Unknown(self, message):
	m = cast_to(message, self.received_type)
	if not self.idle_process:
		if self.size_of_spool is None or len(self.pending_request) < self.size_of_spool:
			self.pending_request.append((m, self.return_address))
			return SPOOLING
		request = portable_to_signature(self.received_type)
		self.reply(Overloaded('Process resources busy and spool full', request=request))
		return SPOOLING

	def forward_response(self, value, kv):
		# Completion of a request/responsesequence.
		# Record the idle process.
		self.idle_process.append(kv.idle)

		# Update the performance metric.
		span = clock_now() - kv.started
		self.total_span += span
		self.span.append(span)
		while len(self.span) > SPOOL_SPAN:
			s = self.span.popleft()
			self.total_span -= s
		self.average = self.total_span / len(self.span)

		# Deliver reponse to the original client.
		m = cast_to(value, self.returned_type)
		self.send(m, kv.return_address)
		if not self.pending_request:
			return
		message, return_address = self.pending_request.popleft()

		# There is a request-to-go and an available process.
		self.submit_request(message, forward_response, return_address)
		return

	# There is a request-to-go and an available process.
	self.submit_request(m, forward_response, self.return_address)
	return SPOOLING

def ProcessObjectSpool_SPOOLING_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(self, message)
		return SPOOLING

	if self.working():
		self.abort()
		return CLEARING
	self.complete(Aborted())

def ProcessObjectSpool_SPOOLING_Stop(self, message):
	self.abort()
	return CLEARING

def ProcessObjectSpool_CLEARING_Returned(self, message):
	d = self.debrief()
	if self.working():
		return CLEARING
	self.complete(Aborted())

OBJECT_SPOOL_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	SPOOLING: (
		(Unknown, Returned, Stop,),
		()
	),
	CLEARING: (
		(Returned,),
		()
	),
}

bind_statemachine(ProcessObjectSpool, dispatch=OBJECT_SPOOL_DISPATCH, thread='process-object-spool')
