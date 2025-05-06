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

Run the pub-sub name service at the HOST level. Connected to
by directories at HOST and PROCESS levels, i.e. as part of the
auto-configuration driven by the pub-sub activity within the
associated, underlying PROCESS(es).

This directory needs an HTTP/web interface for the management
of WAN connection credentials. This is the first level that
WAN connectivity is supported, allowing a minimal WAN configuration
of a PROCESS, HOST and WAN.

The other level supporting WAN connectivity is at LAN.
"""
__docformat__ = 'restructuredtext'

import layer_cake as lc

#
#
class INITIAL: pass
class RUNNING: pass

class Host(lc.Threaded, lc.StateMachine):
	def __init__(self):
		lc.Threaded.__init__(self)
		lc.StateMachine.__init__(self, INITIAL)

def Host_INITIAL_Start(self, message):
	return RUNNING

def Host_RUNNING_Faulted(self, message):
	self.complete(message)

def Host_RUNNING_Stop(self, message):
	self.complete(lc.Aborted())

HOST_DISPATCH = {
	INITIAL: (
		(lc.Start,),
		()
	),
	RUNNING: (
		(lc.Faulted, lc.Stop),
		()
	),
}

lc.bind(Host, HOST_DISPATCH)

# For package scripting.
def main():
	# Explicit scope is processed in ObjectDirectory_INITIAL_Start
	# Unless there is an explicit argument this will open a listen
	# port at 127.0.0.1:DIRECTORY_PORT (e.g. 54195). If the directory
	# is presented with pub-subs for higher levels it will auto-
	# connect to DIRECTORY_AT_LAN (e.g. 192.168.0.195:DIRECTORY_PORT)
	lc.create(Host, scope=lc.ScopeOfDirectory.HOST)

if __name__ == '__main__':
	main()
