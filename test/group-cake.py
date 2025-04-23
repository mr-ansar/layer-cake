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

""".

.
"""
__docformat__ = 'restructuredtext'

import re
import layer_cake as lc

#
#
DEFAULT_HOME = '.layer-cake'

class Group(lc.Point, lc.Stateless):
	def __init__(self, *search):
		lc.Point.__init__(self)
		lc.Stateless.__init__(self)
		self.search = search

		self.machine = []
		self.home_path = lc.CL.home_path or DEFAULT_HOME
		self.role_name = lc.CL.role_name
		self.clearing = False

def Group_Start(self, message):
	s = ', '.join(self.search)
	self.console(f'Search "{s}"')
	self.send(lc.Enquiry(), lc.PD.directory)

def Group_HostPort(self, message):
	home = lc.open_home(self.home_path)
	if home is None:
		self.complete(lc.Faulted(f'Cannot open path "{self.home_path}"'))

	for s in self.search:
		try:
			m = re.compile(s)
		except re.error as e:
			self.complete(lc.Faulted(f'Cannot compile search "{s}"', str(e)))
		self.machine.append(m)

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

	for k, v in home.items():
		a = self.create(lc.ProcessObject, v,
			origin=lc.ProcessOrigin.RUN,
			home_path=self.home_path, role_name=k,
			directory_scope=lc.ScopeOfDirectory.PROCESS, connect_to_directory=message)
		self.assign(a, 1)

def Group_Returned(self, message):
	d = self.debrief()

	if not self.working():
		self.complete(lc.Aborted())

	if not self.clearing:
		self.abort()

def Group_Faulted(self, message):
	if not self.working():
		self.complete(message)

	self.clearing = True
	self.abort()

def Group_Stop(self, message):
	if not self.working():
		self.complete(message)

	self.clearing = True
	self.abort()

lc.bind(Group, (lc.Start, lc.HostPort, lc.Returned, lc.Faulted, lc.Stop))


if __name__ == '__main__':
	lc.create(Group)
