# Author: Scott Woods <scott.18.ansar@gmail.com.com>
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
__docformat__ = 'restructuredtext'

import errno
import ansar.create as ar
from .socketry import *
from .transporting import *
from .model import *
from .plumbing import ip_retry, ServiceUp, ServiceNotUp, ServiceDown

__all__ = [
	'ConnectDirectory',
	'AcceptDirectory',
]

#
#
class INITIAL: pass
class CONNECTING: pass
class LOOKING: pass
class REDIRECTING: pass
class ASSIGNING: pass
class ESTABLISHED: pass
class PAUSING: pass
class CLOSING: pass
class STARTING: pass

class ConnectDirectory(ar.Point, ar.StateMachine):
	def __init__(self, directory, tag, retry=None):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.directory = directory
		self.tag = tag

		if retry is None:
			s = local_private_public(directory.access_ipp.host)
			retry = ip_retry(s)

		self.retry = retry
		self.remote = None
		self.redirect = None
		self.connected = None
		self.your = None

def ConnectDirectory_INITIAL_Start(self, message):
	self.intervals = iter(ar.smart_intervals(self.retry))
	connect(self, self.directory.access_ipp, tag=self.tag)
	return CONNECTING

def ConnectDirectory_CONNECTING_Connected(self, message):
	d = self.directory
	lookup = DirectoryLookup(d.account_id, d.directory_id)
	self.reply(lookup)
	return LOOKING

def ConnectDirectory_CONNECTING_NotConnected(self, message):
	seconds = next(self.intervals)
	self.send(ServiceNotUp(message), self.parent_address)
	self.start(ar.T1, seconds)
	return PAUSING

def ConnectDirectory_CONNECTING_Stop(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_LOOKING_DirectoryRedirect(self, message):
	self.redirect = message
	ipp = message.redirect_ipp
	t = f'{ipp.host}:{ipp.port}'
	self.trace(f'Redirecting from FOH to WAN ({t})')
	connect(self, ipp, tag=self.tag)
	self.reply(Close())
	return REDIRECTING

def ConnectDirectory_LOOKING_Unknown(self, message):
	seconds = next(self.intervals)
	nc = NotConnected(requested_ipp=self.directory.access_ipp,
		error_code=errno.ENOLINK,
		error_text=f'Unexpected "{message}"',
		tag=self.tag)
	self.send(ServiceNotUp(nc), self.parent_address)
	self.start(ar.T1, seconds)
	return PAUSING

def ConnectDirectory_LOOKING_Stop(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_REDIRECTING_Connected(self, message):
	self.connected = message
	r = self.redirect
	assignment = DirectoryAssignment(r.directory_id, r.assignment_token)
	self.reply(assignment)
	return ASSIGNING

def ConnectDirectory_REDIRECTING_NotConnected(self, message):
	seconds = next(self.intervals)
	self.send(ServiceNotUp(message), self.parent_address)
	self.start(ar.T1, seconds)
	return PAUSING

def ConnectDirectory_REDIRECTING_Stop(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_ASSIGNING_YourDirectory(self, message):
	self.your = message
	self.remote = self.return_address
	self.forward(ServiceUp(self.connected), self.parent_address, self.remote)
	return ESTABLISHED

def ConnectDirectory_ASSIGNING_Closed(self, message):
	# Housekeeping - dropped previous connection.
	return ASSIGNING

def ConnectDirectory_ASSIGNING_Unknown(self, message):
	seconds = next(self.intervals)
	nc = NotConnected(requested_ipp=self.directory.access_ipp,
		error_code=errno.ENOLINK,
		error_text=f'Unexpected "{message}"',
		tag=self.tag)
	self.send(ServiceNotUp(nc), self.parent_address)
	self.start(ar.T1, seconds)
	return PAUSING

def ConnectDirectory_ASSIGNING_Stop(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_ESTABLISHED_Unknown(self, message):
	self.forward(message, self.parent_address, self.remote)
	return ESTABLISHED

def ConnectDirectory_ESTABLISHED_Abandoned(self, message):
	self.forward(ServiceDown(message), self.parent_address, self.remote)
	self.intervals = iter(ar.smart_intervals(self.retry))
	seconds = next(self.intervals)
	self.start(ar.T1, seconds)
	return PAUSING

def ConnectDirectory_ESTABLISHED_Closed(self, message):
	return ConnectDirectory_ESTABLISHED_Abandoned(self, message)

def ConnectDirectory_ESTABLISHED_Stop(self, message):
	self.send(Close(), self.remote)
	self.start(ar.T2, 3.0)
	return CLOSING

def ConnectDirectory_CLOSING_Closed(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_CLOSING_Abandoned(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_CLOSING_T2(self, message):
	self.complete(ar.Aborted())

def ConnectDirectory_PAUSING_T1(self, message):
	connect(self, self.directory.access_ipp, tag=self.tag)
	return CONNECTING

def ConnectDirectory_PAUSING_Stop(self, message):
	self.complete(ar.Aborted())

CONNECT_DIRECTORY_DISPATCH = {
	INITIAL: (
		(ar.Start,),
		()
	),
	CONNECTING: (
		(Connected, NotConnected, ar.Stop),
		()
	),
	LOOKING: (
		(DirectoryRedirect, ar.Stop, ar.Unknown),
		()
	),
	REDIRECTING: (
		(Connected, NotConnected, ar.Stop),
		()
	),
	ASSIGNING: (
		(YourDirectory, Closed, ar.Stop, ar.Unknown),
		()
	),
	ESTABLISHED: (
		(ar.Unknown, Abandoned, Closed, ar.Stop),
		()
	),
	CLOSING: (
		(Abandoned, Closed, ar.T2),
		()
	),
	PAUSING: (
		(ar.T1, ar.Stop),
		()
	),
}

ar.bind(ConnectDirectory, CONNECT_DIRECTORY_DISPATCH)

#
#
class AcceptDirectory(ar.Point, ar.StateMachine):
	def __init__(self, local_ipp, local_id, retry=None):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.local_ipp = local_ipp
		self.local_id = local_id

		if retry is None:
			s = local_private_public(local_ipp.host)
			retry = ip_retry(s)

		self.retry = retry
		self.listening = None
		self.local = {}
		self.closing = 0

def AcceptDirectory_INITIAL_Start(self, message):
	self.intervals = iter(ar.smart_intervals(self.retry))
	listen(self, self.local_ipp, tag=self.local_id)
	return STARTING

def AcceptDirectory_STARTING_Listening(self, message):
	self.listening = message
	return ESTABLISHED

def AcceptDirectory_STARTING_NotListening(self, message):
	seconds = next(self.intervals)
	self.send(message, self.parent_address)
	self.start(ar.T1, seconds)
	return PAUSING

def AcceptDirectory_STARTING_Stop(self, message):
	self.complete(ar.Aborted())

def AcceptDirectory_ESTABLISHED_Accepted(self, message):
	self.local[self.return_address] = message
	self.forward(message, self.parent_address, self.return_address)
	return ESTABLISHED

def AcceptDirectory_ESTABLISHED_Unknown(self, message):
	self.forward(message, self.parent_address, self.return_address)
	return ESTABLISHED

def AcceptDirectory_ESTABLISHED_Abandoned(self, message):
	accepted = self.local.pop(self.return_address, None)
	if accepted:
		self.forward(message, self.parent_address, self.return_address)
	return ESTABLISHED

def AcceptDirectory_ESTABLISHED_Closed(self, message):
	AcceptDirectory_ESTABLISHED_Abandoned(self, message)
	return ESTABLISHED

def AcceptDirectory_ESTABLISHED_Stop(self, message):
	self.closing = len(self.local)
	if self.closing == 0:
		self.complete(ar.Aborted())

	c = Close()
	for a in self.local.keys():
		self.send(c, a)
	self.start(ar.T2, 3.0)
	return CLOSING

def AcceptDirectory_CLOSING_Closed(self, message):
	# !!!!!!!!!!!!!
	# self.forward(message, self.parent_address, self.return_address)
	self.closing -= 1
	if self.closing > 0:
		return CLOSING
	self.complete(ar.Aborted())

def AcceptDirectory_CLOSING_Abandoned(self, message):
	self.closing -= 1
	if self.closing > 0:
		return CLOSING
	self.complete(ar.Aborted())

def AcceptDirectory_CLOSING_T2(self, message):
	self.complete(ar.Aborted())

def AcceptDirectory_PAUSING_T1(self, message):
	listen(self, self.local_ipp, tag=self.local_id)
	return STARTING

def AcceptDirectory_PAUSING_Stop(self, message):
	self.complete(ar.Aborted())

ACCEPT_CLIENT_DISPATCH = {
	INITIAL: (
		(ar.Start,),
		()
	),
	STARTING: (
		(Listening, NotListening, ar.Stop),
		()
	),
	ESTABLISHED: (
		(Accepted, ar.Unknown, Abandoned, Closed, ar.Stop),
		()
	),
	CLOSING: (
		(Closed, Abandoned, ar.T2),
		()
	),
	PAUSING: (
		(ar.T1, ar.Stop),
		()
	),
}

ar.bind(AcceptDirectory, ACCEPT_CLIENT_DISPATCH)

