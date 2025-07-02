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

"""Directory at the HOST scope.

Run the pub-sub name service at the HOST level.
"""
__docformat__ = 'restructuredtext'

import layer_cake as lc

#
#
class INITIAL: pass
class RUNNING: pass
class CLEARING: pass

class Host(lc.Threaded, lc.StateMachine):
	def __init__(self, directory_at_host: lc.HostPort=None, directory_at_lan: lc.HostPort=None):
		lc.Threaded.__init__(self)
		lc.StateMachine.__init__(self, INITIAL)
		self.directory_at_host = directory_at_host
		self.directory_at_lan = directory_at_lan

def Host_INITIAL_Start(self, message):
	connect_to_directory = self.directory_at_lan
	accept_directories_at = self.directory_at_host or lc.DIRECTORY_AT_HOST

	self.directory = self.create(lc.ObjectDirectory, directory_scope=lc.ScopeOfDirectory.HOST,
		connect_to_directory=connect_to_directory,
		accept_directories_at=accept_directories_at)
	
	self.assign(self.directory, 1)
	return RUNNING

def Host_RUNNING_Returned(self, message):
	f = lc.Faulted('directory terminated')
	self.complete(f)

def Host_RUNNING_Faulted(self, message):
	self.abort(message)
	return CLEARING

def Host_RUNNING_Stop(self, message):
	self.abort(lc.Aborted())
	return CLEARING

def Host_CLEARING_Returned(self, message):
	self.complete(self.aborted_value)

HOST_DISPATCH = {
	INITIAL: (
		(lc.Start,),
		()
	),
	RUNNING: (
		(lc.Returned, lc.Faulted, lc.Stop),
		()
	),
	CLEARING: (
		(lc.Returned,),
		()
	),
}

lc.bind(Host, HOST_DISPATCH)

# For package scripting.
def main():
	lc.create(Host)

if __name__ == '__main__':
	main()
