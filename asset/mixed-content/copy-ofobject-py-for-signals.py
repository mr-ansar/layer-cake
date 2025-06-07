# Author: Scott Woods <scott.18.ansar@gmail.com.com>
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

""".

.
"""
__docformat__ = 'restructuredtext'

import os
import sys
import signal
import uuid
import time

import ansar.encode as ar

from .lifecycle import *
from .point import *
from .log import *
from .rolling import *
from .locking import *
from .root import *
from .home import *

__all__ = [
	'POINT_OF_ORIGIN',
	'start_origin',
	'run_origin',
	'LOG_NUMBER',
	'ObjectSettings',
	'object_settings',
	'object_role',
	'object_resolve',
	'object_args',
	'object_variables',
	'object_executable',
	'object_words',
	'object_custom_settings',
	'object_unknown',
	'store_settings',
	'object_input',
	'object_resource_folder',
	'object_tmp_folder',
	'object_model_folder',
	'object_resource_path',
	'object_tmp_path',
	'object_model_path',
	'object_passing',
	'sub_object_passing',
	'create_object',
]

#
#
POINT_OF_ORIGIN = ar.Enumeration(START_ORIGIN=1, START_CHILD=2, RUN_ORIGIN=3, RUN_CHILD=4)

def start_origin(p):
	return p in (POINT_OF_ORIGIN.START_ORIGIN, POINT_OF_ORIGIN.START_CHILD)

def run_origin(p):
	return p in (POINT_OF_ORIGIN.RUN_ORIGIN, POINT_OF_ORIGIN.RUN_CHILD)

#
#
LOG_NUMBER = ar.Enumeration(FAULT=ar.USER_LOG_FAULT, WARNING=ar.USER_LOG_WARNING,
	CONSOLE=ar.USER_LOG_CONSOLE, OBJECT=ar.USER_LOG_OBJECT,
	TRACE=ar.USER_LOG_TRACE, DEBUG=ar.USER_LOG_DEBUG, NONE=ar.USER_LOG_NONE)

#
#
class ObjectSettings(object):
	"""Values that capture the details of a "call" between parent and child process.

	These are the values used to implement integration between parent and child
	processes. There are also values that are useful at the command-line, i.e.
	debug_level, help, dump_settings, dump_input, store_settings, store_input,
	settings_file, input_file and output_file are all available as command-line
	setttings (i.e. to dump the current input use --dump-input).

	:param call_signature: I/O expectations of the caller
	:type call_signature: "io", "i", "o" or None
	:param debug_level: NONE, DEBUG, TRACE, OBJECT, CONSOLE, WARNING, FAULT
	:type debug_level: str
	:param home_path: location of a process group
	:type home_path: str
	:param role_name: role within a process group
	:type role_name: str
	:param point_of_origin: context of execution - start, run or call (sub-process)
	:type point_of_origin: 1, 2, or 3
	:param help: enable output of help page
	:type help: bool
	:param dump_settings: enable output of current settings
	:type dump_settings: JSON representation
	:param dump_input: enable output of the stored input
	:type dump_input: JSON representation
	:param store_settings: enable saving of the current settings
	:type store_settings: bool
	:param store_input: enable saving of the current input
	:type store_input: bool
	:param settings_file: use the settings in the specified file
	:type settings_file: str
	:param input_file: use the input in the specified file
	:type input_file: str
	:param output_file: place any output in the specified file
	:type output_file: str
	"""
	def __init__(self,
			pure_object=False,
			call_signature=None,			# All scenarios.
			debug_level=None,
			home_path=None, role_name=None,	# Fully-homed only.
			point_of_origin=None,			# Variants on home execution.
			help=False,						# Administrative features.
			dump_settings=False,
			dump_input=False,
			store_settings=False, store_input=False, factory_reset=False,
			settings_file=None, input_file=None, output_file=None,
			group_pid=None):
		self.pure_object = pure_object
		self.call_signature = call_signature
		self.debug_level = debug_level
		self.home_path = home_path
		self.role_name = role_name
		self.point_of_origin = point_of_origin
		self.help = help
		self.dump_settings = dump_settings
		self.dump_input = dump_input
		self.store_settings = store_settings
		self.store_input = store_input
		self.factory_reset = factory_reset
		self.settings_file = settings_file
		self.input_file = input_file
		self.output_file = output_file
		self.group_pid = group_pid

	def homed(self):
		if self.home_path and self.role_name:
			return True
		return False

OBJECT_SETTINGS_SCHEMA = {
	'pure_object': ar.Boolean(),
	'call_signature': ar.Unicode(),
	'debug_level': LOG_NUMBER,
	'home_path': ar.Unicode(),
	'role_name': ar.Unicode(),
	'point_of_origin': POINT_OF_ORIGIN,
	'help': ar.Boolean(),
	'dump_settings': ar.Boolean(),
	'dump_input': ar.Boolean(),
	'store_settings': ar.Boolean(),
	'store_input': ar.Boolean(),
	'factory_reset': ar.Boolean(),
	'settings_file': ar.Unicode(),
	'input_file': ar.Unicode(),
	'output_file': ar.Unicode(),
	'group_pid': ar.Integer8(),
}

ar.bind_message(ObjectSettings, object_schema=OBJECT_SETTINGS_SCHEMA)

object_settings = ObjectSettings()

#
#
co = ar.Gas(command_args=[], environment_variables={}, command_executable=None, command_words=[], unknown=None, settings=None, input=None, role=None, signal_received=None)

#
#
def object_role():
	"""Global access to the runtime context assumed by create_object(). Returns a HomeRole."""
	return co.role

def object_resolve(name):
	"""Global access to executables within the bin folder."""
	hb = co.role.home
	executable = hb.resolve_executable(name)
	if executable is None:
		return name
	return executable

def object_args():
	"""Global access to the words appearing on the command-line. Returns a list of words."""
	return co.command_args

def object_variables():
	"""Global access to the values decoded from the environment. Returns the variables object."""
	return co.environment_variables

def object_executable():
	"""Global access to the host executable. Returns a str."""
	return co.command_executable

def object_words():
	"""Global access to the words appearing on the command-line. Returns a list of words."""
	return co.command_words

def object_custom_settings():
	"""Global access to the values decoded from persistent configuration. Returns the values or None."""
	return co.settings

def object_unknown():
	"""Global access to the values decoded from persistent configuration. Returns the values or None."""
	return co.unknown_args

def store_settings(settings):
	"""Global mechanism for updating the persistent configuration. Returns indication of success."""
	if co.role.role_settings is not None:
		co.role.role_settings[1].store(settings)
		co.role.role_settings[2] = settings
		return True
	return False

def object_input():
	"""Global access to the values decoded from the input pipe or file. Returns the values or None."""
	return co.command_input

def object_resource_folder():
	"""Part of the disk management context, i.e. resource. Returns the per-executable, read-only resource folder or None."""
	if object_settings.homed():
		return co.role.role_resource
	return None

def object_tmp_folder():
	"""Part of the disk management context, i.e tmp. Returns the empty-on-start, temporary folder or None."""
	if object_settings.homed():
			return co.role.role_tmp
	return None

def object_model_folder():
	"""Part of the disk management context, i.e. model. Returns the folder of bulk, persistent storage or None."""
	if object_settings.homed():
			return co.role.role_model
	return None

#
#
def object_resource_path():
	"""Partner to resource_folder(). Returns the folder path or None."""
	f = object_resource_folder()
	if f:
		return f.path
	return None

def object_tmp_path():
	"""Partner to tmp_folder(). Returns the folder path or None."""
	f = object_tmp_folder()
	if f:
		return f.path
	return None

def object_model_path():
	"""Partner to model_folder(). Returns the folder path or None."""
	f = object_model_folder()
	if f:
		return f.path
	return None

# Fragments of supporting code that work between the
# platform and the object.

def decoration_store(d, value):
	f = d[1]
	f.store(value)
	d[2] = value

def decoration_recover(d, compiled):
	f = d[1]
	try:
		settings, v = f.recover()
		return settings, v
	except ar.FileNotFound:
		pass

	try:
		f.store(compiled)
	except ar.FileFailure:
		return None, None
	return compiled, None

#
#
def catch_interrupt(number, frame):
	co.signal_received = number

def interrupt_alias(number, frame):
	root = start_up(None)
	# Skip the filtering.
	accepting = 'Accepting signal {number} as SIGINT alias'
	root.log(ar.TAG_TRACE, accepting.format(number=number))
	co.signal_received = signal.SIGINT

def ignore_signal(number, frame):
	pass

def log_signal(number, frame):
	root = start_up(None)
	# Skip the filtering.
	root.log(ar.TAG_WARNING, 'Unexpected signal {number}'.format(number=number))

# Default handling of mismatch between loaded settings and
# what the application expects.
def no_upgrade(s, v):
	rt = s.__art__
	c = 'decoded version "%s" of "%s"' % (v, rt.path)
	f = ar.Failed(settings_upgrade=(None, c))
	raise ar.Incomplete(f)

# Standard parameter processing. Check for name collision.
#
def object_passing(special_settings):
	if special_settings is not None:
		a = object_settings.__art__.value.keys()
		b = special_settings.__art__.value.keys()
		c = set(a) & set(b)
		if len(c) > 0:
			j = ', '.join(c)
			raise ValueError('collision in settings names - {collisions}'.format(collisions=j))
	executable, word, ls = ar.break_args()
	x, r = ar.extract_args(object_settings, ls, special_settings)
	ar.arg_values(object_settings, x)
	return executable, word, r

def sub_object_passing(specific_settings, table):
	if specific_settings is not None:
		a = object_settings.__art__.value.keys()		# Framework values.
		b = specific_settings.__art__.value.keys()	  # Application.
		c = set(a) & set(b)
		if len(c) > 0:
			j = ', '.join(c)
			raise ValueError(f'collision in settings names - {j}')

	executable, ls1, sub, ls2, word = ar.sub_args()
	x1, r1 = ar.extract_args(object_settings, ls1, specific_settings)
	ar.arg_values(object_settings, x1)

	# Support for the concept of a noop pass, just for the
	# framework.
	def no_sub_required(s):
		return s.help or s.dump_settings or s.dump_input

	if sub is not None:
		try:
			sub_function, sub_settings = table[sub]
		except KeyError:
			raise ValueError(f'unknown sub-command "{sub}"')

		if sub_settings:
			x2, r2 = ar.extract_args(sub_settings, ls2, None)
			ar.arg_values(sub_settings, x2)
		else:
			r2 = ls2
	elif no_sub_required(object_settings):
		# Give framework a chance to complete some
		# admin operation.
		sub_function = None
		r2 = ({}, {})
	else:
		raise ValueError('no-op command')

	bundle = (sub_function, # The sub-command function.
		r2,				 # Remainder from ls2, i.e. for passing to sub-component
		word)			   # Non-flag arguments.

	return executable, bundle, r1

#
#
def object_vector(self, object_type, settings, input, fixed_value, key_value):
	name_counts = ['"%s" (%d)' % (k, len(v)) for k, v in pt.thread_classes.items()]

	executable = os.path.abspath(sys.argv[0])
	self.trace('Executable "%s" as object process (%d)' % (executable, os.getpid()))
	self.trace('Working folder "%s"' % (os.getcwd()))
	self.trace('Running object "%s"' % (object_type.__art__.path,))
	self.trace('Class threads (%d) %s' % (len(pt.thread_classes), ','.join(name_counts)))

	unknown = object_unknown()
	if unknown is not None:
		self.warning(f'Unknown settings ({unknown}) ignored')

	pa = ()
	if settings is not None:
		pa = pa + (settings,)
	if input is not None:
		pa = pa + (input,)
	pa = pa + fixed_value

	a = self.create(object_type, *pa, **key_value)

	while True:
		m = self.select(Completed, Stop, Pause, Resume)

		if isinstance(m, Completed):
			# Do a "fake" signaling. Sidestep all the platform machinery
			# and just set a global. It does avoid any complexities
			# arising from overlapping events. Spent far too much time
			# trying to untangle signals, exceptions and interrupted i/o.
			co.signal_received = signal.SIGKILL
			return m.value
		elif isinstance(m, Stop):
			# Received a Stop.
			self.send(m, a)
			m = self.select(Completed)
			return m.value
		
		self.send(m, a)

bind_function(object_vector, lifecycle=True, message_trail=True, execution_trace=True)

#
#
def load_home(factory_settings, factory_input, properties):
	# Determine the framework support; homed, tool or transient object.
	homed = False		# Operating within a home.

	point_of_origin = object_settings.point_of_origin or POINT_OF_ORIGIN.RUN_ORIGIN
	try:
		bp = ar.breakpath(co.command_executable)
		executable = bp[1]

		if object_settings.homed():
			homed = True

			# Home is pre-requisite, i.e. created by ansar cli.
			hb = Homebase(object_settings.home_path, FULL_SERVICE)
			if not hb.plan_exists():
				f = ar.Failed(home_open=(None, f'home "{object_settings.home_path}" does not exist'))
				raise ar.Incomplete(f)
			hb.open_plan()

			if hb.role_exists(object_settings.role_name):
				rp = properties()
			else:
				rp = properties(
					guid=uuid.uuid4(),
					created=ar.world_now(),
					executable=executable,
				)
			hr = hb.open_role(object_settings.role_name, factory_settings, factory_input, properties=rp)

		elif factory_settings or factory_input:
			# Running in context of the local user/host. Auto-create a limited
			# version of a home.
			base = os.getenv('ANSAR_TOOL') or os.getenv('HOME') or os.getcwd()
			path = os.path.join(base, '.ansar-tool')

			# Auto-create home as needed.
			hb = Homebase(path, TOOL_SERVICE)
			if not hb.plan_exists():
				hb.create_plan({})		# No redirects :-(.
			else:
				hb.open_plan()

			# Auto-create role. This is a persistent context
			# for every instance of a tool. No multi-processing
			# guarantees.
			if hb.role_exists(executable):
				rp = properties()
			else:
				rp = properties(
					guid=uuid.uuid4(),
					created=ar.world_now(),
					executable=executable,
				)
			hr = hb.open_role(executable, factory_settings, factory_input, properties=rp)
		else:
			# Also running in the wild but with no need for persistent
			# services such as settings or input.
			hb = Homebase('.', [])
			hr = hb.open_role(executable, None, None)
	except (ar.CodecFailed, ar.FileFailure) as e:
		f = ar.Failed(home_open=(e, None))
		raise ar.Incomplete(f)
	except ar.CommandError as e:
		f = ar.Failed(home_open=(e, None))
		raise ar.Incomplete(f)

	return homed, point_of_origin, hr

def daemonize():
	"""
	Do the UNIX double-fork shuffle, see Stevens' "Advanced
	Programming in the UNIX Environment" for details (ISBN 0201563177)
	http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
	"""
	try:
		pid = os.fork()
		if pid > 0:
			# exit first parent
			sys.exit(0)
	except OSError as e:
		f = ar.Failed(process_fork=(e, '#1'))
		raise ar.Incomplete(f)

	# decouple from parent environment
	os.chdir("/")
	os.setsid()
	os.umask(0)

	try:
		pid = os.fork()
		if pid > 0:
			# exit second parent
			sys.exit(0)
	except OSError as e:
		f = ar.Failed(process_fork=(e, '#2'))
		raise ar.Incomplete(f)

	# redirect standard file descriptors
	#sys.stdout.flush()
	#sys.stderr.flush()
	#si = file(self.stdin, 'r')
	#so = file(self.stdout, 'a+')
	#se = file(self.stderr, 'a+', 0)
	#os.dup2(si.fileno(), sys.stdin.fileno())
	#os.dup2(so.fileno(), sys.stdout.fileno())
	#os.dup2(se.fileno(), sys.stderr.fileno())

	# write pidfile
	#atexit.register(self.delpid)
	#pid = str(os.getpid())
	#file(self.pidfile,'w+').write("%s\n" % pid)

def load_settings(role, factory_settings, args, upgrade):
	unknown = None
	if factory_settings is None:
		return None, unknown

	if not ar.is_message(factory_settings):
		t = ar.tof(factory_settings)
		f = ar.Failed(object_settings=(None, 'object "{t}" is not a registered message'))
		raise ar.Incomplete(f)

	tos = ar.value_type(factory_settings)
	try:
		if object_settings.settings_file:
			settings, v = ar.file_recover(object_settings.settings_file, tos)
		else:
			#settings, v = factory_settings, None
			settings, v = decoration_recover(role.role_settings, factory_settings)

		if v is not None:
			mismatch = f'mismatched version ({v}) of settings'
			if not upgrade:
				f = ar.Failed(settings_upgrade=(mismatch, 'no upgrade feature available'))
				raise ar.Incomplete(f)
			try:
				settings = upgrade(settings, v)
			except ar.CommandError as e:
				f = ar.Failed(settings_upgrade=(mismatch, e))
				raise ar.Incomplete(f)

		x, r = ar.extract_args(settings, args, None)
		if len(r[0]) > 0 or len(r[1]) > 0:
			lf, sf = r
			lk, sk = lf.keys(), sf.keys()
			ld = [k for k in lk]
			sd = [k for k in sk]
			ld.extend(sd)
			unknown = ', '.join(ld)
			#f = ar.Failed(object_args=(None, f'unknown ({unknown}) settings detected in arguments'))
			#raise ar.Incomplete(f)
		change = len(x[0]) or len(x[1])
		if change:
			ar.arg_values(settings, x)
	except (ar.FileFailure, ar.CodecFailed) as e:
		f = ar.Failed(settings_load=(e, None))
		raise ar.Incomplete(f)
	except ar.CommandError as e:
		f = ar.Failed(settings_load=(e, 'unexpected name or name/value mismatch?'))
		raise ar.Incomplete(f)

	return settings, unknown

def load_input(role, factory_input, input_type, upgrade, word):
	if factory_input is None:
		return None

	toi = input_type or  ar.value_type(factory_input)
	try:
		# Explicit file has priority, then the presence/absence
		# of command-line words (e.g. files), then input
		# piped from the parent.
		if object_settings.input_file:
			input, v = ar.file_recover(object_settings.input_file, toi)
		elif word:
			input, v = factory_input, None
		elif object_settings.call_signature is None or 'i' in object_settings.call_signature:
			input, v = ar.input_decode(toi)
		elif role.role_input and role.role_input[2]:
			input, v = role.role_input[2], None
		else:
			input, v = factory_input, None

		if v is not None:
			mismatch = f'mismatched version ({v}) of input'
			if not upgrade:
				f = ar.Failed(input_upgrade=(mismatch, 'no upgrade feature available'))
				raise ar.Incomplete(f)
			try:
				settings = upgrade(settings, v)
			except ar.CommandError as e:
				f = ar.Failed(input_upgrade=(mismatch, e))
				raise ar.Incomplete(f)

	except (ar.FileFailure, ar.CodecFailed) as e:
		f = ar.Failed(input_decode=(e, 'cannot decode input'))
		raise ar.Incomplete(f)

	return input

def load_logging(role, point_of_origin, homed):
	files_in_folder = None
	try:
		if homed:
			storage = role.properties.storage
			if storage:
				bytes_in_file = 120 * LINES_IN_FILE
				files_in_folder = storage / bytes_in_file

			if start_origin(point_of_origin):
				logs = RollingLog(role.role_logs.path, files_in_folder=files_in_folder)
			elif object_settings.debug_level in (None, LOG_NUMBER.NONE):
					logs = log_to_nowhere
			else:
				logs = select_logs(object_settings.debug_level)
		elif object_settings.debug_level in (None, LOG_NUMBER.NONE):
				logs = log_to_nowhere
		else:
			logs = select_logs(object_settings.debug_level)
	except ar.CommandError as e:
		f = ar.Failed(logs_open=(e, None))
		raise ar.Incomplete(f)

	return logs

def run_object(start_vector, object_type, settings, input, fixed_value, role, logs, homed, point_of_origin, key_value):
	output = None
	early_return = False
	root = None
	try:

		# Primary goal is translation of SIGINT (control-c) into
		# a stop protocol. The SIGHUP signal also receives similar
		# attention on the basis its notification of a shutdown.
		# For debugging purposes other signals are logged as warnings.
		signal.signal(signal.SIGINT, catch_interrupt)
		signal.signal(signal.SIGQUIT, interrupt_alias)
		signal.signal(signal.SIGHUP, interrupt_alias)
		signal.signal(signal.SIGTERM, interrupt_alias)

		signal.signal(signal.SIGCHLD, ignore_signal)
		signal.signal(signal.SIGTRAP, log_signal)
		signal.signal(signal.SIGABRT, log_signal)
		#signal.signal(signal.SIGKILL, log_signal)	... cant be caught.
		signal.signal(signal.SIGPIPE, log_signal)
		signal.signal(signal.SIGUSR1, catch_interrupt)
		signal.signal(signal.SIGUSR2, catch_interrupt)
		signal.signal(signal.SIGALRM, log_signal)
		signal.signal(signal.SIGTTIN, log_signal)
		#signal.signal(signal.SIGSTOP, log_signal)	... ditto.
		signal.signal(signal.SIGTSTP, log_signal)
		signal.signal(signal.SIGPWR, log_signal)

		# Start up async world.
		root = start_up(logs)

		home_entry = homed and role.role_entry
		if home_entry:
			a = root.create(lock_and_hold, role.home.lock.path, role.role_name, group_pid=object_settings.group_pid)
			root.assign(a, role.role_name)
			m = root.select(Ready, Completed)
			if isinstance(m, Completed):	# Cannot lock.
				root.debrief()
				c = ar.Failed(object_lock=(None, f'role {role.role_name} is running'))
				raise ar.Incomplete(c)

		cs = object_settings.call_signature
		no_output = cs is not None and 'o' not in cs
		if point_of_origin == POINT_OF_ORIGIN.START_ORIGIN or no_output:
			early_return = True
			ar.output_encode(Ack(), ar.Any())
			sys.stdout.close()
			os.close(1)

		#
		#
		if home_entry:
			role.entry_started()

		# Create the async object.
		a = root.create(start_vector, object_type, settings, input, fixed_value, key_value)

		# Termination of this function is
		# either by SIGINT (control-c) or assignment by object_vector.
		running = True
		while running:
			while co.signal_received is None:
				time.sleep(0.1)
				#signal.pause()
			sr, co.signal_received = co.signal_received, None

			# If it was keyboard then async object needs
			# to be bumped.
			if sr == signal.SIGKILL:
				running = False
			elif sr == signal.SIGINT:
				root.send(Stop(), a)
				running = False
			elif sr == signal.SIGUSR1:
				root.send(Pause(), a)
			elif sr == signal.SIGUSR2:
				root.send(Resume(), a)

		m = root.select(Completed)
		output = m.value

	finally:
		if root is not None:
			root.abort()
			while root.working():
				root.select(Completed)
				root.debrief()

		# Close the active record.
		if home_entry:
			role.entry_returned(output)

	if early_return:
		return None
	return output

def object_output(output):
	# Default exit code is success, i.e. framework operating properly.
	code = 0
	if output is None:
		return code

	def error_code():
		# Need a framework-specific exit code but also
		# need to honour any exit code specified in a
		# command fault.
		code = 171 if code == 0 else code
		return code

	# Command has faulted. If console-based (the default) put
	# diagnostic on stderr and terminate.
	if isinstance(output, ar.Faulted):
		code = 172 if output.exit_code is None else output.exit_code
		if not object_settings.pure_object:
			ar.command_error(output)
			return code

	# Place the command output/fault in a requested file.
	if object_settings.output_file:
		try:
			ar.file_store(object_settings.output_file, output, t=ar.Any())
			return code
		except (ar.FileFailure, ar.CodecFailed) as e:
			# Framework has faulted. Fault is the new
			# output.
			output = ar.Failed(command_output=(e, None))
			if not object_settings.pure_object:
				ar.command_error(output)
				return error_code()

	# Place the command output/fault or framework fault
	# on stdout.
	try:
		if not ar.is_message(output):
			t = ar.tof(output)
			output = ar.Faulted(f'object returned a "{t}"', 'not a registered message')
			if not object_settings.pure_object:
				ar.command_error(fault)
				return code

		if object_settings.pure_object:
			ar.output_encode(output, t=ar.Any())
		else:
			ar.output_human(output)

	except (ar.CodecFailed, OSError) as e:
		# Output does not encode or the stream/platform is
		# compromised. Worth trying to put diagnostic on stderr
		# but otherwise we are hosed.
		if not object_settings.pure_object:
			fault = ar.Failed(command_output=(e, None))
			ar.command_error(fault)
		return error_code()

	return code

#
#
def create_object(object_type, *fixed_value,
	factory_settings=None, factory_input=None, input_type=None, factory_variables=None,
	upgrade=None,
	parameter_passing=object_passing, parameter_table=None,
	start_vector=object_vector,
	logs=log_to_nowhere, properties=RoleProperties,
	**key_value):
	"""Creates an async process shim around a "main" async object. Returns nothing.

	:param object_type: the type of an async object to be instantiated
	:type object_type: a function or a Point-based class
	:param factory_settings: persistent values
	:type factory_settings: instance of a registered class
	:param factory_input: per-invocation values
	:type factory_input: instance of a registered class
	:param factory_variables: host environment values
	:type factory_variables: instance of a registered class
	:param upgrade: function that accepts old versions of settings/input and produces the current version
	:type upgrade: function
	:param parameter_passing: method for parsing sys.argv[]
	:type parameter_passing: a function
	:param logs: a callable object expecting to receive log objects
	:type logs: function or class with __call__ method
	:rtype: None
	"""
	# Start with a command line of flags and words and declaration
	# information about what to expect in the way of parameters and
	# piped input, i.e. if any.

	try:
		# Break down the command line with reference to the
		# name/type information in the settings object.
		executable, words, args = ar.load_args(factory_settings, parameter_passing, parameter_table)

		co.command_executable = executable
		co.command_words = words
		co.command_args = args

		# Extract values from the environment with reference
		# to the name/type info in the variables object.
		variables = ar.load_variables(factory_variables)

		co.environment_variables = variables

		# Resume the appropriate operation context, i.e. home.
		# to the name/type info in the variables object.
		homed, point_of_origin, role = load_home(factory_settings, factory_input, properties)

		co.role = role

		#
		#
		if homed and point_of_origin == POINT_OF_ORIGIN.START_ORIGIN:
			daemonize()

		if object_settings.factory_reset and factory_settings is not None:
			try:
				decoration_store(role.role_settings, factory_settings)
			except (ar.FileFailure, ar.CodecFailed) as e:
				f = ar.Failed(settings_reset=(e, None))
				raise ar.Incomplete(f)
			raise ar.Incomplete(None)

		# Extract values from the words and args off the command
		# line, with reference to the name/type ino in the
		# settings object.
		settings, unknown = load_settings(role, factory_settings, args, upgrade)

		co.unknown_args = unknown
		co.custom_settings = settings

		# Non-operational features, i.e. command object not called.
		# Place settings for this command on stdout.
		if object_settings.help:
			ar.command_help(object_type, settings, parameter_table)
			raise ar.Incomplete(None)
		elif object_settings.dump_settings:
			if settings is None:
				f = ar.Failed(settings_dump=(None, 'no settings defined'))
				raise ar.Incomplete(f)
			try:
				ar.output_encode(settings)
			except ar.CodecFailed as e:
				f = ar.Failed(settings_dump=(e, None))
				raise ar.Incomplete(f)
			raise ar.Incomplete(None)

		if object_settings.store_settings and settings is not None:
			try:
				decoration_store(role.role_settings, settings)
			except (ar.FileFailure, ar.CodecFailed) as e:
				f = ar.Failed(settings_changed=(e, None))
				raise ar.Incomplete(f)

		# Primary input. Object expects to work on an instance of
		# input_type. Load from file or pipe.
		input = load_input(role, factory_input, input_type, upgrade, words)

		co.input = input

		#
		#
		if object_settings.dump_input:
			if input is None:
				f = ar.Failed(input_dump=(None, 'no dump defined'))
				raise ar.Incomplete(f)
			try:
				ar.output_encode(input)
			except ar.CodecFailed as e:
				f = ar.Failed(input_dump=(e, None))
				raise ar.Incomplete(f)
			raise ar.Incomplete(None)

		if object_settings.store_input and input is not None:
			try:
				decoration_store(role.role_input, input)
			except (ar.FileFailure, ar.CodecFailed) as e:
				f = ar.Faulted('cannot store input', str(e))
				raise ar.Incomplete(f)

		if object_settings.store_settings or object_settings.store_input:
			raise ar.Incomplete(Ack())

		# Resolve logging - where should it go?
		#
		logs = load_logging(role, point_of_origin, homed)

		output = run_object(start_vector, object_type, settings, input, fixed_value, role, logs, homed, point_of_origin, key_value)
	except ar.Incomplete as e:
		output = e.value

	code = object_output(output)

	sys.exit(code)

