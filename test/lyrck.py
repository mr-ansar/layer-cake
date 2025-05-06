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
		running = home_running(self, home_path, home)
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
		r = ','.join(running)
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
		running = home_running(self, home_path, home)
		if not running:
			lc.remove_folder(home_path)
	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	if running:
		r = ','.join(running)
		return lc.Faulted(cannot_destroy, f'running roles "{r}"')

	return None

lc.bind(destroy)

#
#
def word_i(word, i):
	if i < len(word):
		return word[i]
	return None

def home_listing(self, home_path, search):
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

def home_running(self, home_path, home):
	running = []
	for k, v in home.items():
		home_role = os.path.join(home_path, k)
		a = self.create(lc.head_lock, home_role, 'head')
		self.assign(a, k)
		m, i = self.select(lc.Ready, lc.Returned)
		if isinstance(m, lc.Returned):	# Cannot lock.
			r = self.debrief()
			running.append(r)

	return running

#
#
table = [
	# CRUD for a set of role definitions.
	create,
	add,
	list_,
	update,
	delete,
	destroy
]

# For package scripting.
def main():
	lc.create(layer_cake, table, strict=False)

if __name__ == '__main__':
	main()
