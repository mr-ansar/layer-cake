# Author: Scott Woods <scott.suzuki@gmail.com>
# MIT License
#
# Copyright (c) 2017-2022
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

"""Makes of a standard executable.

Blah.
"""
__docformat__ = 'restructuredtext'

__all__ = [
    'XYZ',
	'home',
    'Manifest',
    'log_to_stderr',
    'run',
]

import os
import sys
import signal
import io
import time
import ansar.encode as ar
import ansar.create.point as pt
import ansar.create.timing as tm
from .space import set_queue
from .point import Point, Channel, bind_point, bind_function, object_dispatch, sync_complete
from .lifecycle import Stop, Completed, Enquiry, Ack
from .log import LogAgent

XYZ = None

def home():
	return XYZ

#
#
def log_to_stderr(log):
    pid = os.getpid()
    mark = time.strftime('%Y-%m-%dT%H:%M:%S', log.stamp)
    name = log.name.split('.')[-1]
    state = log.state
    if state is None:
        p = '[%06d] %s %s <%08x>%s - %s\n' % (pid, mark, log.tag, log.address[-1], name, log.text)
    else:
        p = '[%06d] %s %s <%08x>%s[%s] - %s\n' % (pid, mark, log.tag, log.address[-1], name, state, log.text)
    sys.stderr.write(p)
    sys.stderr.flush()

#
#
class ComponentFailed(Exception):
    def __init__(self, condition, explanation):
        Exception.__init__(self)
        self.condition = condition
        self.explanation = explanation

    def __str__(self):
        s = '%s, %s' % (self.condition, self.explanation)
        return s

#
#
FINAL_WORD = '''******************************************
******************************************
*** STANDARD COMPONENTRY FAULT ***********
*** COMMAND REQUESTED RETURN ON STDOUT ***
*** AND ENCODING FAILS COMPLETELY ********
*** BELOW ARE THE INTENDED RETURN ********
*** AND THE RELATED ENCODING ERROR *******
*** %r ***
*** %s ***
******************************************
******************************************'''
termination = None

def signal_termination(number, frame):
    global termination
    termination = number

def run_frame(self, one_of_these, passing_these, version):
	# Application is up and running. Wait for completion of the
	# group or a stop instruction from main thread, i.e. post
	# a signal.

	a = self.create(one_of_these, passing_these, version)
	m = self.select(Completed, Stop)
	if isinstance(m, Completed):
		# The termination is coming from the application.
		# Use the common termination mechanism marking
		# it with assigned number (SIGUSR1)
		global termination
		termination = signal.SIGUSR1
		return m.value

	# Received the stop instruction. Pass it to the
	# group and then wait for it to terminate.
	self.send(m, a)
	m = self.select(Completed)
	return m.value

bind_function(run_frame, lifecycle=False, message_trail=False, execution_trace=False, user_logs=ar.USER_LOG_NONE)

SHIPMENT_TRUE = 'True'

SHIPMENT_WITH_QUOTES = """{
	"value": "%s"
}"""

SHIPMENT_WITHOUT_QUOTES = """{
	"value": %s
}"""

# From w2p {} in codec.py
# The set of types decoded from a JSON string.
QUOTED_TYPE = (ar.Character, ar.Rune,
	ar.Block, ar.String, ar.Unicode,
	ar.WorldTime, ar.TimeDelta, ar.ClockTime, ar.TimeSpan,
	ar.UUID,
	ar.Enumeration)

def get_command_line(passing_these):
	rt = passing_these.__art__

	def short_to_long(a):
		for k, _ in rt.value.items():
			if k[0] == a:
				return k
		return None

	# Attempt to override the named member
	def override(k, v):
		# Unknown name errors and
		# codec errors
		try:
			t = rt.value[k]
		except KeyError as e:
			s = 'unknown setting "%s"' % (k,)
			raise ComponentFailed(s, 'dump and verify')
		if isinstance(t, QUOTED_TYPE):
			v = SHIPMENT_WITH_QUOTES % (v,)
		else:
			v = SHIPMENT_WITHOUT_QUOTES % (v,)
		try:
			encoding = ar.CodecJson()
			v, _ = encoding.decode(v, t)
		except ar.CodecFailed as e:
			s = 'cannot decode value for "%s"' % (k,)
			raise ComponentFailed(s, 'format or type problem?')
		setattr(passing_these, k, v)

	for f in sys.argv[1:]:
		if f.startswith(ANSAR_DASH):
			continue
		elif f.startswith('--'):
			try:
				i = f.index('=')
				k = f[2:i]
				v = f[i + 1:]
			except ValueError:
				k = f[2:]
				v = SHIPMENT_TRUE
		elif f.startswith('-'):
			try:
				i = f.index('=')
				n = f[1:i]
				v = f[i + 1:]
			except ValueError:
				k = f[1:]
				n = SHIPMENT_TRUE
			k = short_to_long(n)
			if k is None:
				s = 'unknown short setting "%s"' % (n[0],)
				raise ComponentFailed(s, 'dump and verify')
		else:
			s = 'cannot accept setting "%s"' % (f,)
			raise ComponentFailed(s, 'dash or double-dash settings only')
		# We have a key (somethings verified) and an item
		# of command line text
		override(k, v)

def get_stdin(passing_these):
	utf8 = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='strict')
	input = utf8.read()
	try:
		codec = ar.CodecJson()
		a, v = codec.decode(input, ar.UserDefined(type(passing_these)))
	except ar.CodecFailed as e:
		s = str(e)
		raise ComponentFailed('cannot decode stdin', s)
	return a, v

def get_settings(settings, t):
	try:
		a, v = settings.recover()
	except ar.CodecFailed as e:
		s = str(e)
		raise ComponentFailed('cannot decode settings', s)
	return a, v

def put_stdout(r):
	try:
		h = home()
		p = not h.home and not h.role
		codec = ar.CodecJson(pretty_format=p)
		output = codec.encode(r, ar.Any())
		if p:
			output += '\n'
	except ar.CodecFailed as e:
		s = str(e)
		raise ComponentFailed('cannot encode stdout', s)
	return output

ANSAR_DASH = '--ansar-'

root_queue = None

#
#
class MainChannel(Channel):
    def __init__(self):
        Channel.__init__(self)

bind_point(MainChannel, lifecycle=False, message_trail=False, execution_trace=False, user_logs=ar.USER_LOG_NONE)

#
#
def get_root(logs):
	# Async entry.
	global root_queue
	p = Point()
	root = p.create(MainChannel)

	# Populate with standard resources
	# logging, timers, threads...
	if logs:
		pt.log_address = root.create(LogAgent, log_to_stderr)
	else:
		pt.log_address = root.create(LogAgent, log_to_stderr)

	pt.timer_address = root.create(tm.CountdownTimer)
	ticker = root.create(tm.timer_circuit, pt.timer_address)

	# TBD - start all the named threads.

	root_queue = root.create(object_dispatch)
	set_queue(None, root_queue)

	return root

def drop_root(code, root):
	# TBD - stop the named threads.
	root.stop(root_queue)
	tm.circuit_ticking = False
	root.select(Completed)
	root.ask(Enquiry(), Ack, pt.log_address)
	root.stop(pt.timer_address)
	root.stop(pt.log_address)
	sync_complete(root)
	sys.exit(code)

def ansar_flags():
	kv = {}
	for a in sys.argv[1:]:
		if a.startswith(ANSAR_DASH):
			try:
				i = a.index('=')
				k = a[2:i]
				v = a[i + 1:]
			except ValueError:
				k = a[2:]
				v = 'y'
			kv[k] = v
	return kv

def dump_settings(a):
	try:
		encoding = ar.CodecJson(pretty_format=True)
		output = encoding.encode(a, ar.UserDefined(type(a)))
		sys.stdout.write(output)
	except ar.CodecFailed as e:
		s = 'cannot dump settings %s' % (str(e),)
		raise ComponentFailed(s, 'internal problem')

def home_folder(h):
	expanded = [h]
	for p in home().role_name.split('.'):
		expanded.append('child')
		expanded.append(p)
	expanded = os.sep.join(expanded)
	return expanded

class Manifest(object):
	def __init__(self, home):
		if home:
			self.home = ar.Folder(home)
			self.settings = home.folder('settings')
			self.bin = home.folder('bin')
			self.logs = home.folder('logs')
		else:
			self.home = None
			self.settings = None
			self.bin = None
			self.logs = None
		self.bin_path = None
		self.bin_env = None
		self.role = None
		self.role_name = None
		self.role_settings = None
		self.role_logs = None
		self.store = lambda : False

	def overrides(self, settings, bin, logs):
		if settings: self.settings = ar.Folder(settings)
		if bin: self.bin = ar.Folder(bin)
		if logs: self.logs = ar.Folder(logs)

		if self.bin:
			bin_env = dict(os.environ)
			old = bin_env.get('PATH', None)
			if old:
				bin_path = '%s:%s' % (self.bin.path, old)
			else:
				bin_path = self.bin.path
			bin_env['PATH'] = bin_path
			self.bin_path = bin_path
			self.bin_env = bin_env

	def identify(self, role, passing):
		self.role = role
		self.role_name = role or '.root'
		if self.settings:
			t = type(passing)
			self.role_settings = self.settings.file(self.role_name, ar.UserDefined(t), create_default=True)
		
		if self.logs:
			self.role_logs = self.logs.folder(self.role_name)

	def storage(self, passing):
		if self.role_settings:
			def store():
				try:
					self.role_settings.store(passing)
				except ar.FileFailure as e:
					return False
				return True
			self.store = store

def run(one_of_these, passing_these):
	flags = ansar_flags()	# Get all those framework attributes.

	ansar_io = flags.get('ansar-io', 'o')
	ansar_dump = flags.get('ansar-dump', None)

	ansar_role = flags.get('ansar-role', None)
	ansar_home = flags.get('ansar-home', None)

	ansar_settings = flags.get('ansar-settings', None)
	ansar_bin = flags.get('ansar-bin', None)
	ansar_logs = flags.get('ansar-logs', None)

	h = Manifest(ansar_home)
	global XYZ
	XYZ = h
	setattr(sys.modules['ansar.create.framework'], 'XYZ', h)
	# An initial error context before we have a root
	# object to log with. Need to figure out the logging
	# situation before creating the root. Still need to
	# potentially report to the parent or print diagnostic
	# on the console.
	any, error, code = None, None, 0
	try:
		# Start with the top-level folder and the
		# implicit sub-folders.
		
		# Allow explicit sub-folders that may override
		# an implicit setting.
		h.overrides(ansar_settings, ansar_bin, ansar_logs)

		# Now that we have the effective operational
		# environment, assume the role within this process
		# hierarchy.
		h.identify(ansar_role, passing_these)

	except KeyboardInterrupt:
		raise
	except SystemExit:
		raise
	except Exception as e:
		if 'o' in ansar_io:
			s = str(e)
			f = ar.Faulted(condition='cannot resolve folders', explanation=s)
			try:
				encoding = ar.CodecJson()
				any = encoding.encode(f, ar.Any())
			except ar.CodecFailed as e2:
				s2 = str(e2)
				any = FINAL_WORD % (f, s2)
				code = 1
		else:
			error = '%s: %s\n' % (sys.argv[0], str(e,))
			code = 1

		if any:
			utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='strict')
			utf8.write(any)
		elif error:
			sys.stderr.write(error)
		sys.exit(code)

	# Global framework attributes of this process
	# passed from parent, or shell.

	root = get_root(h.role_logs)

	# Make the admin object that becomes convenient access
	# to attributes, resources derived from that command
	# line.

	# Actual application.
	# 3 phases of the executable. Input, object instantiation
	# and output.
	# Default args and normal processing.
	any, error, code = None, None, 0
	try:

		if 'i' in ansar_io:			# Args coming from upstream pipe?
			a, v = get_stdin(passing_these)
		elif h.role_settings:
			a, v = get_settings(h.role_settings, type(passing_these))
		else:
			# Allow command line to set individual members
			# of the settings, overriding compiled/factory
			# defaults.
			get_command_line(passing_these)
			a, v = passing_these, None

		h.storage(a)

		if ansar_dump:
			dump_settings(a)
			drop_root(0, root)

		signal.signal(signal.SIGHUP, signal_termination)    # Hangup of terminal or termination of parent.
		signal.signal(signal.SIGINT, signal_termination)    # Interrupt from keyboard.
		signal.signal(signal.SIGQUIT, signal_termination)   # Quit from keyboard.
		signal.signal(signal.SIGTERM, signal_termination)   # Termination (from platform?)
		signal.signal(signal.SIGUSR1, signal_termination)   # Normal application termination.

		# Put the application in dedicated, non-main thread.
		a = root.create(run_frame, one_of_these, a, v)

		# Damn. Signals no longer bump system calls out
		# of their work. Cant seem to get exceptions
		# working either.
		while termination is None:
			time.sleep(0.25)

		# If termination is not coming from the app then
		# we need to use explicit stop messaging.
		if termination != signal.SIGUSR1:
			root.send(Stop(), a)
		m = root.select(Completed)
		r = m.value

		if 'o' in ansar_io:				# Result going to downstream pipe?
			any = put_stdout(r)
	except ComponentFailed as e:
		if 'o' in ansar_io:
			f = ar.Faulted(condition=e.condition, explanation=e.explanation)
			try:
				encoding = ar.CodecJson()
				any = encoding.encode(f, ar.Any())
			except ar.CodecFailed as e2:
				s2 = str(e2)
				any = FINAL_WORD % (f, s2)
				code = 1
		else:
			error = '%s: %s\n' % (sys.argv[0], str(e,))
			code = 1
	except KeyboardInterrupt:
		raise
	except SystemExit:
		raise
	except Exception as e:
		if 'o' in ansar_io:
			f = ar.Faulted(condition='unexpected exception', explanation=str(e,))
			try:
				encoding = ar.CodecJson()
				any = encoding.encode(f, ar.Any())
			except ar.CodecFailed as e2:
				s2 = str(e2)
				any = FINAL_WORD % (f, s2)
				code = 1
		else:
			error = '%s: %s\n' % (sys.argv[0], str(e,))
			code = 1
	
	# All roads lead to here - normal completion and exceptions.
	# There is either a message to report to a parent or a
	# diagnostic to report to a shell or neither. Then just
	# need to terminate with a code that is zero for success
	# or 1 for failure. In the case of parent-child reporting
	# a succeeful reporting of failure gets an exit code of 0.
	# That indicates a successful communication between parent
	# and child even when the report is of a failure.

	if any:
		utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='strict')
		utf8.write(any)
	elif error:
		sys.stderr.write(error)

	drop_root(code, root)

