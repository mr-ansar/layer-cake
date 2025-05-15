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

import os
import sys
import time
import signal
import uuid
import datetime
import tempfile
import json
from os.path import join
from .virtual_memory import *
from .convert_memory import *
from .message_memory import *
from .convert_type import *
from .convert_type import SIGNATURE_TABLE
from .virtual_codec import *
from .json_codec import *
from .noop_codec import *
from .file_object import *
from .folder_object import *
from .virtual_runtime import *
from .virtual_point import *
from .routine_point import *
from .point_runtime import *
from .general_purpose import *
from .command_line import *
from .command_startup import *
from .object_runtime import *
from .object_logs import *
from .rolling_log import *
from .platform_system import *
from .head_lock import *
from .home_role import *
from .bind_type import *
from .object_directory import *
from .process_directory import *

__all__ = [
	'FAULTY_EXIT',
	'CommandResponse',
	'StartStop',
	'HomeRole',
	'open_role',
	'open_home',
	'create',
]

FAULTY_EXIT = 71

#
class Unassigned(object): pass

class Incomplete(Exception):
	def __init__(self, value=Unassigned):
		self.value = value

class CommandResponse(object):
	def __init__(self, command: str=None, note: str=None):
		self.command = command
		self.note = note

bind_message(CommandResponse)

class HomeFile(object):
	def __init__(self, path_name, t):
		self.file = File(path_name, t, create_default=True)
		self.value = None

	def __call__(self):
		return self.value

	def update(self, value=Unassigned):
		if value != Unassigned:
			self.value = value
		self.file.store(self.value)

	def resume(self):
		self.value = self.file.recover()
		return self.value

class NoHomeFile(object):
	def __init__(self, value=None):
		self.value = value

	def __call__(self):
		return self.value

	def update(self, value=Unassigned):
		if value != Unassigned:
			self.value = value

	def resume(self):
		return self.value

class TmpFolder(object):
	def __init__(self, path_name, t):
		self.folder = Folder(path_name)

	def __call__(self):
		return None

	def update(self, value=Unassigned):
		pass

	def resume(self):
		remove_contents(self.folder.path)

class StartStop(object):
	def __init__(self, start: datetime.datetime=None, stop: datetime.datetime=None, returned: Any=None):
		self.start = start
		self.stop = stop
		self.returned = returned

bind_message(StartStop)

START_STOPS = 16

#
class HomeRole(object):
	def __init__(self,
		unique_id=None, start_stop=None,
		settings=None,
		logs=None,
		model=None, tmp=None,
		lock=None,
		log_storage=None,
		executable_file=None):
		self.unique_id = unique_id
		self.start_stop = start_stop
		self.settings = settings
		self.logs = logs
		self.model = model
		self.tmp = tmp
		self.lock = lock
		self.log_storage = log_storage
		self.executable_file = executable_file

	def starting(self):
		s = self.start_stop()
		s.append(StartStop(start=world_now()))
		while len(s) > START_STOPS:
			s.popleft()
		self.start_stop.update()

	def stopped(self, value):
		s = self.start_stop()
		if len(s) < 1:
			return
		s = s[-1]
		s.stop = world_now()
		s.returned = value
		self.start_stop.update()

DEFAULT_STORAGE = 1024 * 1024 * 256

#
def open_role(home_role):
	'''Load all the details of a role from the specified location. Returns HomeRole.'''
	try:
		# Get list of names in role, less any extent.
		split = os.path.splitext
		listing = [split(s)[0] for s in os.listdir(home_role)]
	except FileNotFoundError:
		return None

	role = HomeRole()

	# Check name is in role and folder. Only then is the
	# property created and existing value loaded.
	def resume(name, t):
		if name not in listing:
			raise Incomplete(Faulted(f'cannot open "{home_role}"', f'missing property "{name}"'))
		if not hasattr(role, name):
			raise Incomplete(Faulted(f'cannot open "{home_role}"', f'unknown property "{name}"'))

		path_name = join(home_role, name)
		f = HomeFile(path_name, t)
		f.resume()
		setattr(role, name, f)

	# Create runtime object for each named property.
	resume('unique_id', UUID())
	resume('start_stop', DequeOf(UserDefined(StartStop)))
	resume('settings', MapOf(Unicode(),Any()))
	resume('log_storage', Integer8())
	resume('executable_file', Unicode())

	# Create a runtime object for potential folders.
	def link(name):
		path_name = os.path.join(home_role, name)
		value = Folder(path_name)
		setattr(role, name, value)

	link('model')
	link('tmp')
	link('logs')
	link('lock')

	return role

def create_role(home_role, executable):
	Folder(home_role)
	role = HomeRole()

	# Check name is in role and folder. Only then is the
	# property created and existing value loaded.
	def create(name, t, value):
		path_name = join(home_role, name)
		f = HomeFile(path_name, t)
		f.update(value)
		setattr(role, name, f)

	# Create runtime object for each named property.
	create('unique_id', UUID(), uuid.uuid4())
	create('settings', MapOf(Unicode(), Any()), {})
	create('start_stop', DequeOf(UserDefined(StartStop)), deque())
	create('log_storage', Integer8(), DEFAULT_STORAGE)
	create('executable_file', Unicode(), executable)

	# Create a runtime object for potential folders.
	def link(name):
		path_name = os.path.join(home_role, name)
		value = Folder(path_name)
		setattr(role, name, value)

	link('model')
	link('tmp')
	link('logs')
	link('lock')

	return role

def create_memory_role(executable):
	role = HomeRole()

	def create(name, t, value):
		f = NoHomeFile(value)
		setattr(role, name, f)

	# Create runtime object for each named property.
	create('unique_id', UUID(), uuid.uuid4())
	create('settings', MapOf(Unicode(), Any()), {})
	create('start_stop', DequeOf(UserDefined(StartStop)), deque())
	create('log_storage', Integer8(), DEFAULT_STORAGE)
	create('executable_file', Unicode(), executable)

	return role

#
def open_home(home_path, grouping=False, sub_roles=False):
	'''Load all the roles within a folder. Return a dict of HomeRoles'''

	try:
		def role(s):
			if '.' in s and not sub_roles:
				return False
			elif s.startswith('group') and not grouping:
				return False
			return True

		listing = {s: open_role(join(home_path, s)) for s in os.listdir(home_path) if role(s)}
	except FileNotFoundError:
		return None
	except Incomplete:
		return None

	return listing

def object_home(executable, home_role, sticky=False):
	'''Compile the runtime, file-based context for the current process. Return HomeRole and role.'''

	role = open_role(home_role)
	if CL.create_role:
		if role is not None:
			raise Incomplete(Faulted(f'cannot create "{home_role}"', f'already exists'))
		role = create_role(home_role, executable)
	elif role is None:
		if CL.origin in (ProcessOrigin.START, ProcessOrigin.START_CHILD) or sticky or CL.keep_logs:
			role = create_role(home_role, executable)
		else:
			role = create_memory_role(executable)

	# Circular dependency around log_storage. Wrap it in a
	# condition and default to fixed value.
	log_storage = role.log_storage() if role is not None else DEFAULT_STORAGE

	logs, files_in_folder = open_logs(home_role, log_storage)
	if files_in_folder:
		logs = RollingLog(role.logs.path, files_in_folder=files_in_folder)

	rolling = isinstance(logs, RollingLog)
	if sticky or rolling:
		if role is None:
			if home_role.count('.') == 0:
				raise Incomplete(Faulted(f'cannot auto-create "{home_role}"', f'sub-roles only'))
			role = create_role(home_role, executable)

	elif role is None:
		role = create_memory_role(executable)

	if role.tmp:
		remove_contents(role.tmp.path)

	return role, logs

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
		e = str(e)
		f = Faulted(f'cannot fork to daemonize #1 ({e})')
		raise Incomplete(f)

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
		e = str(e)
		f = Faulted(f'cannot fork to daemonize #2 ({e})')
		raise Incomplete(f)

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

def open_logs(home_role, storage):
	debug_level = CL.debug_level

	if CL.origin in (ProcessOrigin.START, ProcessOrigin.START_CHILD) or CL.keep_logs:
		bytes_in_file = 120 * LINES_IN_FILE
		files_in_folder = storage / bytes_in_file
		return None, files_in_folder
	elif debug_level is None:
		logs = log_to_nowhere
	else:
		logs = select_logs(debug_level)

	return logs, None

#def object_home():
#	"""Global access to the runtime context assumed by create_object(). Returns a HomeRole."""
#	return OBJECT_HOME.home_path
#	name_counts = ['"%s" (%d)' % (k, len(v)) for k, v in pt.thread_classes.items()]

#	executable = os.path.abspath(sys.argv[0])
#	self.trace('Working folder "%s"' % (os.getcwd()))
#	self.trace('Running object "%s"' % (object_type.__art__.path,))
#	self.trace('Class threads (%d) %s' % (len(pt.thread_classes), ','.join(name_counts)))

def start_vector(self, object_type, word, args):
	a = self.create(object_type, *word, **args)

	if CL.directory_scope == ScopeOfDirectory.LIBRARY:
		pn = PublishAs(name=CL.role_name, scope=ScopeOfDirectory.PROCESS, publisher_address=a)
		self.send(pn, PD.directory)

	while True:
		m, i = self.select(Returned, Stop)

		if i == 0:
			# Do a "fake" signaling. Sidestep all the platform machinery
			# and just set a global. It does avoid any complexities
			PS.signal_received = PS.platform_kill
		elif i == 1:
			self.send(m, a)
			m, i = self.select(Returned)

		return m.value

bind_routine(start_vector)

def run_object(home, object_type, word, args, logs, locking):
	'''Start the async runtime, lock if required and make arrangements for control-c handling.'''
	output = None
	try:
		# Install signal handlers, i.e. control-c.
		ps = PS.platform_signal
		if ps is None:
			f = Faulted(f'unknown "{PS.platform_system}" ({PS.platform_release})')
			raise Incomplete(f)
		ps()

		# Start the async runtime.
		root = start_up(logs)

		# Exclusive access to disk-based resources.
		if locking or isinstance(logs, RollingLog):
			a = root.create(head_lock, home.lock.path, 'head')
			root.assign(a, 1)
			m, i = root.select(Ready, Returned)
			if isinstance(m, Returned):	# Cannot lock.
				root.debrief()
				c = Faulted(f'role {home.lock.path} is running')
				raise Incomplete(c)

		if CL.edit_role:
			output = HR.edit_role(root, home)
			return output

		# Respond to daemon context, i.e. send output and close stdout.
		#if CL.origin == ProcessOrigin.START:	# or no_output:
		#	early_return = True
		#	object_encode(CommandResponse('background-daemon'))
		#	sys.stdout.close()
		#	os.close(1)

		# Write partial record to disk.
		home.starting()

		# Create the async object. Need to wrap in another object
		# to facilitate the control-c handling.
		a = root.create(start_vector, object_type, word, args)

		# Termination of this function is
		# either by SIGINT (control-c) or assignment by object_vector.
		running = True
		while running:
			while PS.signal_received is None:
				time.sleep(0.25)
				#signal.pause()
			sr, PS.signal_received = PS.signal_received, None

			# If it was keyboard then async object needs
			# to be bumped.
			if sr == PS.platform_kill:
				running = False
			elif sr == signal.SIGINT:
				root.send(Stop(), a)
				running = False

		m, i = root.select(Returned)		# End of start_vector.
		output = m.value

	finally:
		root.abort()					# Stop the lock if present.
		while root.working():
			root.select(Returned)
			root.debrief()

		home.stopped(output)

	#if early_return:		# Already sent output. Silence any output.
	#	return None

	return output

def object_encode(value):
	'''Put the encoding of the final result, on to stdout.'''
	pretty_format = not CL.child_process
	if CL.full_output:
		codec = CodecJson(pretty_format=pretty_format)
		output = codec.encode(value, Any())
		sys.stdout.write(output)
		sys.stdout.write('\n')
		return
	codec = CodecNoop()
	js = codec.encode(value, Any())
	value = js['value'][1]
	indent = 4 if pretty_format else None
	output = json.dumps(value, indent=indent)
	sys.stdout.write(output)
	sys.stdout.write('\n')

def object_error(fault):
	'''Print the final result - an error - on the console.'''
	p = sys.argv[0]
	sys.stderr.write(f'{p}: {fault}\n')

def object_output(value):
	'''Put the final output into an output file or on stdout.'''
	if value is None:
		return
	output_file = CL.output_file

	try:
		if output_file:
			f = File(output_file, Any())
			f.store(value)
			return
		object_encode(value)
		return
	except OSError as e:
		value = Faulted(str(e))
		PB.exit_status = e.args[0]
		if not CL.full_output:
			object_error(value)
			return
	except CodecError as e:
		value = Faulted(str(e))
		PB.exit_status = FAULTY_EXIT
		if not CL.full_output:
			object_error(value)
			return

	# Single, unmanaged attempt to output a failed object
	# output, i.e. cant open output file or failed encoding.
	object_encode(value)

#
def create(object_type, object_table=None, environment_variables=None, sticky=False, strict=True, scope=None):
	"""Creates an async process shim around a "main" async object. Returns nothing.

	:param object_type: the type of an async object to be instantiated
	:type object_type: a function or a Point-based class
	:rtype: None
	"""
	early_return = False
	try:
		# Break down the command line with reference to the
		# name/type information in the object type.
		if object_table is None:
			executable, argument, word = command_arguments(object_type)
		else:
			executable, argument, word = command_sub_arguments(object_type, object_table, strict=strict)

		bp = breakpath(executable)
		name = bp[1]

		if scope:
			CL.directory_scope = scope

		# Compose the location of file-based materials.
		home_path = CL.home_path or DEFAULT_HOME
		role_name = CL.role_name or name

		home_path = os.path.abspath(home_path)
		home_role = join(home_path, role_name)

		# Extract values from the environment with reference
		# to the name/type info in the variables object.
		command_variables(environment_variables)

		# Resume the appropriate operational context, i.e. home.
		home, logs = object_home(executable, home_role, sticky=sticky)

		HR.home_path = home_path
		HR.home_role = home_role
		HR.role_name = role_name

		if CL.dump_types:
			table = sorted(SIGNATURE_TABLE.keys())
			for t in table:
				print(t)
			raise Incomplete(None)

		if CL.create_role:
			home.settings.update(argument)
			t = [a for a in argument.keys()]
			if not t:
				t = ['empty']
			c = CommandResponse('create-role', ','.join(t))
			raise Incomplete(c)

		expect_settings = CL.update_role or CL.dump_role
		expect_settings = expect_settings or CL.factory_reset or CL.delete_role
		if expect_settings and not isinstance(home.settings, HomeFile):
			raise Incomplete(Faulted(f'no settings available "{home_role}"'))

		# Non-operational features, i.e. command object not called.
		# Current arguments not included.
		if CL.factory_reset:
			home.settings.update({})
			c = CommandResponse('factory-reset')
			raise Incomplete(c)

		if CL.dump_role:
			settings = (home.settings(), MapOf(Unicode(), Any()))
			object_encode(settings)
			raise Incomplete(None)		# Settings on stdout.

		# Add/override current settings with values from
		# the command line.
		settings = home.settings()
		for k, v in argument.items():
			settings[k] = v

		if CL.update_role:
			home.settings.update()
			t = [a for a in settings.keys()]
			if not t:
				t = ['empty']
			c = CommandResponse('update-role', ','.join(t))
			raise Incomplete(c)

		if CL.delete_role:
			try:
				remove_folder(HR.home_role)
			except OSError as e:
				raise Incomplete(Faulted('Cannot delete role', str(e)))
			c = CommandResponse('delete-role')
			raise Incomplete(c)

		if CL.help:
			#command_help(object_type, argument)
			raise Incomplete(None)

		if CL.origin == ProcessOrigin.START:
			object_encode(CommandResponse('background-daemon'))
			sys.stdout.close()
			os.close(1)
			daemonize()
			early_return = True

		rolling = isinstance(logs, RollingLog)
		locking = sticky or rolling

		args = kv_arguments(settings)

		output = run_object(home, object_type, word, args, logs, locking)
	except (CodecError, ValueError, KeyError) as e:
		s = str(e)
		output = Faulted(s)
	except Incomplete as e:
		output = e.value

	def ending(output):
		exit_status = 0
		if isinstance(output, Faulted):
			# Need a non-zero exit for command-line scenario but also a value
			# that ProcessObject can detect as part of framework operations,
			# i.e. and still make use of the fault, rather than discarding
			# the event.
			exit_status = output.exit_status if output.exit_status is not None else FAULTY_EXIT
			if not CL.full_output and not early_return:
				object_error(output)
				return exit_status
		if not early_return:
			object_output(output)
		return exit_status

	# Make available to tear_down (atexit) and also for checking
	# within unit tests.
	PB.output_value, PB.exit_status = output, ending(output)
