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

import os
import re
import layer_cake as lc

#
#
DEFAULT_HOME = '.layer-cake'
DEFAULT_GROUP = 'group.default'

class Group(lc.Point, lc.Stateless):
	def __init__(self, *search, retry: lc.RetryIntervals=None, one_and_all=False, main_role=None):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.search = search			# List or re's.
		self.retry = retry
		self.one_and_all = one_and_all
		self.main_role = main_role

		self.home_path = lc.CL.home_path or DEFAULT_HOME
		self.role_name = lc.CL.role_name or DEFAULT_GROUP

		self.machine = []				# Compiled re's.
		self.home = {}					# Roles matched by patterns.
		self.ephemeral = None			# The connect_to_directory value for child processes.
		self.returned = {}				# Values returned by self-terminating processes
		self.interval = {}				# Interval iterators for each role.
		self.clearing = None			# Termination initiated by Stop or Faulted.
		self.aborted = False

def Group_Start(self, message):
	if self.search:
		s = ', '.join(self.search)
		self.console(f'Search "{s}"')
	self.send(lc.Enquiry(), lc.PD.directory)	# Request the accept_directories_at value.

def Group_HostPort(self, message):
	self.ephemeral = message					# This is accept_directories_at.

	# Load all the roles.
	home = lc.open_home(self.home_path)
	if home is None:
		self.complete(lc.Faulted(f'Cannot open path "{self.home_path}"'))

	# Compile all the patterns.
	for s in self.search:
		try:
			m = re.compile(s)
		except re.error as e:
			self.complete(lc.Faulted(f'Cannot compile search "{s}"', str(e)))
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
		#origin=lc.ProcessOrigin.RUN,
		a = self.create(lc.ProcessObject, v,
			home_path=self.home_path, role_name=k,
			directory_scope=lc.ScopeOfDirectory.PROCESS, connect_to_directory=self.ephemeral)
		self.assign(a, k)

	# Remember for restarts.
	self.home = home

def Group_Returned(self, message):
	d = self.debrief()
	if isinstance(d, lc.OnReturned):			# Restart callbacks.
		d(self, message)
		return

	# A role has terminated.
	# Was this prompted by a Stop or Faulted.
	if self.clearing:
		if not self.working():					# Includes ProcessObjects and restart callbacks.
			self.complete(self.clearing)
		return

	# Un-prompted termination, i.e. not stopped.
	self.returned[d] = message.value

	if self.aborted:
		if not self.working():					# Includes ProcessObjects and restart callbacks.
			self.complete(self.returned)
		return

	if d == self.main_role:						# Declared "main" - no retries.
		if not self.working():					# Includes ProcessObjects and restart callbacks.
			self.complete(self.returned)

		if not self.aborted:
			self.abort()
			self.aborted = True
		return

	if self.retry is None:						# Not configured for restarts.
		if not self.working():					# As above.
			self.complete(self.returned)

		if self.one_and_all and not self.aborted:		# Take everything with it.
			self.abort()
			self.aborted = True
		return

	i = self.interval.get(d, None)
	if i is None:
		i = lc.smart_intervals(self.retry)
		self.interval[d] = i

	try:
		seconds = next(i)
		self.console(f'Restart "{d}" ({seconds} seconds)')
	except StopIteration:
		if not self.working():					# No ProcessObjects and no restarts.
			self.complete(self.returned)

		if self.one_and_all and not self.aborted:		# Take everything with it.
			self.abort()
			self.aborted = True
		return

	def restart(self, value, args):
		# origin=lc.ProcessOrigin.RUN,
		a = self.create(lc.ProcessObject, self.home[args.role],
			home_path=self.home_path, role_name=args.role,
			directory_scope=lc.ScopeOfDirectory.PROCESS, connect_to_directory=self.ephemeral)
		self.assign(a, args.role)

	# Run a no-op with the desired timeout.
	a = self.create(lc.GetResponse, lc.Enquiry(), lc.NO_SUCH_ADDRESS, seconds=seconds)
	self.callback(a, restart, role=d)

def Group_Faulted(self, message):
	if not self.working():
		self.complete(message)

	self.clearing = message
	self.abort()

def Group_Stop(self, message):
	if not self.working():
		self.complete(lc.Aborted())

	self.clearing = lc.Aborted()
	self.abort()

lc.bind(Group, (lc.Start, lc.HostPort, lc.Returned, lc.Faulted, lc.Stop), return_type=lc.MapOf(lc.Unicode(),lc.Any()))


if __name__ == '__main__':
	lc.create(Group)
