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
import uuid
import re
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
	'PublishAs',
	'SubscribeTo',
	'PublishedObject',
	'SubscribedObject',
	'DirectoryMatch',
	'ObjectDirectory',
]

# Activate/update the directory.
class ConnectTo(object):
	def __init__(self, ipp: HostPort=None):
		self.ipp = ipp or HostPort()

class AcceptAt(object):
	def __init__(self, ipp: HostPort=None):
		self.ipp = ipp or HostPort()

bind(ConnectTo)
bind(AcceptAt)

class PublishAs(object):
	def __init__(self, name: str=None, scope: ScopeOfDirectory=None, address: Address=None, device_id: UUID=None):
		self.name = name
		self.scope = scope
		self.address = address
		self.device_id = device_id

class SubscribeTo(object):
	def __init__(self, search: str=None, scope: ScopeOfDirectory=None, address: Address=None, device_id: UUID=None):
		self.search = search
		self.scope = scope
		self.address = address
		self.device_id = device_id

bind(PublishAs)
bind(SubscribeTo)

class PublishedObject(object):
	def __init__(self, name: str=None, scope: ScopeOfDirectory=None, device_id: UUID=None, listening_ipp: HostPort=None, home_address: Address=None):
		self.name = name
		self.scope = scope
		self.device_id = device_id
		self.listening_ipp = listening_ipp or HostPort()
		self.home_address = home_address

class SubscribedObject(object):
	def __init__(self, search: str=None, scope: ScopeOfDirectory=None, device_id: UUID=None, home_address: Address=None):
		self.search = search
		self.scope = scope
		self.device_id = device_id
		self.home_address = home_address

bind(PublishedObject)
bind(SubscribedObject)

class PublishedDirectory(object):
	def __init__(self, published: list[PublishedObject]=None, subscribed: list[SubscribedObject]=None):
		self.published = published or []
		self.subscribed = subscribed or []

class DirectoryMatch(Point, Stateless):
	def __init__(self, scope, subscribed, published):
		Point.__init__(self)
		Stateless.__init__(self)
		self.scope = scope
		self.subscribed = subscribed
		self.published = published

bind(PublishedDirectory)
#bind(DirectoryMatch, thread='directory-match')

#
class OpenPeer(object):
	def __init__(self, address: Address=None):
		self.address = address

class PeerOpened(object):
	def __init__(self, address: Address=None):
		self.address = address

bind(OpenPeer)
bind(PeerOpened)

#
class Available(object):
	pass

class Delivered(object):
	pass

bind(Available)
bind(Delivered)

#
class INITIAL: pass
class PENDING: pass
class READY: pass
class CLEARING: pass

class ListeningForPeer(Point, StateMachine):
	def __init__(self, name: str=None, scope: ScopeOfDirectory=None, address: Address=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.name = name
		self.scope = scope
		self.address = address
		self.listening = None

def ListeningForPeer_INITIAL_Start(self, message):
	if self.scope == ScopeOfDirectory.LAN:
		ipp = HostPort('0.0.0.0', 0)
	elif self.scope in (ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
		ipp = HostPort('127.0.0.1', 0)
	else:
		self.complete(Faulted(f'cannot peer for scope [{self.scope}]'))
	listen(self, ipp)
	return PENDING

def ListeningForPeer_PENDING_Listening(self, message):
	self.listening = message
	self.send(message.listening_ipp, self.parent_address)
	return READY

def ListeningForPeer_PENDING_NotListening(self, message):
	self.complete(message)

def ListeningForPeer_READY_Accepted(self, message):
	return READY

def ListeningForPeer_READY_Closed(self, message):
	return READY

def ListeningForPeer_READY_Abandoned(self, message):
	return READY

def ListeningForPeer_READY_OpenPeer(self, message):
	self.send(PeerOpened(self.address), self.return_address)
	self.forward(Delivered(), self.address, message.address)
	return READY

def ListeningForPeer_READY_Stop(self, message):
	self.complete(Aborted())

LISTENING_FOR_PEER_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	PENDING: (
		(Listening, NotListening),
		()
	),
	READY: (
		(Accepted, Closed, Abandoned,
		OpenPeer,
		Stop),
		()
	),
}

bind(ListeningForPeer, LISTENING_FOR_PEER_DISPATCH)

#
class ObjectDirectory(Threaded, StateMachine):
	def __init__(self, directory_scope: ScopeOfDirectory=None, accept_directories_at: HostPort=None, connect_to_directory: HostPort=None):
		Threaded.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.directory_scope = directory_scope or ScopeOfDirectory.PROCESS
		self.accept_directories_at = accept_directories_at or HostPort()
		self.connect_to_directory = connect_to_directory or HostPort()

		self.unique_id = uuid.uuid4()
		self.listening = None
		self.connected = None
		self.pending_enquiry = set()
		self.published = {}
		self.subscribed = {}
		self.accepted = {}

	def add_publisher(self, published, message):
		name = published.name
		scope = published.scope

		# Existence.
		p = self.published.get(name, None)
		if p is not None:
			self.warning(f'cannot publish {name}[{scope}] (already exists)')
			return False
		self.console(name=name, scope=scope)

		if message:
			# Need to make a listen for subscriber access.
			if scope in (ScopeOfDirectory.LAN, ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
				a = self.create(ListeningForPeer, name, scope, message.address)
				self.assign(a, (published, message))
				return False
		elif self.directory_scope == ScopeOfDirectory.LAN:
			# Overwrite the listening ip (0.0.0.0) with the ip from sockets.
			a = self.accepted.get(self.return_address[-1])
			published.listening_ipp = HostPort(a.opened_ipp.host, published.listening_ipp.port)
		elif self.directory_scope in (ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
			# Force the use of the loopback interface.
			published.listening_ipp = HostPort('127.0.0.1', published.listening_ipp.port)

		self.published[name] = (published, message)
		return True

	def add_subscriber(self, subscribed, message):
		search = subscribed.search
		scope = subscribed.scope

		# Existence of search.
		s = self.subscribed.get(search, None)
		if s is None:
			try:
				r = re.compile(subscribed.search)
			except re.error as e:
				t = str(e)
				self.warning(f'cannot subscribe to {search}[{scope}] ({t})')
				return False
			a = {}
			s = [a, r]
			self.subscribed[search] = s
		else:
			a = s[0]

		# Existence of subscriber.
		if subscribed.device_id in a:
			self.warning(f'cannot subscribe {search}[{scope}] (already subscribed)')
			return False

		a[subscribed.device_id] = (subscribed, message)
		return True

	def find_subscribers(self, published):
		for k, v in self.subscribed.items():
			m = v[1].match(published.name)
			if m:
				for s in v[0].values():
					yield s[0]

	def find_publishers(self, subscribed):
		s = self.subscribed.get(subscribed.search, None)
		if s is None:
			return
		machine = s[1]
		for k, v in self.published.items():
			m = machine.match(k)
			if m:
				yield v[0]

	def create_match(self, subscriber, publisher):
		self.console('matched', subscriber=subscriber.search, publisher=publisher.name)

	def push_up(self):
		published = [v[0] for k, v in self.published.items() if v[0].scope.value < self.directory_scope.value]
		subscribed = []
		for k, v in self.subscribed.items():
			for t in v[0].values():
				if t[0].scope.value < self.directory_scope.value:
					subscribed.append(t[0])
		if published or subscribed:
			self.send(PublishedDirectory(published, subscribed), self.connected.proxy_address)

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

def ObjectDirectory_READY_Connected(self, message):
	self.connected = message
	self.push_up()
	return READY

def ObjectDirectory_READY_NotConnected(self, message):
	self.connected = message
	# Schedule a retry.
	# Different scheduling to close/abandon.
	return READY

def ObjectDirectory_READY_Accepted(self, message):
	self.accepted[self.return_address[-1]] = message
	return READY

def ObjectDirectory_READY_Closed(self, message):
	self.accepted.pop(self.return_address[-1], None)
	return READY

def ObjectDirectory_READY_Abandoned(self, message):
	self.accepted.pop(self.return_address[-1], None)
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

def ObjectDirectory_READY_PublishAs(self, message):
	name = message.name
	scope = message.scope

	# Provisional directory record.
	p = PublishedObject(name=name, scope=scope, device_id=message.device_id, home_address=self.object_address)

	# Add and
	if not self.add_publisher(p, message):
		return READY
	for s in self.find_subscribers(p):
		self.create_match(s, p)
	
	if isinstance(self.connected, Connected):
		self.send(p, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_HostPort(self, message):
	d = self.progress()
	if d is None:
		self.complete(Faulted(f'cannot complete ListenForPeer (no message record)'))
		return READY
	published, requested = d
	published.listening_ipp = message	# Update with live network address.

	self.published[published.name] = (published, requested)
	for s in self.find_subscribers(published):
		self.create_match(s, published)

	if isinstance(self.connected, Connected):
		self.send(published, self.connected.proxy_address)

	return READY

def ObjectDirectory_READY_SubscribeTo(self, message):
	search = message.search
	scope = message.scope

	p = SubscribedObject(search=search, scope=scope, device_id=message.device_id, home_address=self.object_address)
	if not self.add_subscriber(p, message):
		return READY
	for s in self.find_publishers(p):
		self.create_match(s, p)
	
	if isinstance(self.connected, Connected):
		self.send(p, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_PublishedObject(self, message):
	if not self.add_publisher(message, None):
		return READY
	for s in self.find_subscribers(message):
		self.create_match(s, message)

	if isinstance(self.connected, Connected) and message.scope < self.directory_scope:
		self.send(message, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_SubscribedObject(self, message):
	if not self.add_subscriber(message, None):
		return READY
	for p in self.find_publishers(message):
		self.create_match(message, p)

	if isinstance(self.connected, Connected) and message.scope < self.directory_scope:
		self.send(message, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_PublishedDirectory(self, message):
	for p in message.published:
		if not self.add_publisher(p, None):
			continue
		for s in self.find_subscribers(p):
			self.create_match(s, p)

	for s in message.subscribed:
		if not self.add_subscriber(p, None):
			continue
		for p in self.find_publishers(p):
			self.create_match(s, p)

	if isinstance(self.connected, Connected):
		self.push_up()
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
		Accepted, Closed, Abandoned,
		ConnectTo, AcceptAt,
		Enquiry,
		PublishAs, SubscribeTo, HostPort,
		PublishedObject, SubscribedObject,
		PublishedDirectory,
		Stop,),
		()
	),
	CLEARING: (
		(T1,),
		()
	),
}

bind(ObjectDirectory, OBJECT_DIRECTORY_DISPATCH)
