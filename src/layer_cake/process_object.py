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

Async objects are used to start and manage underlying platform processes. The
named process is started, runs to completion and (potentially) returns a value.
This conforms to the general model of an asynchronous object.

There are two variants. Utility provides the most expressive access possible to
third-party executables. These are processes that may accept many different styles
of arguments and behave differently with respect to the standard streams (e.g. stdout).
The class provides for convenient sending of a stream of text or bytes to the process,
and the corresponding ability to receive text or bytes as a result.

The ProcessObject class is used where the targeted executable is implemented using a
special framework provided by the library. An instance of a message (i.e. with
fully typed members) is passed over the input pipe, to serve as "arguments" or
"configuration". An instance of an Any() expression is expected on the output.
In this way the local object can satisfy all the expectations of an async object,
while the actual work is carried out in the child process.

Both classes implement the proper termination behaviour. A Stop() message is
translated into a platform signal, to interrupt the execution of the targeted
process. This is a fundamental part of the asynchronous object lifecycle and
it brings expressive and responsive multi-processing capability.
"""
__docformat__ = 'restructuredtext'

#
#
import sys
import os
import threading
import signal
from subprocess import Popen, PIPE
import shutil
import io
import uuid
from datetime import datetime, timedelta
from collections import deque
import base64

from .general_purpose import *
from .virtual_memory import *
from .convert_memory import *
from .message_memory import *
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
from .home_role import *
from .bind_type import *
from .object_collector import *
from .object_directory import *
from .process_directory import *
from .ip_networking import *

__all__ = [
	'ProcessObject',
	'Punctuation',
	'Utility',
	'process_args',
	'CodecArgs'
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
def wait(self, p, piping):
	if piping:
		out, err = p.communicate()
		return p.returncode, out
	else:
		code = p.wait()
		return code, None

bind(wait)

# The ProcessObject class
# A platform process that accepts a set of fully-typed arguments
# and returns a fully-typed result.
class INITIAL: pass
class PENDING: pass
class EXECUTING: pass
class CLEARING: pass

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
	def __init__(self, object_type, role_name=None, **settings):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.object_type = object_type

		#self.group_pid = HR.group_pid
		#self.group_port = group_port

		self.module_name = object_type.__module__
		self.module = sys.modules[self.module_name]
		self.module_path = self.module.__file__

		role_name = role_name or breakpath(self.module_path)[1]

		self.home_path = HR.home_path
		self.role_name = f'{HR.role_name}.{role_name}'

		self.settings = settings
		self.p = None

		self.published = None
		self.queue = deque()

def ProcessObject_INITIAL_Start(self, message):
	rt = getattr(self.object_type, '__art__', None)
	if rt and rt.api is not None and len(rt.api) > 0:
		self.send(Enquiry(), PD.directory)
		return PENDING
	executable = sys.executable

	# Build the sub-process command line.
	command = [executable, self.module_path]

	command.append(f'--child-process')
	command.append(f'--full-output')
	if CL.background_daemon:
		command.append(f'--background-daemon')

	command.append(f'--home-path={self.home_path}')
	command.append(f'--role-name={self.role_name}')

	if CL.debug_level is not None:
		command.append(f'--debug-level={CL.debug_level.name}')

	if CL.keep_logs:
		command.append(f'--keep-logs')

	#self.group_pid = self.group_pid or CL.group_pid
	#if self.group_pid:
	#	arg = f'--group-pid={self.group_pid}'
	#	command.append(arg)

	rt = self.object_type.__art__
	if isinstance(rt, PointRuntime):
		schema = rt.schema | CommandLine.__art__.schema

		try:
			c = CodecNoop()
			for k, v in self.settings.items():
				name = k
				e = schema[k]
				k = k.replace('_', '-')
				v = encode_argument(c, v, e)
				command.append(f'--{k}={v}')
		except KeyError as e:
			self.complete(Faulted(f'cannot encode value for "{self.role_name}" ({e.args[0]} does not exist)'))
		except CodecError as e:
			e = str(e)
			s = e.replace('cannot encode', f'cannot encode value for "{self.role_name}.{name}"')
			self.complete(Faulted(s))

	# Force the details of the I/O streams.
	try:
		start_new_session = CL.background_daemon and not CL.child_process
		self.p = Popen(command,
			start_new_session=start_new_session,
			stdin=None, stdout=PIPE, stderr=sys.stderr,
			text=True, encoding='utf-8', errors='strict')
			#env=hb.bin_env,
			#**self.kw)
	except OSError as e:
		f = Faulted(process_start=(e, None))
		self.warning(str(f))
		self.complete(f)

	self.log(USER_TAG.STARTED, f'Started process ({self.p.pid})')
	self.create(wait, self.p, True)

	# Good to go. Next event should be Returned.
	self.send(AddObject(self.object_address), PO.collector)
	return EXECUTING

def ProcessObject_PENDING_Unknown(self, message):
	message = cast_to(message, self.message_type)
	q = (message, self.return_address)
	self.queue.append(q)
	return PENDING

def ProcessObject_PENDING_HostPort(self, message):
	executable = sys.executable

	# Build the sub-process command line.
	command = [executable, self.module_path]

	command.append(f'--child-process')
	command.append(f'--full-output')
	if CL.background_daemon:
		command.append(f'--background-daemon')

	command.append(f'--home-path={self.home_path}')
	command.append(f'--role-name={self.role_name}')

	if CL.debug_level is not None:
		command.append(f'--debug-level={CL.debug_level.name}')

	if CL.keep_logs:
		command.append(f'--keep-logs')

	#self.group_pid = self.group_pid or CL.group_pid
	#if self.group_pid:
	#	arg = f'--group-pid={self.group_pid}'
	#	command.append(arg)

	rt = self.object_type.__art__
	if isinstance(rt, PointRuntime):
		schema = rt.schema | CommandLine.__art__.schema
		try:
			c = CodecNoop()
			v = encode_argument(c, message, UserDefined(HostPort))
			command.append(f'--connect-to-directory={v}')

			subscribe(self, self.role_name)

			for k, v in self.settings.items():
				name = k
				e = schema[k]
				k = k.replace('_', '-')
				v = encode_argument(c, v, e)
				command.append(f'--{k}={v}')
		except KeyError as e:
			self.complete(Faulted(f'cannot encode value for "{self.role_name}" ({e.args[0]} does not exist)'))
		except CodecError as e:
			e = str(e)
			s = e.replace('cannot encode', f'cannot encode value for "{self.role_name}.{name}"')
			self.complete(Faulted(s))

	# Force the details of the I/O streams.
	try:
		start_new_session = CL.background_daemon and not CL.child_process
		self.p = Popen(command,
			start_new_session=start_new_session,
			stdin=None, stdout=PIPE, stderr=sys.stderr,
			text=True, encoding='utf-8', errors='strict')
			#env=hb.bin_env,
			#**self.kw)
	except OSError as e:
		f = Faulted(process_start=(e, None))
		self.warning(str(f))
		self.complete(f)

	self.log(USER_TAG.STARTED, f'Started process ({self.p.pid})')
	self.create(wait, self.p, True)

	# Good to go. Next event should be Returned.
	self.send(AddObject(self.object_address), PO.collector)
	return EXECUTING

def ProcessObject_EXECUTING_PublishAsName(self, message):
	self.published = message
	for q in self.queue:
		self.forward(q[0], self.published.address, q[1])
	self.queue = deque()
	return EXECUTING

def ProcessObject_EXECUTING_Unknown(self, message):
	if self.published is None:
		message = cast_to(message, self.message_type)
		q = (message, self.return_address)
		self.queue.append(q)
		return EXECUTING
	self.forward(message, self.published.address, self.return_address)
	return EXECUTING

def ProcessObject_EXECUTING_Returned(self, message):
	self.send(RemoveObject(self.object_address), PO.collector)

	# Wait thread has returned
	# Forward the result.
	code, out = message.value

	self.log(USER_TAG.ENDED, f'ProcessObject ({self.p.pid}) ended with {code}')
	if not out:
		self.complete(None)

	encoding = CodecJson()
	try:
		output = encoding.decode(out, Any())
	except CodecError as e:
		s = str(e)
		self.complete(Faulted(f'cannot decode output ({s}) not a standard executable?'))

	self.complete(output)

def ProcessObject_EXECUTING_Stop(self, message):
	pid = self.p.pid
	try:
		os.kill(pid, signal.SIGINT)
	except OSError as e:
		self.complete(Faulted(f'cannot relay local Stop to "{pid}" as SIGINT'))
	return CLEARING

def ProcessObject_CLEARING_Returned(self, message):
	ProcessObject_EXECUTING_Returned(self, message)

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
		(PublishAsName, Unknown, Returned, Stop),
		()
	),
	CLEARING: (
		(Returned,),
		()
	),
}

bind_statemachine(ProcessObject, dispatch=PROCESS_DISPATCH)

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
	the object will return the text received on the output pipe, in the :class:`~.lifecycle.Returned`
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
	  can be described as a ``ClockTime`` and the float will be converted to a full ISO
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
		c = 'cannot process arguments for "%s", %s' % (self.name, s)
		self.complete(Faulted(condition=c))

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

	if len(self.kw) > 0:
		kw = dict(stdin=self.stdin, stdout=self.stdout, stderr=self.stderr,
			text=self.text, encoding=self.encoding, errors=self.errors,
			cwd=self.cwd)
		kw.update(self.kw)
		self.p = Popen(line, **kw)
		self.create(wait, self.p, self.piping)
		return EXECUTING

	if self.piping:
		self.p = Popen(line,
			stdin=self.stdin, stdout=self.stdout, stderr=self.stderr,
			text=self.text, encoding=self.encoding, errors=self.errors,
			cwd=self.cwd)
	else:
		self.p = Popen(line, cwd=self.cwd)
	self.create(wait, self.p, self.piping)
	return EXECUTING

def Utility_EXECUTING_Returned(self, message):
	# Wait thread has returned
	# Forward the result.
	code, out = message.value
	if code == 0:
		self.complete(out)
	c = 'child exit code %d' % (code,)
	self.complete(Faulted(condition=c, explanation='expecting 0 (zero)'))

def Utility_EXECUTING_Stop(self, message):
	self.p.terminate()
	return CLEARING

def Utility_CLEARING_Returned(self, message):
	code, _ = message.value
	if code < 0:
		if -code == signal.SIGTERM:
			self.complete(Aborted())
		c = 'child signal code %d' % (-code,)
		self.complete(Faulted(condition=c, explanation='expecting SIGTERM (15)'))

	# These are non-standard processes, i.e. there will
	# be a variety of meanings to exit codes. Also, allow
	# ships passing in the night. And any positive exit
	# code.
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

bind_statemachine(Utility, dispatch=UTILITY_DISPATCH)

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
	encoding = CodecArgs(pretty_format=False)
	inferred = False
	try:
		if schema:
			try:
				te = schema[name]
			except KeyError:
				inferred = True
				t = type(value)
				te = fix_expression(t, set())
		else:
			inferred = True
			t = type(value)
			te = fix_expression(t, set())

		value = encoding.encode(value, te, punctuation)
		return value
	except CodecError as e:
		s = str(e)
	except TypeTrack as e:
		s = e.reason

	if inferred:
		s = 'inferring type for %r failed - %s' % (name, s)
	else:
		s = 'encoding for %r failed - %s' % (name, s)
	raise ValueError(s)

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

# Dedicated code for transforming python data into
# reasonable command-line text.

def p2a_placeholder(c, p, t):
	r = c.representation
	r.write('<?>')

def p2a_address(c, p, t):
	p2a_vector(c, p, VectorOf(Integer8()))

def p2a_none(c, p, t):
	r = c.representation
	r.write('<>')

def p2a_bool(c, p, t):
	r = c.representation
	tf = c.punctuation.true_false
	write_if_else(r, p, tf)

def p2a_byte(c, p, t):
	r = c.representation
	value = '%d' % (p,)
	r.write(value)

def p2a_int(c, p, t):
	r = c.representation
	value = '%d' % (p,)
	r.write(value)

def p2a_float(c, p, t):
	r = c.representation
	value = '%f' % (p,)
	value = value.rstrip('0')
	r.write(value)

def p2a_string(c, p, t):
	r = c.representation
	w = ''
	for b in p:
		w += chr(b)
	r.write(w)

def p2a_block(c, p, t):
	r = c.representation
	w = base64.b64encode(p)
	w = w.decode(encoding='utf-8', errors='strict')
	r.write(w)

def p2a_unicode(c, p, t):
	r = c.representation
	r.write(p)

def p2a_clock(c, p, t):
	r = c.representation
	w = clock_to_text(p)
	r.write(w)

def p2a_span(c, p, t):
	r = c.representation
	w = span_to_text(p)
	r.write(w)

def p2a_world(c, p, t):
	r = c.representation
	w = world_to_text(p)
	r.write(w)

def p2a_delta(c, p, t):
	r = c.representation
	w = delta_to_text(p)
	r.write(w)

def p2a_uuid(c, p, t):
	r = c.representation
	w = uuid_to_text(p)
	r.write(w)

def p2a_enumeration(c, p, t):
	r = c.representation
	try:
		w = t.to_name(p)
	except KeyError:
		m = '/'.join(t.kv.keys())
		raise ValueError('no name for %d in "%s"' % (p, m))
	r.write(w)

def p2a_message(c, p, t):
	message = t.element
	rt = message.__art__
	schema = rt.value
	# Get the set of names appropriate to
	# this message type. Or none.
	r = c.representation
	me = c.punctuation.message_ends
	ms = c.punctuation.message_separator
	mc = c.punctuation.message_colon
	n = len(schema)

	write_if(r, me[0])
	for k, v in schema.items():
		c.walking_stack.append(k)
		def get_put():
			m = getattr(p, k, None)
			r.write(k)
			write_if(r, mc)
			python_to_args(c, m, v)
			if (n - 1) > 0:
				write_if(r, ms)
		get_put()
		n -= 1
		c.walking_stack.pop()
	write_if(r, me[1])

def p2a_array(c, p, t):
	e = t.element
	n = len(p)
	s = t.size
	if n != s:
		raise ValueError('array size vs specification - %d/%d' % (n, s))
	r = c.representation
	le = c.punctuation.list_ends
	ls = c.punctuation.list_separator
	write_if(r, le[0])
	for i, y in enumerate(p):
		c.walking_stack.append(i)
		python_to_args(c, p[i], e)
		if (i + 1) < n:
			write_if(r, ls)
		c.walking_stack.pop()
	write_if(r, le[1])

def p2a_vector(c, p, t):
	e = t.element
	r = c.representation
	le = c.punctuation.list_ends
	ls = c.punctuation.list_separator
	n = len(p)
	write_if(r, le[0])
	for i, y in enumerate(p):
		c.walking_stack.append(i)
		python_to_args(c, p[i], e)
		if (i + 1) < n:
			write_if(r, ls)
		c.walking_stack.pop()
	write_if(r, le[1])

def p2a_set(c, p, t):
	e = t.element
	r = c.representation
	le = c.punctuation.list_ends
	ls = c.punctuation.list_separator
	n = len(p)
	write_if(r, le[0])
	for i, y in enumerate(p):
		c.walking_stack.append(i)
		python_to_args(c, y, e)
		if (i + 1) < n:
			write_if(r, ls)
		c.walking_stack.pop()
	write_if(r, le[1])

def p2a_map(c, p, t):
	k_t = t.key
	v_t = t.value
	r = c.representation
	de = c.punctuation.dict_ends
	ds = c.punctuation.dict_separator
	dc = c.punctuation.dict_colon
	n = len(p)
	write_if(r, de[0])
	for k, v in p.items():
		python_to_args(c, k, k_t)
		write_if(r, dc)
		python_to_args(c, v, v_t)
		if (n - 1) > 0:
			write_if(r, ds)
		n -= 1
	write_if(r, de[1])

def p2a_type(c, p, t):
	r = c.representation
	b = p.__art__
	w = b.path
	r.write(w)

def p2a_any(c, p, t):
	r = c.representation
	le = c.punctuation.list_ends
	ls = c.punctuation.any_separator
	a = p.__class__

	write_if(r, le[0])
	python_to_args(c, a, Type())
	write_if(r, ls)
	python_to_args(c, p, UserDefined(a))
	write_if(r, le[1])

# Map the python+portable pair to a dedicated
# transform function.
p2a = {
	# Direct mappings.
	(bool, Boolean): p2a_bool,
	(int, Byte): p2a_byte,
	(bytes, Character): p2a_string,
	(str, Rune): p2a_unicode,
	(int, Integer2): p2a_int,
	(int, Integer4): p2a_int,
	(int, Integer8): p2a_int,
	(int, Unsigned2): p2a_int,
	(int, Unsigned4): p2a_int,
	(int, Unsigned8): p2a_int,
	(float, Float4): p2a_float,
	(float, Float8): p2a_float,
	(int, Enumeration): p2a_enumeration,
	(bytearray, Block): p2a_block,
	(bytes, String): p2a_string,
	(str, Unicode): p2a_unicode,
	(float, ClockTime): p2a_clock,
	(float, TimeSpan): p2a_span,
	(datetime, WorldTime): p2a_world,
	(timedelta, TimeDelta): p2a_delta,
	(uuid.UUID, UUID): p2a_uuid,
	(list, ArrayOf): p2a_array,
	(list, VectorOf): p2a_vector,
	(set, SetOf): p2a_set,
	(dict, MapOf): p2a_map,
	(deque, DequeOf): p2a_set,
	(TypeType, Type): p2a_type,
	(list, TargetAddress): p2a_address,
	(list, Address): p2a_address,

	# PointerTo - can be any of the above.
	# (bool, PointerTo): p2a_pointer,
	# (int, PointerTo): p2a_pointer,
	# (float, PointerTo): p2a_pointer,
	# (bytearray, PointerTo): p2a_pointer,
	# (bytes, PointerTo): p2a_pointer,
	# (str, PointerTo): p2a_pointer,
	# ClockTime and TimeDelta. Float/ptr already in table.
	# (float, PointerTo): p2a_pointer,
	# (float, PointerTo): p2a_pointer,
	# (datetime, PointerTo): p2a_pointer,
	# (timedelta, PointerTo): p2a_pointer,
	# (uuid.UUID, PointerTo): p2a_pointer,
	# (list, PointerTo): p2a_pointer,
	# (set, PointerTo): p2a_pointer,
	# (dict, PointerTo): p2a_pointer,
	# (deque, PointerTo): p2a_pointer,
	# (TypeType, PointerTo): p2a_pointer,
	# (tuple, PointerTo): p2a_pointer,
	# (Message, PointerTo): p2a_pointer,

	# Two mechanisms for including messages
	(Message, UserDefined): p2a_message,
	(Message, Any): p2a_any,

	# Support for Word, i.e. passthru anything
	# that could have been produced by the functions
	# above. No iterating nested layers.

	(bool, Word): p2a_bool,
	(int, Word): p2a_int,
	(float, Word): p2a_float,
	# (bytearray, Word): pass_thru,
	# (bytes, Word): pass_thru,
	(str, Word): p2a_unicode,
	(list, Word): p2a_vector,
	(dict, Word): p2a_map,
	# set, tuple - do not appear in generic

	# Provide for null values being
	# presented for different universal
	# types.

	(NoneType, Boolean): p2a_none,
	(NoneType, Byte): p2a_none,
	(NoneType, Character): p2a_none,
	(NoneType, Rune): p2a_none,
	(NoneType, Integer2): p2a_none,
	(NoneType, Integer4): p2a_none,
	(NoneType, Integer8): p2a_none,
	(NoneType, Unsigned2): p2a_none,
	(NoneType, Unsigned4): p2a_none,
	(NoneType, Unsigned8): p2a_none,
	(NoneType, Float4): p2a_none,
	(NoneType, Float8): p2a_none,
	(NoneType, Block): p2a_none,
	(NoneType, String): p2a_none,
	(NoneType, Unicode): p2a_none,
	(NoneType, ClockTime): p2a_none,
	(NoneType, TimeSpan): p2a_none,
	(NoneType, WorldTime): p2a_none,
	(NoneType, TimeDelta): p2a_none,
	(NoneType, UUID): p2a_none,
	(NoneType, Enumeration): p2a_none,
	# DO NOT ALLOW
	# (NoneType, UserDefined): p2a_none,
	# (NoneType, ArrayOf): p2a_none,
	# (NoneType, VectorOf): p2a_none,
	# (NoneType, SetOf): p2a_none,
	# (NoneType, MapOf): p2a_none,
	# (NoneType, DequeOf): p2a_none,
	(NoneType, PointerTo): p2a_none,
	(NoneType, Type): p2a_none,
	(NoneType, TargetAddress): p2a_none,
	(NoneType, Address): p2a_none,
	(NoneType, Word): p2a_none,
	(NoneType, Any): p2a_none,
}

def python_to_args(c, p, t):
	"""Generate word equivalent for the supplied application data.

	:param c: the active codec
	:type c: an Ansar Codec
	:param p: the data item
	:type p: application data
	:param t: the portable description of `p`.
	:type t: a portable expression
	:return: a generic word, ready for serialization.
	"""
	try:
		if is_message(p):
			a = Message
		else:
			a = getattr(p, '__class__')
	except AttributeError:
		a = None

	try:
		b = t.__class__		 # One of the universal types.
	except AttributeError:
		b = None

	if a is None:
		if b is None:
			raise TypeError('unusable value and type')
		raise TypeError(f'value with type "{b.__name__}" is unusable')
	elif b is None:
		raise TypeError(f'value "{a.__name__}" is unusable')

	try:
		f = p2a[a, b]
	except KeyError:
		raise TypeError(f'no transform {a.__name__}/{b.__name__}')

	# Apply the transform function
	return f(c, p, t)


# Define the wrapper around the JSON encoding
# primitives.
class CodecArgs(Codec):
	"""Encoding and decoding of command-line representations."""

	EXTENSION = 'arg'
	SINGLE_TAB = '  '

	def __init__(self, return_proxy=None, local_termination=None, pretty_format=False, decorate_names=True):
		"""Construct an args codec."""
		Codec.__init__(self,
			CodecArgs.EXTENSION,
			None,
			None,
			return_proxy, local_termination, pretty_format, decorate_names)
		self.representation = None
		self.tabstops = {}

	def find_tab(self, tabs):
		"""Generate the tab-space indicated by the tabs count. Return a string of spaces."""
		try:
			tab = self.tabstops[tabs]
		except KeyError:
			tab = CodecArgs.SINGLE_TAB * tabs
			self.tabstops[tabs] = tab
		return tab

	def encode(self, value, expression, punctuation):
		"""Blah."""
		self.punctuation = punctuation

		self.walking_stack = []		 # Breadcrumbs for m.a[0].f.c[1] tracking.
		self.aliased_pointer = {}	   # Pointers encountered in value.
		self.portable_pointer = {}	  # Pointers accumulated from Incognitos.
		self.any_stack = [set()]
		self.pointer_alias = 2022

		u4 = uuid.uuid4()
		self.alias_space = str(u4)

		self.representation = io.StringIO()

		try:
			# Convert the value to a generic intermediate
			# representation.

			python_to_args(self, value, expression)
		except (AttributeError, TypeError, ValueError, IndexError, KeyError) as e:
			text = self.nesting()
			if len(text) == 0:
				raise CodecError(str(e))
			raise CodecError('transformation, near "%s" (%s)', text, str(e))
		s = self.representation.getvalue()
		return s
