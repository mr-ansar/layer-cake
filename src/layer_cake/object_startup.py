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
from os.path import join
from .virtual_memory import *
from .convert_memory import *
from .message_memory import *
from .virtual_codec import *
from .json_codec import *
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

__all__ = [
	'FAULTY_EXIT',
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

DEFAULT_HOME = '.layer-cake'
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
			return
		if not hasattr(role, name):
			return

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
		if name in listing and hasattr(role, name):
			path_name = os.path.join(home_role, name)
			value = Folder(path_name)
			setattr(role, name, value)

	link('logs')
	link('model')
	link('tmp')
	link('lock')

	return role

#
def open_home(home_path):
	'''Load all the roles within a folder. Return a dict of HomeRoles'''
	try:
		listing = {s: open_role(join(home_path, s)) for s in os.listdir(home_path)}
	except FileNotFoundError:
		return None

	return listing

def object_home(executable, sticky=False, model=False, tmp=False, recording=False):
	'''Compile the runtime, file-based context for the current process. Return HomeRole and role.'''

	bp = breakpath(executable)
	name = bp[1]

	# Compose the location of file-based materials.
	home_path = CL.home_path or DEFAULT_HOME
	role_name = CL.role_name or name

	home_path = os.path.abspath(home_path)
	home_role = join(home_path, role_name)

	# Load whats already there.
	role = open_role(home_role)
	creating = sticky or model or tmp
	if role is None:
		if creating:
			Folder(home_role)
		role = HomeRole()

	# Reconcile with current requirements.
	def recover(name, portable, value):
		a = getattr(role, name, None)
		if not sticky:
			if a:
				value = a()
			f = NoHomeFile(value)
		elif a is None:
			f = HomeFile(join(home_role, name), portable)
			f.update(value)
		else:
			a.resume()
			return
		setattr(role, name, f)

	recover('unique_id', UUID(), uuid.uuid4())
	recover('settings', MapOf(Unicode(), Any()), {})
	recover('start_stop', DequeOf(UserDefined(StartStop)), deque())
	recover('log_storage', Integer8(), DEFAULT_STORAGE)
	recover('executable_file', Unicode(), executable)

	# Create missing folders.
	if model and not role.model:
		path_name = join(home_role, 'model')
		role.model = Folder(path_name)

	if tmp and not role.tmp:
		path_name = join(home_role, 'tmp')
		role.tmp = Folder(path_name)

	# Create folder if storing logs. Depends on command-line
	# arguments, i.e. startup context.
	logs, rolling = open_logs(home_role, role.log_storage(), recording)
	if rolling:
		role_logs, files_in_folder = rolling
		if not role.logs:
			role.logs = Folder(role_logs)
		logs = RollingLog(role.logs.path, files_in_folder=files_in_folder)

	# Create locking area if there is any disk based
	# activity, i.e. exclusive access.
	locking = rolling or sticky or model or tmp
	if locking and not role.lock:
		path_name = join(home_role, 'lock')
		role.lock = Folder(path_name)

	if role.tmp:
		remove_contents(role.tmp.path)

	return role, role_name, logs

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
		f = Faulted(str(e))
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
		f = Faulted(str(e))
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

def open_logs(home_role, storage, recording):
	origin = CL.point_of_origin or POINT_OF_ORIGIN.RUN_ORIGIN
	debug_level = CL.debug_level

	role_logs = None
	if origin in (POINT_OF_ORIGIN.START_ORIGIN, POINT_OF_ORIGIN.START_CHILD) or recording:
		bytes_in_file = 120 * LINES_IN_FILE
		files_in_folder = storage / bytes_in_file
		role_logs = join(home_role, 'logs')
		return None, (role_logs, files_in_folder)
	elif debug_level is None:
		logs = log_to_stderr
	elif debug_level == USER_LOG.NONE:
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

def start_vector(self, object_type, args):
	a = self.create(object_type, **args)

	while True:
		m = self.select(Completed, Stop)

		if isinstance(m, Completed):
			# Do a "fake" signaling. Sidestep all the platform machinery
			# and just set a global. It does avoid any complexities
			# arising from overlapping events. Spent far too much time
			# trying to untangle signals, exceptions and interrupted i/o.
			PS.signal_received = PS.platform_kill
			return m.value
		elif isinstance(m, Stop):
			self.send(m, a)
			m = self.select(Completed)
			return m.value

		self.send(m, a)

bind_routine(start_vector, lifecycle=True, message_trail=True, execution_trace=True,
	object_type=Type(),
	argument=MapOf(Unicode(), Any()))

def run_object(home, role, object_type, args, logs, locking, self_cleaning):
	'''Start the async runtime, lock if required and make arrangements for control-c handling.'''
	early_return = False
	output = None
	try:
		# Install signal handlers, i.e. control-c.
		ps = PS.platform_signal
		if ps is None:
			f = Faulted(f'unknown "{PS.platform_system}" ({PS.platform_release})')
			raise Incomplete(f)
		ps()

		# Start the async runtime.
		root = start_up(logs, self_cleaning)

		# Exclusive access to disk-based resources.
		if locking or isinstance(logs, RollingLog):
			a = root.create(head_lock, home.lock.path, 'head', group_pid=CL.group_pid)
			root.assign(a, 1)
			m = root.select(Ready, Completed)
			if isinstance(m, Completed):	# Cannot lock.
				root.debrief()
				c = Faulted(f'role {home.lock.path} is running')
				raise Incomplete(c)

		# Respond to daemon context, i.e. send output and close stdout.
		#cs = CL.call_signature
		#no_output = cs is not None and 'o' not in cs
		if CL.point_of_origin == POINT_OF_ORIGIN.START_ORIGIN:	# or no_output:
			early_return = True
			object_encode(Ack())
			sys.stdout.close()
			os.close(1)

		# Write partial record to disk.
		home.starting()

		# Create the async object. Need to wrap in another object
		# to facilitate the control-c handling.
		a = root.create(start_vector, object_type, args)

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

		m = root.select(Completed)		# End of start_vector.
		output = m.value

	finally:
		root.abort()					# Stop the lock if present.
		while root.working():
			m = root.select(Completed)
			root.debrief()

		rt = object_type.__art__
		if isinstance(rt, (RoutineRuntime, PointRuntime)):
			t = rt.return_type
		else:
			t = None

		if not isinstance(t, UserDefined):
			output = (output, t)
		home.stopped(output)

	if early_return:		# Already sent output. Silence any output.
		return None

	return output

def object_encode(value, pretty_format=True):
	'''Put the encoding of the final result, on to stdout.'''
	codec = CodecJson(pretty_format=pretty_format)
	output = codec.encode(value, Any())
	sys.stdout.write(output)
	sys.stdout.write('\n')

def object_error(fault):
	'''Print the final result - an error - on the console.'''
	p = sys.argv[0]
	sys.stderr.write(f'{p}: {fault}\n')

def object_output(value, pretty_format=True):
	'''Put the final output into an output file or on stdout.'''
	output_file = CL.output_file

	try:
		if output_file is None:
			object_encode(value, pretty_format=pretty_format)
			return
		f = File(output_file, Any())
		f.store(value)
		return
	except OSError as e:
		value = Faulted(str(e))
		PB.exit_status = e.args[0]
		if not CL.pure_object:
			object_error(value)
			return
	except CodecError as e:
		value = Faulted(str(e))
		PB.exit_status = FAULTY_EXIT
		if not CL.pure_object:
			object_error(value)
			return

	# Single, unmanaged attempt to output a failed object
	# output, i.e. cant open output file or failed encoding.
	object_encode(value, pretty_format=pretty_format)

#
def create(object_type, object_table=None,
	environment_variables=None,
	sticky=False, model=False, tmp=False, recording=False, self_cleaning=True):
	"""Creates an async process shim around a "main" async object. Returns nothing.

	:param object_type: the type of an async object to be instantiated
	:type object_type: a function or a Point-based class
	:rtype: None
	"""
	try:
		# Break down the command line with reference to the
		# name/type information in the object type.
		if object_table is None:
			executable, argument, word = command_arguments(object_type)
			sub = None
		else:
			executable, argument, word, sub = command_sub_arguments(object_type, object_table)

		# Extract values from the environment with reference
		# to the name/type info in the variables object.
		command_variables(environment_variables)

		# Resume the appropriate operational context, i.e. home.
		home, role, logs = object_home(executable, sticky=sticky, model=model, tmp=tmp, recording=recording)

		# Non-operational features, i.e. command object not called.
		# Current arguments not included.
		if CL.factory_reset:
			home.settings.update({})
			raise Incomplete(None)

		if CL.dump_settings:
			# ES.output_value = argment
			raise Incomplete(home.settings())

		# Add/override current settings with values from
		# the command line.
		settings = home.settings()
		for k, v in argument.items():
			settings[k] = v

		if CL.store_settings:
			home.settings.update()
			raise Incomplete(Ack())

		if CL.help:
			#command_help(object_type, argument)
			raise Incomplete(None)

		if CL.point_of_origin == POINT_OF_ORIGIN.START_ORIGIN:
			daemonize()

		locking = sticky or model or tmp

		args = {k: from_any(v) for k, v in settings.items()}

		output = run_object(home, role, object_type, args, logs, locking, self_cleaning)
	except (CodecError, ValueError, KeyError) as e:
		s = str(e)
		output = Faulted(s)
	except Incomplete as e:
		output = e.value

	def end():
		exit_status = 0
		if isinstance(output, Faulted):
			exit_status = output.exit_status if output.exit_status is not None else FAULTY_EXIT
			if not CL.pure_object:
				object_error(output)
				return exit_status

		object_output(output)
		return exit_status

	PB.output_value = output
	PB.exit_status = end()
