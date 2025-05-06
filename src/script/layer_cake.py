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

import layer_cake as lc

#
#
class INITIAL: pass
class RUNNING: pass

class LayerCake(lc.Threaded, lc.StateMachine):
	def __init__(self):
		lc.Threaded.__init__(self)
		lc.StateMachine.__init__(self, INITIAL)

def LayerCake_INITIAL_Start(self, message):
	return RUNNING

def LayerCake_RUNNING_Faulted(self, message):
	self.complete(message)

def LayerCake_RUNNING_Stop(self, message):
	self.complete(lc.Aborted())

LAYER_CAKE_DISPATCH = {
	INITIAL: (
		(lc.Start,),
		()
	),
	RUNNING: (
		(lc.Faulted, lc.Stop),
		()
	),
}

lc.bind(LayerCake, LAYER_CAKE_DISPATCH)

def add(self, number: int=None):
	return

table = [add]

# For package scripting.
def main():
	lc.create(LayerCake, table)

if __name__ == '__main__':
	main()
