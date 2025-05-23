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

"""Layer-cake, command line utility.

CRUD for creation/management of a set of process definitions.
Process orchestration for running images of defintiions.
Access to records of execution.
"""
__docformat__ = 'restructuredtext'

import os
import signal
import re
import datetime
import layer_cake as lc
import layer_cake.rolling_log as rl

from enum import Enum
import calendar

#
GROUP_ROLE = 'group'
GROUP_EXECUTABLE = 'group_cake'

#
def layer_cake(self, *word):
	# At [0] is the tuple created by command_sub_arguments() based on the
	# presence of a valid sub-command name, or its None.
	sub = word[0]
	word = word[1:]

	if sub is None:
		# A non-sub execution of the utility.
		return
	sub_command, jump, sub_args, remainder = sub

	# Catch uncurated args that are not going anywhere.
	if jump not in (create, add, update) and (remainder[0] or remainder[1]):
		a = [k for k in remainder[0].keys()]
		b = [k for k in remainder[1].keys()]
		a.extend(b)
		a = ','.join(a)
		return lc.Faulted(f'cannot execute "{sub_command}"', f'unknown arg(s) "{a}"')

	# Transfer to sub function. Perhaps could be
	# a self.create.
	return jump(self, word, remainder, **sub_args)

lc.bind(layer_cake)

def create(self, word, remainder):
	'''Create a new area on disk to hold process definitions. Return Faulted/None.'''
	home_path = word_i(word, 0) or lc.CL.home_path or lc.DEFAULT_HOME

	cannot_create = f'cannot create "{home_path}"'
	if os.path.isfile(home_path):
		return lc.Faulted(cannot_create, 'existing file')

	elif os.path.isdir(home_path):
		return lc.Faulted(cannot_create, 'already exists')

	self.console('create', home_path=home_path)

	try:
		f = lc.Folder(home_path)
		f.folder('script')
		f.folder('resource')
		f.folder('role')
		f.folder('departures')
		f.folder('arrivals')

	except OSError as e:
		return lc.Faulted(cannot_create, str(e))

	# Folder created by execution of group create-role.
	self.create(lc.ProcessObject, GROUP_EXECUTABLE,
		home_path=home_path,
		role_name=GROUP_ROLE, top_role=True,
		create_role=True,
		remainder_args=remainder)

	m = self.input()
	if not isinstance(m, lc.Returned):
		return lc.Faulted(cannot_create, f'unexpected process response {m}')

	if isinstance(m.value, lc.Faulted):
		return m.value

	# Consume the expected response.
	if not isinstance(m.value, lc.CommandResponse):
		return lc.Faulted(cannot_create, f'unexpected command response {m.value}')

	return None

lc.bind(create)

#
#
def add(self, word, remainder, count: int=None, start: int=0):
	'''Add process definition(s) to an existing store. Return Faulted/None.'''
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

	if role_name.startswith(GROUP_ROLE):
		return lc.Faulted(cannot_add, 'reserved name')

	home = lc.open_home(home_path)
	if home is None:
		return lc.Faulted(cannot_add, f'home path "{home_path}" does not exist or contains unexpected/incomplete materials')

	if count is None:
		role_call = [role_name]
	elif 1 <= count <= 1000:
		role_call = [f'{role_name}-{i}' for i in range(start, start + count)]
	else:
		return lc.Faulted(cannot_add, 'expecting count in the range 1...1000')

	c = set(home.keys()) & set(role_call)
	if c:
		s = ','.join(c)
		return lc.Faulted(cannot_add, f'collision of roles "{s}"')

	self.console('add', executable=executable, role_name=role_name, home_path=home_path)

	for r in role_call:
		a = self.create(lc.ProcessObject, executable,
			home_path=home_path,
			role_name=r, top_role=True,
			create_role=True,
			remainder_args=remainder)
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
def list_(self, search, remainder, long_listing: bool=False, group_role: bool=False, sub_roles: bool=False):
	'''List the process definition(s) in an existing store. Return Faulted/None.'''
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_list = f'cannot list "{home_path}"'

	home = home_listing(self, home_path, search, grouping=group_role, sub_roles=sub_roles)
	if home is None:
		return lc.Faulted(cannot_list, f'does not exist or contains unexpected/incomplete materials')

	s = ','.join(search)
	self.console('list', search=s, home_path=home_path)

	keys = sorted(home.keys())
	for k in keys:
		v = home[k]
		if long_listing:
			home_role = os.path.join(home_path, 'role', k)
			m, _ = lc.storage_manifest(home_role)
			print(f'{k:24} {v.executable_file()} {m.manifests}/{m.listings}/{m.bytes}')
			continue
		print(k)

	return None

lc.bind(list_)

#
#
def update(self, search, remainder, group_role: bool=False, sub_roles: bool=False):
	'''Update details of existing process definition(s). Return Faulted/None.'''
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_update = f'cannot update "{home_path}"'

	home = home_listing(self, home_path, search, sub_roles=sub_roles)
	if home is None:
		return lc.Faulted(cannot_update, f'does not exist or contains unexpected/incomplete materials')

	elif group_role:
		a = self.create(lc.ProcessObject, GROUP_EXECUTABLE,
			home_path=home_path,
			role_name=GROUP_ROLE, top_role=True,
			update_role=True,
			remainder_args=remainder)
		m = self.input()
		if not isinstance(m, lc.Returned):
			return lc.Faulted(cannot_update, f'unexpected process response {m}')

		if isinstance(m.value, lc.Faulted):
			return m.value

		if not isinstance(m.value, lc.CommandResponse):
			return lc.Faulted(cannot_update, f'not a proper command response {m.value}')
		return None

	r = ','.join(home.keys())
	self.console('update', roles=r, home_path=home_path)

	for k, v in home.items():
		a = self.create(lc.ProcessObject, v,
			home_path=home_path,
			role_name=k, top_role=True,
			update_role=True,
			remainder_args=remainder)
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
	'''Delete existing process definition(s). Return Faulted/None.'''
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_delete = f'cannot delete from "{home_path}"'
	if search:
		home = home_listing(self, home_path, search)
	elif all:
		home = lc.open_home(home_path)
		if home is None:
			return lc.Faulted(cannot_delete, f'does not exist or unexpected/incomplete materials')
	else:
		return lc.Faulted(cannot_delete, f'no roles specified, use --all?')

	s = ','.join(search)
	self.console('delete', search=s, home_path=home_path)

	try:
		running = home_running(self, home)
		if running:
			r = ','.join(running.keys())
			return lc.Faulted(cannot_delete, f'roles "{r}" are currently running')

	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	try:
		role_path = os.path.join(home_path, 'role')
		for p in os.listdir(role_path):
			if p.startswith('group'):
				continue
			s = p.split('.')
			if s[0] not in home:
				continue
			home_role = os.path.join(role_path, p)
			lc.remove_folder(home_role)
	except FileNotFoundError as e:
		return lc.Faulted(cannot_delete, str(e))

	return None

lc.bind(delete)

#
#
def destroy(self, word, remainder):
	'''Remove all trace of an existing store. Return Faulted/None.'''
	home_path = word_i(word, 0) or lc.CL.home_path or lc.DEFAULT_HOME

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

	self.console('destroy', home_path=home_path)

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
	'''Execute a subset/all of the process definition(s), to completion. Return Faulted/None.'''
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_run = f'cannot run "{home_path}"'
	if search:
		home = home_listing(self, home_path, search)
	else:
		home = lc.open_home(home_path)
		if not home:
			return lc.Faulted(cannot_run, f'does not exist or unexpected/incomplete materials')

	s = ','.join(search)
	self.console('run', search=s, home_path=home_path)

	try:
		kv = {}
		if main_role is not None:
			kv['main_role'] = main_role

		running = home_running(self, home)
		if not running:
			a = self.create(lc.ProcessObject, GROUP_EXECUTABLE, *search,
				home_path=home_path,
				role_name=GROUP_ROLE, top_role=True,
				origin=lc.ProcessOrigin.RUN,
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
		return lc.Faulted(cannot_run, f'roles "{r}" are already running')

	return None

lc.bind(run)

#
#
def start(self, search, remainder, main_role: str=None):
	'''Start a subset/all of the process definition(s) as background daemons. Return Faulted/None (immediately).'''
	home_path = lc.CL.home_path or lc.DEFAULT_HOME
	home_path = os.path.abspath(home_path)

	cannot_start = f'cannot start "{home_path}"'
	if search:
		home = home_listing(self, home_path, search)
	else:
		home = lc.open_home(home_path)
		if home is None:
			return lc.Faulted(cannot_start, f'does not exist or unexpected/incomplete materials')

	if not home:
		return lc.Faulted(cannot_start, f'empty')

	s = ','.join(search)
	self.console('start', search=s, home_path=home_path)

	try:
		kv = {}
		if main_role is not None:
			kv['main_role'] = main_role

		running = home_running(self, home)
		if not running:
			a = self.create(lc.ProcessObject, GROUP_EXECUTABLE, *search,
				home_path=home_path,
				role_name=GROUP_ROLE, top_role=True,
				origin=lc.ProcessOrigin.START,
				**kv)
			self.assign(a, 0)
			m = self.input()
			if isinstance(m, lc.Returned):
				self.debrief()
				if not isinstance(m.value, lc.CommandResponse):
					return lc.Faulted(cannot_start, f'unexpected response from group')
				return None
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
def stop(self, word, remainder):
	'''Stop the previously started set of background daemons. Return Faulted/None (immediately).'''
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	cannot_stop = f'cannot stop "{home_path}"'
	home = lc.open_home(home_path)
	if home is None:
		return lc.Faulted(cannot_stop, f'does not exist or unexpected/incomplete materials')

	if not home:
		return lc.Faulted(cannot_stop, f'empty')

	self.console('stop', home_path=home_path)

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
def status(self, search, remainder, long_listing: bool=False, group_role: bool=False, sub_roles: bool=False):
	'''Query running/not-running status of background daemons. Return Faulted/None.'''
	home_path = lc.CL.home_path or lc.DEFAULT_HOME

	cannot_status = f'cannot query status "{home_path}"'

	# Get list of roles at home_path, trimmed down
	# according to the list of search patterns.
	home = home_listing(self, home_path, search, grouping=group_role, sub_roles=sub_roles)
	if home is None:
		return lc.Faulted(cannot_status, f'does not exist or unexpected/incomplete materials')

	if not home:
		return lc.Faulted(cannot_status, f'empty')

	s = ','.join(search)
	self.console('status', search=s, home_path=home_path)

	try:
		# Determine the running/idle status of the
		# selected roles.
		running = home_running(self, home)
		if not running:
			return lc.Faulted(cannot_status, f'nothing running')

	finally:
		# Cleanup the locking from inside home_running().
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	now = datetime.datetime.now(lc.UTC)

	orderly = sorted(running.keys())
	def long_status():
		for k in orderly:
			v = home.get(k, None)
			r = running.get(k, None)

			start_stop = v.start_stop()
			s = start_stop[-1]
			if s.start is not None:
				d = now - s.start
				s = short_delta(d)
			else:
				s = '(never started)'
			def dq(pid):
				if pid is None:
					return '0'
				return f'{pid}'
			lc.output_line('%-24s <%s> %s' % (k, dq(r.pid), s))

	def short_status():
		for k in orderly:
			lc.output_line(k)

	if long_listing:
		long_status()
	else:
		short_status()

	return None

lc.bind(status)

#
#
def history(self, word, remainder, long_listing: bool=False, group_role: bool=False):
	'''List the the start/stop record for the specified role. Return Faulted/None.'''
	role_name = word_i(word, 0) or lc.CL.role_name
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	if role_name is None and group_role:
		role_name = GROUP_ROLE

	if role_name is None:
		return lc.Faulted(f'cannot pull history', f'no role specified')
	cannot_history = f'cannot pull history for "{role_name}"'

	home = lc.open_home(home_path, grouping=group_role)
	if home is None:
		return lc.Faulted(cannot_history, f'home at "{home_path}" does not exist or contains unexpected/incomplete materials')

	role = home.get(role_name, None)
	if role is None:
		return lc.Faulted(cannot_history, f'does not exist')

	self.console('history', role_name=role_name, home_path=home_path)

	def long_history():
		now = datetime.datetime.now(lc.UTC)
		for s in role.start_stop():
			start = lc.world_to_text(s.start)
			if s.stop is None:
				lc.output_line('%s ... ?' % (start,))
				continue
			stop = lc.world_to_text(s.stop)
			d = s.stop - s.start
			span = '%s' % (lc.short_delta(d),)
			if isinstance(s.returned, lc.Incognito):
				lc.output_line('%s ... %s (%s) %s' % (start, stop, span, s.returned.type_name))
			else:
				lc.output_line('%s ... %s (%s) %s' % (start, stop, span, s.returned.__class__.__name__))

	def short_history():
		for i, s in enumerate(role.start_stop()):
			now = datetime.datetime.now(lc.UTC)
			d = now - s.start
			start = '%s ago' % (lc.short_delta(d),)
			if s.stop is None:
				lc.output_line('[%d] %s ... ?' % (i, start))
				continue
			d = s.stop - s.start
			stop = lc.short_delta(d)
			if isinstance(s.returned, lc.Incognito):
				lc.output_line('[%d] %s ... %s (%s)' % (i, start, stop, s.returned.type_name))
			else:
				lc.output_line('[%d] %s ... %s (%s)' % (i, start, stop, s.returned.__class__.__name__))

	if long_listing:
		long_history()
	else:
		short_history()
	return None

lc.bind(history)

#
#
class NoFault(object):
	def __init__(self, fault: lc.Any=None):
		self.fault = fault

lc.bind(NoFault)

def returned(self, word, remainder, start: int=None, timeout: float=None, group_role: bool=False):
	'''Print a specific termination value for the specified role. Return Faulted/None.'''
	role_name = word_i(word, 0) or lc.CL.role_name
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	if role_name is None and group_role:
		role_name = GROUP_ROLE

	if role_name is None:
		return lc.Faulted(f'cannot pull return', f'no role specified')
	cannot_returned = f'cannot pull return for "{role_name}"'

	home = lc.open_home(home_path, grouping=group_role)
	if home is None:
		return lc.Faulted(cannot_returned, f'home at "{home_path}" does not exist or contains unexpected/incomplete materials')

	role = home.get(role_name, None)
	if role is None:
		return lc.Faulted(cannot_returned, f'does not exist')

	self.console('returned', role_name=role_name, home_path=home_path)

	start_stop = role.start_stop()
	if len(start_stop) < 1:
		return lc.Faulted(cannot_returned, f'no start/stop records')

	ls = len(start_stop) - 1	# Last stop
	if start is None:
		start = ls
	elif start < 0:
		start = ls + 1 + start

	if start < 0 or start > ls:
		return lc.Faulted(cannot_returned, f'start [{start}] out of bounds')

	# Criteria met - valid row in the table.
	selected = start_stop[start]
	anchor = selected.start

	def no_fault(value):
		if isinstance(value, lc.Faulted):
			return NoFault(value)
		return selected.returned

	# This row has already returned.
	if selected.stop is not None:
		return no_fault(selected.returned)

	# Cannot poll for completion of anything other
	# than the last row.
	if start != ls:
		return lc.Faulted(cannot_returned, f'no record of role[{start}] stopping and never will be')

	if timeout is not None:
		self.start(lc.T1, timeout)

	self.start(lc.T2, 1.0)
	while True:
		m = self.select(lc.Stop, lc.T1, lc.T2)
		if isinstance(m, lc.Stop):
			break
		elif isinstance(m, lc.T1):
			return lc.TimedOut()
		elif isinstance(m, lc.T2):
			r = role.start_stop.resume()
			if len(r) < start:
				return lc.Faulted(cannot_returned, f'lost original start position')
			if r[start].start != anchor:
				return lc.Faulted(cannot_returned, f'lost original start position, datetime anchor')
			if r[start].stop is not None:
				return no_fault(r[start].returned)
			self.start(lc.T2, 1.0)

	return None

lc.bind(returned)

#
#
# Extraction of logs for a role.
#
class TimeFrame(Enum):
	MONTH=0
	WEEK=1
	DAY=2
	HOUR=3 
	MINUTE=4
	HALF=5
	QUARTER=6
	TEN=7
	FIVE=8

def log(self, word, remainder, clock: bool=False,
	rewind: int=None, from_: str=None, last: TimeFrame=None, start: int=None, back=None,
	to: str=None, span=None, count: int=None, sample: str=None, group_role: bool=False, sub_roles: bool=False):
	'''List logging records for the specified process definition. Return Faulted/None.'''
	role_name = word_i(word, 0) or lc.CL.role_name
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	if role_name is None and group_role:
		role_name = GROUP_ROLE

	if role_name is None:
		return lc.Faulted(f'cannot log', f'no role specified')
	cannot_log = f'cannot log "{role_name}"'

	self.console('log', role_name=role_name, home_path=home_path)

	# Initial sanity checks and a default <begin>.
	f = [rewind, from_, last, start, back]
	c = len(f) - f.count(None)
	if c == 0:
		rewind = os.get_terminal_size().lines - 1
	elif c != 1:
		# one of <from>, <last>, <start> or <back> is required
		return lc.Faulted(cannot_log, f'need a rewind, from_, last, start or back')

	t = [to, span, count]
	c = len(t) - t.count(None)
	if c == 0:
		pass		# Default is query to end-of-log or end of start-stop.
	elif c != 1:
		# one of <to>, <span> or <count> is required
		return lc.Faulted(cannot_log, f'need a to, span or count')

	home = lc.open_home(home_path, grouping=group_role, sub_roles=sub_roles)
	if home is None:
		return lc.Faulted(cannot_log, f'home at "{home_path}" does not exist or contains unexpected/incomplete materials')

	role = home.get(role_name, None)
	if role is None:
		return lc.Faulted(cannot_log, f'does not exist')

	begin, end = None, None
	if rewind is not None:
		if rewind < 1:
			return lc.Faulted(cannot_log, f'rewind [{rewind}] out of range')
		begin = rewind			# Rewind expresses the begin and end (count).

	elif from_ is not None:
		begin = world_or_clock(from_, clock)

	elif last is not None:
		begin = from_last(last)
		if begin is None:
			return lc.Faulted(cannot_log, f'last is not a TimeFrame')

	elif start is not None:
		start_stop = role.start_stop()
		if len(start_stop) < 1:
			return lc.Faulted(cannot_log, f'no history available')
		if start < 0:
			y = len(start_stop) + start
		else:
			y = start
		try:
			s = start_stop[y]
		except IndexError:
			return lc.Faulted(cannot_log, f'start [{y} out of range]')
		begin = s.start
		p1 = y + 1
		if p1 < len(start_stop):
			end = start_stop[p1].start
		else:
			end = None
	elif back is not None:
		d = datetime.datetime.now(lc.UTC)
		t = datetime.timedelta(seconds=back)
		begin =  d - t

	count = None
	if to is not None:
		end = world_or_clock(to, clock)
	elif span is not None:
		#t = datetime.timedelta(seconds=span)
		end = begin + span	#t
	elif count is not None:
		count = count
		# Override an assignment associated with "start".
		end = None
	# Else
	#   end remains as the default None or
	#   the stop part of a start-stop.

	# Now that <begin> and <end> have been established, a
	# few more sanity checks.
	if begin is None:
		return lc.Faulted(cannot_log, f'<begin> not defined and not inferred')

	if end is not None and end < begin:
		return lc.Faulted(cannot_log, f'<end> comes before <begin>')

	header = None
	if sample:
		header = sample.split(',')
		if len(header) < 1 or '' in header:
			return lc.Faulted(cannot_log, f'<sample> empty or contains empty column')

	if rewind:
		a = self.create(backward, role, begin)
	elif header:
		a = self.create(sampler, role, begin, end, count, header)
	elif clock:
		a = self.create(clocker, role, begin, end, count)
	else:
		a = self.create(printer, role, begin, end, count)

	m, i = self.select(lc.Stop, lc.Returned)
	if isinstance(m, lc.Stop):
		lc.halt(a)
		m, i = self.select(lc.Returned)
		return lc.Aborted()

	value = m.value
	if value is None:   # Reached the end.
		pass
	elif isinstance(value, lc.Faulted):	 # lc.Failed to complete stream.
		return value
	else:
		return lc.Faulted(cannot_log, f'unexpected reader response')

	return None

lc.bind(log, span=lc.TimeSpan(), back=lc.TimeSpan())

#
#
def edit(self, word, remainder, group_role: bool=False):
	'''Edit the configuration of the specified process defintion. Return Faulted/None.'''
	role_name = word_i(word, 0) or lc.CL.role_name
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	if role_name is None:
		if not group_role:
			return lc.Faulted(f'cannot edit "{home_path}"', f'no role specified')
		role_name = GROUP_ROLE

	cannot_edit = f'cannot edit "{role_name}"'

	home = lc.open_home(home_path, grouping=group_role)
	if home is None:
		return lc.Faulted(cannot_edit, f'does not exist or contains unexpected/incomplete materials')

	try:
		running = home_running(self, home)
		if role_name in running:
			return lc.Faulted(cannot_edit, f'role is running')

	finally:
		self.abort()
		while self.working():
			m, i = self.select(lc.Returned)
			self.debrief()

	r = home.get(role_name, None)
	if r is None:
		return lc.Faulted(cannot_edit, f'does not exist')

	self.console('edit', role_name=role_name, home_path=home_path)

	output = lc.HR.edit_role(self, r)
	return output

lc.bind(edit)

#
#
def snapshot(self, word, remainder,	image_path: str=None):
	'''Store a copy of the composition at home_path, under the '''
	image_path = word_i(word, 0) or image_path
	home_path = word_i(word, 1) or lc.CL.home_path or lc.DEFAULT_HOME

	cannot_snapshot = f'cannot snapshot "{home_path}"'

	if not image_path:
		return lc.Faulted(cannot_snapshot, f'no destination image path')

	home = lc.open_home(home_path, grouping=True, sub_roles=True)
	if home is None:
		return lc.Faulted(cannot_snapshot, f'does not exist or contains unexpected/incomplete materials')


	# Repo modules
	# Read-only executable resources
	# One-time consumable (?)
	# Operational data per role
	# Calculate delta
	# Affected processes (opt stop)
	# Copy complete materials to target device
	# Move to resting places
	# Restart processes
	return None

	# ROLES <home_path>/role/<role>/{settings,executable_file,log_storage}.json ---> <image_path>/defined_role/<role>/*.json
	# SCRIPT <home_path>/script/*.py ---> <image_path>/script/*.py
	# READ-ONLY <home_path>/resource/executable.py/<resources> ---> <image_path>/resource/executable.py/<resources>
	# DATABASE <home_path>/role/<role_name>/model/<model> ---> <image_path>/role/<role_name>/<model>
	# TUNINGS <home_path>/role/<role_name>/<settings> ---> <image_path>/role-settings/<role_name>/<settings> ---> 
	# DELIVERY ./role-model/<role_name>/<model> ---> <home_path>/role/<role_name>/model/<model>
	# INWARD ./role-model/<role_name>/<model> ---> <home_path>/role/<role_name>/model/<model>

	# READ-ONLY ./executable-resource/executable.py/<resources> ---> <home_path>/resource/executable.py/<resources>
	# DATABASE ./role-model/<role_name>/<model> ---> <home_path>/role/<role_name>/model/<model>
	# TUNINGS ./role-settings/<role_name>/<settings> ---> <home_path>/role/<role_name>/<settings>
	# DELIVERY ./role-model/<role_name>/<model> ---> <home_path>/role/<role_name>/model/<model>
	# INWARD ./role-model/<role_name>/<model> ---> <home_path>/role/<role_name>/model/<model>

lc.bind(snapshot)

# Functions supporting the
# sub-commands.
def word_i(word, i):
	'''Return the i-th element of word, if its long enough. Return element or None.'''
	if i < len(word):
		return word[i]
	return None

def home_listing(self, home_path, search, grouping=False, sub_roles=False):
	'''Load the contents of home_path and search for matching roles. Return dict[str,role] or None.'''
	home = lc.open_home(home_path, grouping=grouping, sub_roles=sub_roles)
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

def world_or_clock(s, clock):
	if clock:
		t = lc.text_to_clock(s)
		d = datetime.datetime.fromtimestamp(t, tz=lc.UTC)
		return d
	return lc.text_to_world(s)

def from_last(last):
	d = datetime.datetime.now(lc.UTC)

	if last == TimeFrame.MONTH:
		f = datetime.datetime(d.year, d.month, 1, tzinfo=d.tzinfo)
	elif last == TimeFrame.WEEK:
		dow = d.weekday()
		dom = d.day - 1
		if dom >= dow:
			f = datetime.datetime(d.year, d.month, d.day - dow, tzinfo=d.tzinfo)
		elif d.month > 1:
			t = dow - dom
			r = calendar.monthrange(d.year, d.month - 1)
			f = datetime.datetime(d.year, d.month - 1, r[1] - t, tzinfo=d.tzinfo)
		else:
			t = dow - dom
			r = calendar.monthrange(d.year - 1, 12)
			f = datetime.datetime(d.year - 1, 12, r[1] - t, tzinfo=d.tzinfo)
	elif last == TimeFrame.DAY:
		f = datetime.datetime(d.year, d.month, d.day, tzinfo=d.tzinfo)
	elif last == TimeFrame.HOUR:
		f = datetime.datetime(d.year, d.month, d.day, hour=d.hour, tzinfo=d.tzinfo)
	elif last == TimeFrame.MINUTE:
		f = datetime.datetime(d.year, d.month, d.day, hour=d.hour, minute=d.minute, tzinfo=d.tzinfo)
	elif last == TimeFrame.HALF:
		t = d.minute % 30
		m = d.minute - t
		f = datetime.datetime(d.year, d.month, d.day, hour=d.hour, minute=m, tzinfo=d.tzinfo)
	elif last == TimeFrame.QUARTER:
		t = d.minute % 15
		m = d.minute - t
		f = datetime.datetime(d.year, d.month, d.day, hour=d.hour, minute=m, tzinfo=d.tzinfo)
	elif last == TimeFrame.TEN:
		t = d.minute % 10
		m = d.minute - t
		f = datetime.datetime(d.year, d.month, d.day, hour=d.hour, minute=m, tzinfo=d.tzinfo)
	elif last == TimeFrame.FIVE:
		t = d.minute % 5
		m = d.minute - t
		f = datetime.datetime(d.year, d.month, d.day, hour=d.hour, minute=m, tzinfo=d.tzinfo)
	else:
		return None
	return f

def short_delta(d):
	t = lc.span_to_text(d.total_seconds())
	i = t.find('d')
	if i != -1:
		j = t.find('h')
		if j != -1:
			return t[:j + 1]
		return t[:i + 1]
	i = t.find('h')
	if i != -1:
		j = t.find('m')
		if j != -1:
			return t[:j + 1]
		return t[:i + 1]
	# Minutes or seconds only.
	i = t.find('.')
	if i != -1:
		i += 1
		j = t.find('s')
		if j != -1:
			e = j - i
			e = min(1, e)
			return t[:i + e] + 's'
		return t[:i] + 's'

#
#
def clocker(self, role, begin, end, count):
	try:
		for d, t in rl.read_log(role.logs, begin, end, count):
			if self.halted:
				return lc.Aborted()
			c = d.astimezone(tz=None)		   # To localtime.
			s = c.strftime('%Y-%m-%dt%H:%M:%S') # Normal part.
			f = c.strftime('%f')[:3]			# Up to milliseconds.
			h = '%s.%s' % (s, f)
			i = t.index(' ')
			lc.output_line(h, newline=False)
			lc.output_line(t[i:], newline=False)
	except (KeyboardInterrupt, SystemExit) as e:
		raise e
	except Exception as e:
		condition = str(e)
		fault = lc.Faulted(condition)
		return fault
	return None

lc.bind(clocker)

#
#
def printer(self, role, begin, end, count):
	try:
		for _, t in rl.read_log(role.logs, begin, end, count):
			if self.halted:
				return lc.Aborted()
			lc.output_line(t, newline=False)
	except (KeyboardInterrupt, SystemExit) as e:
		raise e
	except Exception as e:
		condition = str(e)
		fault = lc.Faulted(condition)
		return fault
	return None

lc.bind(printer)

#
#
def backward(self, role, count):
	try:
		for t in rl.rewind_log(role.logs, count):
			if self.halted:
				return lc.Aborted()
			lc.output_line(t, newline=False)
	except (KeyboardInterrupt, SystemExit) as e:
		raise e
	except Exception as e:
		condition = str(e)
		fault = lc.Faulted(condition)
		return fault
	return None

lc.bind(backward)

#
#
def tabulate(header, kv):
	t = []
	for h in header:
		v = kv.get(h, None)
		if v is None:
			return None
		t.append(v)
	t = '\t'.join(t)
	return t

def sampler(self, role, begin, end, count, header):
	try:
		#t = '\t'.join(header)
		#lc.output_line(t, newline=True)

		for _, t in lc.read_log(role.logs, begin, end, count):
			if self.halted:
				return lc.Aborted()
			if t[24] != '&':
				continue
			dash = t.find(' - ', 36)
			if dash == -1:
				continue
			text = t[dash + 3:-1]
			colon = text.split(':')
			equals = [c.split('=') for c in colon]
			kv = {lr[0]: lr[1] for lr in equals}
			kv['time'] = t[0:23]
			t = tabulate(header, kv)
			if t is None:
				continue
			lc.output_line(t, newline=True)
	except (KeyboardInterrupt, SystemExit) as e:
		raise e
	except Exception as e:
		condition = str(e)
		fault = lc.Faulted(condition)
		return fault
	return None

lc.bind(sampler)

#
#
table = [
	# CRUD for a set of role definitions.
	create,
	add,
	list_,
	update,
	delete,
	destroy,

	# Orchestration of the processes, i.e. executing
	# images of the role definitions.
	run,
	start,
	stop,
	status,

	# Access to records of execution.
	log,
	history,
	returned,
	edit,

	# Software distribution.
	snapshot,
]

# For package scripting.
def main():
	lc.create(layer_cake, object_table=table, strict=False)

if __name__ == '__main__':
	main()
