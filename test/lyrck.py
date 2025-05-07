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

"""Directory at the LAN scope.

Run the pub-sub name service at the LAN level. Connected to by directories at
HOST level, i.e. as part of the ObjectDirectory.auto_connect(), driven by the
pub-sub activity within associated, underlying PROCESS(es).

This directory needs an HTTP/web interface for the management
of WAN connection credentials. This is the second level where
WAN connectivity is supported, and possible the better configuration
from a security pov.

The other level supporting WAN connectivity is at HOST.
"""
__docformat__ = 'restructuredtext'

import os
import signal
import re
import layer_cake as lc


#
def layer_cake(self, *word):
	# At [0] is the tuple created by command_sub_arguments() based on the
	# presence of a valid sub-command name, or its None.
	sub = word[0]
	word = word[1:]

	if sub is None:
		return
	sub_command, jump, sub_args, remainder = sub

	# Transfer to sub function.
	return jump(self, word, remainder, **sub_args)

lc.bind(layer_cake)

#
#
def create(self, word, remainder):
	# [0] home
	home_path = word_i(word, 0) or lc.CL.home_path or lc.DEFAULT_HOME

	cannot_create = f'cannot create "{home_path}"'
	if os.path.isfile(home_path):
		return lc.Faulted(cannot_create, 'existing file')

	elif os.path.isdir(home_path):
		return lc.Faulted(cannot_create, 'already exists')

	try:
		lc.Folder(home_path)
	except OSError as e:
		return lc.Faulted(cannot_create, str(e))

	return None

lc.bind(create)

#
#
def add(self, word, remainder, count: int=None, start: int=0):
	executable = word_i(word, 0)
	role_name = word_i(word, 1) or lc.CL.role_name 
	home_path = word_i(word, 2) or lc.CL.home_path or lc.DEFAULT_HOME

	if executable is None:
		return lc.Faulted('cannot add role', 'no module specified')
	bp = lc.breakpath(executable)

	role_name = role_name or bp[1]
	if role_name is None:
		return lc.Faulted('cannot add role', 'no role specified')

	cannot_add = f'cannot add "{role_name}"'

	home = lc.open_home(home_path)
	if home is None:
		return lc.Faulted(cannot_add, f'home path "{home_path}" does not exist or contains unexpected/incomplete materials')

	if count is None:
		role_call = [role_name]
	elif 2 <= count <= 1000:
		role_call = [f'{role_name}-{i}' for i in range(start, start + count)]
	else:
		return lc.Faulted(cannot_add, 'expecting count in the range 2...1000')

	c = set(home.keys()) & set(role_call)
	if c:
		s = ','.join(c)
		return lc.Faulted(cannot_add, f'collision of roles "{s}"')

	# Arguments (un-decoded) to be forwarded to the role process(es).
	kv = {}
	kv.update(remainder[0])
	kv.update(remainder[1])

	self.console(executable=executable, role_name=role_name, home_path=home_path, **kv)

	for r in role_call:
		a = self.create(lc.ProcessObject, executable, role_name=r, home_path=home_path, create_role=True, **kv)
		m = self.input()
		if not isinstance(m, lc.Returned):
			return lc.Faulted(cannot_add, f'unexpected process response {m}')

		if isinstance(m.value, lc.Faulted):
			return m.value

		if not isinstance(m.value, lc.CommandResponse):
			return lc.Faulted(cannot_add, f'unexpected command response {m.value}')

	return None

lc.bind(add)

#
#
def list_(self, search, remainder, long_listing: bool=False):
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_list = f'cannot list "{home_path}"'

	home = home_listing(self, home_path, search)
	if home is None:
		return lc.Faulted(cannot_list, f'does not exist or contains unexpected/incomplete materials')

	keys = sorted(home.keys())
	for k in keys:
		v = home[k]
		if long_listing:
			print(f'{k}\t{v.executable_file()}')
			continue
		print(k)

	return None

lc.bind(list_)

#
#
def update(self, word, remainder, count: int=None, start: int=0):
	role_name = word_i(word, 0) or lc.CL.role_name 
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	if role_name is None:
		return lc.Faulted('cannot update role (no role specified)')

	cannot_update = f'cannot update "{role_name}"'

	home = lc.open_home(home_path)
	if home is None:
		return lc.Faulted(cannot_update, f'does not exist or contains unexpected/incomplete materials')

	if count is None:
		role_call = [role_name]
	elif 2 <= count <= 1000:
		role_call = [f'{role_name}-{i}' for i in range(start, start + count)]
	else:
		return lc.Faulted(cannot_update, 'expecting count in the range 2...1000')

	d = set(role_call) - set(home.keys())
	if d:
		s = ','.join(d)
		return lc.Faulted(cannot_update, f'missing roles "{s}"')

	# Arguments (un-decoded) to forward to role process(es).
	kv = {}
	kv.update(remainder[0])
	kv.update(remainder[1])

	self.console(role_name=role_name, home_path=home_path, **kv)

	for r in role_call:
		a = self.create(lc.ProcessObject, home[r], role_name=r, home_path=home_path, update_role=True, **kv)
		m = self.input()
		if not isinstance(m, lc.Returned):
			return lc.Faulted(cannot_update, f'unexpected process response {m}')

		if isinstance(m.value, lc.Faulted):
			return m.value

		if not isinstance(m.value, lc.CommandResponse):
			return lc.Faulted(cannot_update, f'not a proper command response {m.value}')

	return None

lc.bind(update)

#
#
def delete(self, search, remainder, all: bool=False):
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_delete = f'cannot delete from "{home_path}"'
	if search:
		home = home_listing(self, home_path, search)
	elif all:
		home = lc.open_home(home_path)
		if not home:
			return lc.Faulted(cannot_delete, f'does not exist or unexpected/incomplete materials')
	else:
		return lc.Faulted(cannot_delete, f'no roles specified, use --all?')

	try:
		running = home_running(self, home)
		if not running:
			for k, v in home.items():
				home_role = os.path.join(home_path, k)
				lc.remove_folder(home_role)
	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	if running:
		r = ','.join(running.keys())
		return lc.Faulted(cannot_delete, f'roles "{r}" are currently running')

	return None

lc.bind(delete)

#
#
def destroy(self, word, remainder):
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_destroy = f'cannot destroy "{home_path}"'

	# Most basic checks.
	if os.path.isfile(home_path):
		return lc.Faulted(cannot_destroy, f'existing file')

	elif not os.path.isdir(home_path):
		return lc.Faulted(cannot_destroy, f'not a folder')

	# Need valid contents to be able to check
	# process status.
	home = lc.open_home(home_path)
	if home is None:
		return lc.Faulted(cannot_destroy, f'does not exist or unexpected/incomplete materials')

	try:
		running = home_running(self, home)
		if not running:
			lc.remove_folder(home_path)
	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	if running:
		r = ','.join(running.keys())
		return lc.Faulted(cannot_destroy, f'running roles "{r}"')

	return None

lc.bind(destroy)

#
#
def run(self, search, remainder, main_role: str=None):
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_run = f'cannot run "{home_path}"'
	if search:
		home = home_listing(self, home_path, search)
	else:
		home = lc.open_home(home_path)
		if not home:
			return lc.Faulted(cannot_run, f'does not exist or unexpected/incomplete materials')

	try:
		kv = {}
		if main_role is not None:
			kv['main_role'] = main_role

		running = home_running(self, home)
		if not running:
			a = self.create(lc.ProcessObject, 'group_cake', *search, origin=lc.ProcessOrigin.RUN, **kv)
			self.assign(a, 0)
			m = self.input()
			if isinstance(m, lc.Returned):
				self.debrief()
				return m.value
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()

	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	if running:
		r = ','.join(running.keys())
		return lc.Faulted(cannot_run, f'roles "{r}" are already running')

	return None

lc.bind(run)

#
#
def start(self, search, remainder, main_role: str=None):
	home_path = lc.CL.home_path or lc.DEFAULT_HOME
	home_path = os.path.abspath(home_path)

	cannot_start = f'cannot start "{home_path}"'
	if search:
		home = home_listing(self, home_path, search)
	else:
		home = lc.open_home(home_path)
		if not home:
			return lc.Faulted(cannot_start, f'does not exist or unexpected/incomplete materials')

	try:
		kv = {}
		if main_role is not None:
			kv['main_role'] = main_role

		running = home_running(self, home)
		if not running:
			a = self.create(lc.ProcessObject, 'group_cake', *search,
				origin=lc.ProcessOrigin.START,
				home_path=home_path,
				**kv)
			self.assign(a, 0)
			m = self.input()
			if isinstance(m, lc.Returned):
				self.debrief()
				return m.value
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()

	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	if running:
		r = ','.join(running.keys())
		return lc.Faulted(cannot_start, f'roles "{r}" are already running')

	return None

lc.bind(start)

#
#
def stop(self, word, remainder, group_name: str=None):
	group_name = word_i(word, 0) or 'group_cake'
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	cannot_stop = f'cannot stop "{group_name}"[{home_path}]'
	home = lc.open_home(home_path)
	if not home:
		return lc.Faulted(cannot_stop, f'does not exist or unexpected/incomplete materials')

	try:
		running = home_running(self, home)
		if not running:
			return lc.Faulted(cannot_stop, f'nothing running')
		parent_pid = set()

		for k, v in running.items():
			parent_pid.add(v.parent_pid)

		for p in parent_pid:
			os.kill(p, signal.SIGINT)

	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	return None

lc.bind(stop)

#
#
def status(self, search, remainder):
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_status = f'cannot query status "{home_path}"'
	home = home_listing(self, home_path, search)
	if not home:
		return lc.Faulted(cannot_status, f'does not exist or unexpected/incomplete materials')

	try:
		running = home_running(self, home)
		if not running:
			return lc.Faulted(cannot_status, f'nothing running')

	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	for k, v in running.items():
		print(f'[{v.pid}] {k}')

	return None

lc.bind(status)

# Functions supporting the
# sub-commands.
def word_i(word, i):
	'''Return the i-th element of word, if its long enough. Return element or None.'''
	if i < len(word):
		return word[i]
	return None

def home_listing(self, home_path, search):
	'''Load the contents of home_path and search for matching roles. Return dict[str,role] or None.'''
	home = lc.open_home(home_path)
	if home is None:
		self.complete(lc.Faulted(f'cannot list "{home_path}" (does not exist or contains unexpected/incomplete materials)'))

	# Compile all the patterns.
	machine = []
	for s in search:
		try:
			m = re.compile(s)
		except re.error as e:
			self.complete(lc.Faulted(f'cannot list "{home_path}"', str(e)))
		machine.append(m)

	# Scan for roles matching a pattern.
	if machine:
		def match(name):
			for m in machine:
				b = m.match(name)
				if b:
					return True
			return False
		
		home = {k: v for k, v in home.items() if match(k)}
		if not home:
			s = ', '.join(search)
			self.complete(lc.Faulted(f'cannot list "{home_path}"', f'no roles matching "{s}"'))

	return home

#a = root.create(head_lock, home.lock.path, 'head')

def home_running(self, home):
	'''Scan lock files for the given dict of roles. Return list of those that are running.'''
	running = {}
	for k, v in home.items():
		a = self.create(lc.head_lock, v.lock.path, 'head')
		self.assign(a, k)
		m, i = self.select(lc.Ready, lc.Returned)
		if isinstance(m, lc.Returned):	# Cannot lock.
			r = self.debrief()
			running[r] = m.value	# LockedOut

	return running

#
#
table = [
	# CRUD for a set of role definitions.

	create,		# Create a new, empty set of role definitions.
	add,		# Add one (or more) roles.
	list_,		# List the set of roles.
	update,		# Modify the settings for one (or more) roles.
	delete,		# Delete one (or more, or all) roles.
	destroy,	# Remove all trace of the set of definitions.

	run,
	start,
	stop,
	status
]

# For package scripting.
def main():
	lc.create(layer_cake, object_table=table, strict=False)

if __name__ == '__main__':
	main()
