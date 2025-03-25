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
"""A hierarchical directory of named addresses.

.
"""
__docformat__ = 'restructuredtext'

from enum import Enum
from collections import deque

from .general_purpose import *
from .command_line import *
from .ip_networking import *
from .virtual_memory import *
from .message_memory import *
from .convert_type import *
from .virtual_runtime import *
from .point_runtime import *
from .virtual_point import *
from .point_machine import *
from .bind_type import *
from .listen_connect import *

__all__ = [
	'ConnectTo',
	'AcceptAt',
	'PublishAsName',
	'SubscribeToName',
	'DirectoryMatch',
	'ObjectDirectory',
]

#
class SubscribeToName(object):
	def __init__(self, search: str=None, address: Address=None):
		self.search = search
		self.address = address or NO_SUCH_ADDRESS

class PublishAsName(object):
	def __init__(self, name: str=None, address: Address=None):
		self.name = name
		if address is None:
			address = NO_SUCH_ADDRESS
		self.address = address

class DirectoryMatch(object):
	def __init__(self, matched: str=None, address: Address=None):
		self.matched = matched
		if address is None:
			address = NO_SUCH_ADDRESS
		self.address = address

bind(PublishAsName)
bind(SubscribeToName)
bind(DirectoryMatch)

class ConnectTo(object):
	def __init__(self, ipp: HostPort=None):
		self.ipp = ipp or HostPort()

class AcceptAt(object):
	def __init__(self, ipp: HostPort=None):
		self.ipp = ipp or HostPort()

bind(ConnectTo)
bind(AcceptAt)

#
class INITIAL: pass
class READY: pass
class CLEARING: pass

class ObjectDirectory(Threaded, StateMachine):
	def __init__(self, directory_scope: SCOPE_OF_DIRECTORY=None, accept_directories_at: HostPort=None, connect_to_directory: HostPort=None):
		Threaded.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.directory_scope = directory_scope or SCOPE_OF_DIRECTORY.PROCESS
		self.accept_directories_at = accept_directories_at or HostPort()
		self.connect_to_directory = connect_to_directory or HostPort()
		self.listening = None
		self.connected = None
		self.pending_enquiry = set()
		self.published = {}
		self.subscribed = {}

def ObjectDirectory_INITIAL_Start(self, message):
	if self.connect_to_directory.host is not None:
		connect(self, self.connect_to_directory)
	if self.accept_directories_at.host is not None:
		listen(self, self.accept_directories_at)
	return READY

#
def ObjectDirectory_READY_Listening(self, message):
	self.listening = message
	for p in self.pending_enquiry:
		self.send(message.listening_ipp, p)
	self.pending_enquiry = set()
	return READY

def ObjectDirectory_READY_NotListening(self, message):
	self.listening = message
	# Schedule a retry.
	return READY

published_cast = type_cast(dict[str, PublishAsName])
subscribed_cast = type_cast(dict[str, list[SubscribeToName]])

def ObjectDirectory_READY_Connected(self, message):
	self.connected = message
	if self.published:
		self.send(published_cast(self.published), self.connected.proxy_address)
	if self.subscribed:
		self.send(subscribed_cast(self.subscribed), self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_NotConnected(self, message):
	self.connected = message
	# Schedule a retry.
	# Different scheduling to close/abandon.
	return READY

def ObjectDirectory_READY_Closed(self, message):
	# if connection
	# Schedule reconnect.
	# Modify the tree
	return READY

def ObjectDirectory_READY_Abandoned(self, message):
	ObjectDirectory_READY_Closed(self, message)
	return READY

#
def ObjectDirectory_READY_ConnectTo(self, message):
	if self.connect_to_directory.host is not None:
		if isinstance(self.connected, Connected):
			self.send(Close(), self.connected.proxy_address)
		# Could be a Connected in the queue.
	else:
		connect(self, message.ipp)
	self.connect_to_directory = message.ipp
	return READY

def ObjectDirectory_READY_AcceptAt(self, message):
	if self.accept_directories_at.host is not None:
		if isinstance(self.listening, Listening):
			stop_listening(self, self.listening.lid)
		# Could be a Listening in the queue.
	else:
		listen(self, message.ipp)
	self.accept_directories_at = message.ipp
	return READY

def ObjectDirectory_READY_Enquiry(self, message):
	if self.accept_directories_at.host is None:
		self.accept_directories_at = HostPort('127.0.0.1', 0)
		listen(self, self.accept_directories_at)
		self.pending_enquiry.add(self.return_address)
		return READY

	if not isinstance(self.listening, Listening):
		self.pending_enquiry.add(self.return_address)
		return READY

	return READY

# PublishAsName/SubscribeToName
# Published/Subscribed (?)
# DirectoryListings (sent up)
# NippedOff/

def ObjectDirectory_READY_PublishAsName(self, message):
	self.published[message.name] = message

	if isinstance(self.connected, Connected):
		self.send(message, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_SubscribeToName(self, message):
	s = self.subscribed.get(message.search, None)
	if s is None:
		s = []
		self.subscribed[message.search] = s
	s.append(message)

	if isinstance(self.connected, Connected):
		self.send(message, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_dict_str_PublishAsName(self, message):
	for k, v in message.items():
		self.console(publish=k)
		self.published[k] = v
		s = self.subscribed.get(k, None)
		if s is None:
			self.console(subscribed='not found')
			continue
		for m in s:
			self.console(subscribed=m.address)
			self.send(v, m.address)
	return READY

def ObjectDirectory_READY_dict_str_list_SubscribeToName(self, message):
	for k, v in message.items():
		s = self.subscribed.get(k, None)
		if s is None:
			s = []
			self.subscribed[k] = s
		for m in v:
			s.append(m)
		p = self.published.get(k, None)
		if p is None:
			continue
		self.send(Nak(), p.address)
		
	return READY

def ObjectDirectory_READY_Stop(self, message):
	self.complete()

def ObjectDirectory_CLEARING_T1(self, message):
	self.complete()

OBJECT_DIRECTORY_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	READY: (
		(Listening, NotListening,
		Connected, NotConnected,
		Closed, Abandoned,
		ConnectTo, AcceptAt,
		Enquiry,
		PublishAsName, SubscribeToName,
		dict[str,PublishAsName], dict[str,list[SubscribeToName]],
		Stop,),
		()
	),
	CLEARING: (
		(T1,),
		()
	),
}

bind(ObjectDirectory, OBJECT_DIRECTORY_DISPATCH)
