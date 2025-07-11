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

"""Directory at the GROUP scope.

Starts and monitors a collection of processes, according to the materials
it finds in a folder (i.e. home_path) and optional search criteria.

An empty list of patterns implies "all roles". A non-empty list of
patterns that fails to match anything is considered an error.

Termination is by intervention (i.e. control-c) or termination of the
child processes. There are several variations on this general theme;

* termination of all processes, retries optional (the default),
* termination of any single process, retries optional (see one_and_all),
* termination of a specified process, retries optional (see main_role).
"""
__docformat__ = 'restructuredtext'

import re
import layer_cake as lc

#
#
DEFAULT_GROUP = 'group'

class INITIAL: pass
class ENQUIRING: pass
class RUNNING: pass
class RETURNING: pass
class GROUP_RETURNING: pass

class Group(lc.Threaded, lc.StateMachine):
	def __init__(self, *search,
			directory_at_host: lc.HostPort=None, directory_at_lan: lc.HostPort=None,
			retry: lc.RetryIntervals=None, one_and_all=False, main_role: str=None):
		lc.Threaded.__init__(self)
		lc.StateMachine.__init__(self, INITIAL)
		self.search = search			# List or re's.
		self.directory_at_host = directory_at_host
		self.directory_at_lan = directory_at_lan
		self.retry = retry
		self.one_and_all = one_and_all
		self.main_role = main_role

		self.home_path = lc.CL.home_path or lc.DEFAULT_HOME
		self.role_name = lc.CL.role_name or DEFAULT_GROUP

		self.machine = []				# Compiled re's.
		self.home = {}					# Roles matched by patterns.
		self.ephemeral = None			# The connect_to_directory value for child processes.
		self.interval = {}				# Interval iterators for each role.
		self.group_returned = {}		# Values returned by self-terminating processes

def Group_INITIAL_Start(self, message):
	if self.search:
		s = ', '.join(self.search)
		self.trace(f'Search "{s}"')

	connect_to = self.directory_at_host or self.directory_at_lan
	accept_at = lc.HostPort('127.0.0.1', 0)

	self.directory = self.create(lc.ObjectDirectory, directory_scope=lc.ScopeOfDirectory.GROUP,
		connect_to_directory=connect_to,
		accept_directories_at=accept_at)
	self.assign(self.directory, 0)

	self.send(lc.Enquiry(), self.directory)
	return ENQUIRING

def Group_ENQUIRING_HostPort(self, message):
	self.ephemeral = message					# This is accept_directories_at.

	# Load all the roles.
	home = lc.open_home(self.home_path)
	if home is None:
		self.complete(lc.Faulted(f'cannot open path "{self.home_path}"'))

	# Compile all the patterns.
	for s in self.search:
		try:
			m = re.compile(s)
		except re.error as e:
			self.complete(lc.Faulted(f'cannot compile search "{s}"', str(e)))
		self.machine.append(m)

	# Scan for roles matching a pattern.
	if self.machine:
		def match(name):
			for m in self.machine:
				b = m.match(name)
				if b:
					return True
			return False
		
		home = {k: v for k, v in home.items() if match(k)}
		if not home:
			s = ', '.join(self.search)
			self.complete(lc.Faulted(f'No roles matching "{s}"'))

	elif not home:
		self.complete(lc.Faulted(f'No roles at location "{self.home_path}"'))

	# Start the roles in this non-empty list.
	for k, v in home.items():
		a = self.create(lc.ProcessObject, v,
			home_path=self.home_path, role_name=k, top_role=True,
			directory_scope=lc.ScopeOfDirectory.PROCESS, connect_to_directory=self.ephemeral)
		self.assign(a, k)

	# Remember for restarts.
	self.home = home
	return RUNNING

def Group_ENQUIRING_Faulted(self, message):
	self.complete(message)

def Group_ENQUIRING_Stop(self, message):
	self.complete(lc.Aborted())

def Group_RUNNING_Returned(self, message):
	d = self.debrief()
	if isinstance(d, lc.OnReturned):			# Restart callbacks.
		d(self, message)
		return RUNNING

	if d == self.main_role:						# Declared "main" - no retries.
		if not self.working():					# Includes ProcessObjects and restart callbacks.
			self.complete(message.value)

		self.abort(message.value)
		return RETURNING

	#
	self.group_returned[d] = message.value

	if self.retry is None:						# Not configured for restarts.
		if not self.working():					# As above.
			self.complete(self.group_returned)

		if self.one_and_all:
			self.abort()
			return GROUP_RETURNING

		return RUNNING

	i = self.interval.get(d, None)
	if i is None:
		i = lc.smart_intervals(self.retry)
		self.interval[d] = i

	try:
		seconds = next(i)
		self.trace(f'Restart "{d}" ({seconds} seconds)')
	except StopIteration:
		if not self.working():					# As above.
			self.complete(self.group_returned)

		if self.one_and_all:
			self.abort()
			return GROUP_RETURNING

		return RUNNING

	def restart(self, value, args):
		a = self.create(lc.ProcessObject, self.home[args.role],
			home_path=self.home_path, role_name=args.role, top_role=True,
			directory_scope=lc.ScopeOfDirectory.PROCESS, connect_to_directory=self.ephemeral)
		self.assign(a, args.role)

	# Run a no-op with the desired timeout.
	a = self.create(lc.GetResponse, lc.Enquiry(), lc.NO_SUCH_ADDRESS, seconds=seconds)
	self.on_return(a, restart, role=d)
	return RUNNING

def Group_RUNNING_Faulted(self, message):
	if not self.working():
		self.complete(message)

	self.abort(message.value)
	return RETURNING

def Group_RUNNING_Stop(self, message):
	if not self.working():
		self.complete(lc.Aborted())

	self.abort(lc.Aborted())
	return RETURNING

def Group_RETURNING_Returned(self, message):
	d = self.debrief()
	if isinstance(d, lc.OnReturned):		# Restart callbacks.
		pass

	if not self.working():					# Includes ProcessObjects and restart callbacks.
		self.complete(self.aborted_value)

	return RETURNING

def Group_GROUP_RETURNING_Returned(self, message):
	d = self.debrief()
	if isinstance(d, lc.OnReturned):		# Restart callbacks.
		pass
	else:
		self.group_returned[d] = message.value

	if not self.working():					# Includes ProcessObjects and restart callbacks.
		self.complete(self.group_returned)

	return GROUP_RETURNING


GROUP_DISPATCH = {
	INITIAL: (
		(lc.Start,),
		()
	),
	ENQUIRING: (
		(lc.HostPort, lc.Faulted, lc.Stop),
		()
	),
	RUNNING: (
		(lc.Returned, lc.Faulted, lc.Stop),
		()
	),
	RETURNING: (
		(lc.Returned,),
		()
	),
	GROUP_RETURNING: (
		(lc.Returned,),
		()
	),
}

lc.bind(Group, GROUP_DISPATCH, return_type=lc.MapOf(lc.Unicode(),lc.Any()))

def main():
	# See send(lc.Enquiry()) and Group_ENQUIRING_HostPort for how
	# this process acquires the right listening configuration.
	# Unless there is an explicit argument this will open a listen
	# port at 127.0.0.1:0 (i.e. ephemeral). If the directory
	# is presented with pub-subs for higher levels and no connect
	# address has been specified, it will auto-connect to
	# DIRECTORY_AT_HOST (e.g. 127.0.0.1:DIRECTORY_PORT)
	lc.create(Group)

if __name__ == '__main__':
	main()
