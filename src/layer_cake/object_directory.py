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
from .get_response import *

__all__ = [
	'ConnectTo',
	'AcceptAt',
	'PublishAs',
	'SubscribeTo',
	'Published',
	'Subscribed',
	'ObjectDirectory',
	'Available',
	'Delivered',
	'Cleared',
	'Dropped',
]

CONNECT_GRACE = 5.0

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
	def __init__(self, name: str=None, scope: ScopeOfDirectory=None, address: Address=None):
		self.name = name
		self.scope = scope
		self.address = address

class SubscribeTo(object):
	def __init__(self, search: str=None, scope: ScopeOfDirectory=None, address: Address=None):
		self.search = search
		self.scope = scope
		self.address = address

bind(PublishAs)
bind(SubscribeTo)

class Published(object):
	def __init__(self, name: str=None, scope: ScopeOfDirectory=None, published_id: UUID=None, listening_ipp: HostPort=None, home_address: Address=None):
		self.name = name
		self.scope = scope
		self.published_id = published_id
		self.listening_ipp = listening_ipp or HostPort()
		self.home_address = home_address

class Subscribed(object):
	def __init__(self, search: str=None, scope: ScopeOfDirectory=None, subscribed_id: UUID=None, home_address: Address=None):
		self.search = search
		self.scope = scope
		self.subscribed_id = subscribed_id
		self.home_address = home_address

bind(Published)
bind(Subscribed)

class PublishedDirectory(object):
	def __init__(self, published: list[Published]=None, subscribed: list[Subscribed]=None):
		self.published = published or []
		self.subscribed = subscribed or []

bind(PublishedDirectory)

class ClearListings(object):
	def __init__(self, subscribers: set[UUID]=None, publishers: set[UUID]=None):
		self.subscribers = subscribers or set()
		self.publishers = publishers or set()

class ClearSubscriberRoute(object):
	def __init__(self, subscribed_id: UUID=None, name: str=None, route_id: UUID=None):
		self.subscribed_id = subscribed_id
		self.name = name
		self.route_id = route_id

class ClearPublisherRoute(object):
	def __init__(self, published_id: UUID=None, name: str=None, route_id: UUID=None):
		self.published_id = published_id
		self.name = name
		self.route_id = route_id

bind(ClearListings)
bind(ClearSubscriberRoute)
bind(ClearPublisherRoute)

class ResolveLibrary(object):
	def __init__(self, name: str=None):
		self.name = name

bind(ResolveLibrary)

#
class RouteOverLoop(object):
	def __init__(self, route_id: UUID=None, scope: ScopeOfDirectory=None, subscriber_id: UUID=None, publisher_id: UUID=None, ipp: HostPort=None, name: str=None):
		self.route_id = route_id
		self.scope = scope
		self.subscriber_id = subscriber_id
		self.publisher_id = publisher_id
		self.ipp = ipp
		self.name = name

bind(RouteOverLoop)

#
class RequestLoop(object):
	def __init__(self, subscriber_id: UUID=None, subscriber_address: Address=None, publisher_id: UUID=None, route_id: UUID=None):
		self.subscriber_id = subscriber_id
		self.subscriber_address = subscriber_address
		self.publisher_id = publisher_id
		self.route_id = route_id

class OpenLoop(object):
	def __init__(self, route_id: UUID=None, publisher_id: UUID=None, address: Address=None):
		self.route_id = route_id
		self.publisher_id = publisher_id
		self.address = address

class LoopOpened(object):
	def __init__(self, address: Address=None):
		self.address = address

bind(RequestLoop)
bind(OpenLoop)
bind(LoopOpened)

#
class Available(object):
	pass

class Delivered(object):
	pass

class Cleared(object):
	pass

class Dropped(object):
	pass

bind(Available)
bind(Delivered)
bind(Cleared)
bind(Dropped)

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
		self.accepted = {}

def ListeningForPeer_INITIAL_Start(self, message):
	if self.scope.value < ScopeOfDirectory.HOST.value:
		ipp = HostPort('0.0.0.0', 0)
	elif self.scope.value < ScopeOfDirectory.PROCESS.value:
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
	self.accepted[self.return_address[-1]] = {}
	return READY

def ListeningForPeer_READY_Closed(self, message):
	p = self.accepted.pop(self.return_address[-1], None)
	if p is not None:
		for k, v in p.items():
			self.forward(Dropped(), self.address, k)
	return READY

def ListeningForPeer_READY_Abandoned(self, message):
	p = self.accepted.pop(self.return_address[-1], None)
	if p is not None:
		for k, v in p.items():
			self.forward(Dropped(), self.address, k)
	return READY

def ListeningForPeer_READY_OpenLoop(self, message):
	self.accepted[self.return_address[-1]][message.address] = message

	self.send(LoopOpened(self.address), self.return_address)
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
		OpenLoop,
		Stop),
		()
	),
}

bind(ListeningForPeer, LISTENING_FOR_PEER_DISPATCH)

#
class ConnectToPeer(Point, StateMachine):
	def __init__(self, ipp: HostPort=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.ipp = ipp
		self.request = []
		self.available = []
	
	def not_available(self):
		for a in self.available:
			self.forward(Dropped(), a[1], a[2])

def ConnectToPeer_INITIAL_Start(self, message):
	connect(self, self.ipp)
	return PENDING

def ConnectToPeer_PENDING_Connected(self, message):
	self.connected = message

	def looped(loop, kv):
		if isinstance(loop, LoopOpened):
			a = Available()
			self.forward(a, kv.address, loop.address)
			self.available.append((a, kv.address, loop.address))
			return
		if isinstance(self.connected, Connected):
			self.send(Close(), self.connected.proxy_address)
		self.not_available()
		self.complete(loop)

	# Send OpenLoop on behalf of each client.
	for r in self.request:
		address = r.subscriber_address
		open = OpenLoop(route_id=r.route_id, publisher_id=r.publisher_id, address=address)
		a = self.create(GetResponse, open, self.connected.proxy_address, seconds=CONNECT_GRACE)
		self.begin(a, looped, address=address)
	return READY

def ConnectToPeer_PENDING_NotConnected(self, message):
	self.complete(message)

def ConnectToPeer_PENDING_RequestLoop(self, message):
	self.request.append(message)
	return PENDING

def ConnectToPeer_READY_RequestLoop(self, message):
	self.request.append(message)

	def looped(loop, kv):
		if isinstance(loop, LoopOpened):
			self.forward(Available(), kv.address, loop.address)
			return READY
		if isinstance(self.connected, Connected):
			self.send(Close(), self.connected.proxy_address)
		self.complete(loop)

	address = message.subscriber_address
	open = OpenLoop(route_id=message.route_id, publisher_id=message.publisher_id, address=address)
	a = self.create(GetResponse, open, self.connected.proxy_address, seconds=CONNECT_GRACE)
	self.begin(a, looped, address=address)
	return READY

def ConnectToPeer_READY_Closed(self, message):
	self.not_available()
	self.complete(message)

def ConnectToPeer_READY_Abandoned(self, message):
	self.not_available()
	self.complete(message)

def ConnectToPeer_READY_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(message)
	return READY

def ConnectToPeer_READY_Stop(self, message):
	self.complete(Aborted())

CONNECT_TO_PEER_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	PENDING: (
		(Connected, NotConnected, RequestLoop),
		()
	),
	READY: (
		(RequestLoop,
		Closed, Abandoned,
		Returned,
		Stop),
		()
	),
}

bind(ConnectToPeer, CONNECT_TO_PEER_DISPATCH)

#
class RouteOverConnect(Point, StateMachine):
	def __init__(self, route_id: UUID=None, scope: ScopeOfDirectory=None, subscriber: Subscribed=None, publisher: Published=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.route_id = route_id
		self.scope = scope
		self.subscriber = subscriber
		self.publisher = publisher

def RouteOverConnect_INITIAL_Start(self, message):
	r = RouteOverLoop(route_id=self.route_id, scope=self.scope,
		subscriber_id=self.subscriber.subscribed_id, publisher_id=self.publisher.published_id,
		ipp=self.publisher.listening_ipp, name=self.publisher.name)

	self.send(r, self.subscriber.home_address)
	return READY

def RouteOverConnect_READY_Stop(self, message):
	s = self.subscriber
	p = self.publisher
	self.send(ClearSubscriberRoute(subscribed_id=s.subscribed_id, name=self.publisher.name, route_id=self.route_id), self.subscriber.home_address)
	self.send(ClearPublisherRoute(published_id=s.published_id, route_id=self.route_id), self.publisher.home_address)
	self.complete(Aborted())

ROUTE_OVER_PEER_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	READY: (
		(Stop,),
		()
	),
}

bind(RouteOverConnect, ROUTE_OVER_PEER_DISPATCH)

#
class RouteToLibrary(Point, StateMachine):
	def __init__(self, route_id: UUID=None, scope: ScopeOfDirectory=None, subscriber: SubscribeTo=None, publisher: Published=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.route_id = route_id
		self.scope = scope
		self.subscriber = subscriber
		self.publisher = publisher

def RouteToLibrary_INITIAL_Start(self, message):
	self.forward(ResolveLibrary(self.publisher.name), self.publisher.home_address, self.subscriber.address)
	return READY

def RouteToLibrary_READY_Stop(self, message):
	self.complete(Aborted())

ROUTE_TO_LIBRARY_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	READY: (
		(Stop,),
		()
	),
}

bind(RouteToLibrary, ROUTE_TO_LIBRARY_DISPATCH)

#
class ObjectDirectory(Threaded, StateMachine):
	def __init__(self, directory_scope: ScopeOfDirectory=None, connect_to_directory: HostPort=None, accept_directories_at: HostPort=None):
		Threaded.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.directory_scope = directory_scope or ScopeOfDirectory.PROCESS
		self.connect_to_directory = connect_to_directory or HostPort()
		self.accept_directories_at = accept_directories_at or HostPort()

		self.connected = None			# Upward, downward directory connections.
		self.listening = None
		self.accepted = {}				# Remember who connects from below.
		self.pending_enquiry = set()

		self.live_publish = {}			# name, address -> request id
		self.listed_publish = {}		# request id -> listing, publish
		self.routed_publish = {}		# route id -> listing, address

		self.live_subscribe = {}		# search, address -> request id
		self.listed_subscribe = {}		# request id -> listing, subscribe
		self.routed_subscribe = {}		# route id -> listing, address
		self.subscriber_routing = {}

		self.published = {}		# name -> listing, publish
		self.subscribed = {}	# search -> listings, machine

		self.peer_connect = {}

	def add_publisher(self, listing, source, publish):
		name = listing.name
		scope = listing.scope

		# Existence.
		r = self.listed_publish.get(listing.published_id, None)
		if r is not None:
			self.warning(f'cannot publish "{name}" (already listed)')
			return False

		p = self.published.get(name, None)
		if p is not None:
			self.warning(f'cannot publish "{name}" (already matching)')
			return False

		if publish:
			# Need to make a listen for subscriber access.
			if scope.value < ScopeOfDirectory.PROCESS.value:
				a = self.create(ListeningForPeer, name, scope, publish.address)
				self.assign(a, (listing, publish))
				return False
		elif self.directory_scope == ScopeOfDirectory.LAN:
			# Overwrite the listening ip (0.0.0.0) with the ip from sockets.
			a, sub, pub = self.accepted.get(self.return_address[-1])
			listing.listening_ipp = HostPort(a.opened_ipp.host, listing.listening_ipp.port)
		elif self.directory_scope in (ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
			# Force the use of the loopback interface.
			listing.listening_ipp = HostPort('127.0.0.1', listing.listening_ipp.port)

		self.console(f'Published[{self.directory_scope}]', name=name, listening=listing.listening_ipp)
		self.published[name] = (listing, publish)
		self.listed_publish[listing.published_id] = (listing, publish)
		if source is not None:
			source.add(listing.published_id)
		return True

	def add_subscriber(self, listing, source, subscribe):
		search = listing.search
		scope = listing.scope
		subscribed_id = listing.subscribed_id

		# Existence of search.
		r = self.listed_subscribe.get(listing.subscribed_id, None)
		if r is not None:
			self.warning(f'cannot subscribe "{search}" (id already listed)')
			return False

		s = self.subscribed.get(search, None)
		if s is None:
			try:
				r = re.compile(listing.search)
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
		if subscribed_id in a:
			self.warning(f'cannot subscribe {search}[{scope}] (already listed)')
			return False

		self.console(f'Subscribed[{self.directory_scope}]', search=search)
		a[subscribed_id] = (listing, subscribe)
		self.listed_subscribe[subscribed_id] = (listing, subscribe)
		if source is not None:
			source.add(listing.subscribed_id)
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

	def create_route(self, subscriber, publisher):
		self.console(f'Route[{self.directory_scope}]', name=publisher.name)
		route_id = uuid.uuid4()
		if self.directory_scope in (ScopeOfDirectory.LAN, ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
			r = self.create(RouteOverConnect, route_id=route_id, scope=self.directory_scope, subscriber=subscriber, publisher=publisher)
		elif self.directory_scope in (ScopeOfDirectory.PROCESS,):
			l, s = self.listed_subscribe[subscriber.subscribed_id]
			r = self.create(RouteToLibrary, route_id=route_id, scope=self.directory_scope, subscriber=s, publisher=publisher)
		else:
			self.warning(f'Cannot route at [{self.directory_scope}]')
			return

		self.routed_publish[publisher.published_id] = (publisher, r)
		self.routed_subscribe[subscriber.subscribed_id] = (subscriber, r)

		def clear(value, kv):
			self.routed_publish.pop(kv.subscriber, None)
			self.routed_subscribe.pop(kv.publisher, None)

		self.begin(r, clear, subscriber=subscriber.subscribed_id, publisher=publisher.published_id)

	def clear_listings(self, subscribers, publishers):
		stop = Stop()
		for s in subscribers:
			r = self.routed_subscribe.get(s, None)
			if r:
				self.send(stop, r[1])
			p = self.listed_subscribe.pop(s, None)
			if p is None:
				continue
			g = self.subscribed.get(p[0].search, None)
			if g is None:
				continue
			a, sub = g
			a.pop(s, None)
			if p[1] is not None:
				live_subscribe = (p[1].search, p[1].address)
				self.live_subscribe.pop(live_subscribe, None)

		for p in publishers:
			r = self.routed_publish.get(p, None)
			if r:
				self.send(stop, r[1])
			p = self.listed_publish.pop(p, None)
			if p is None:
				continue
			self.published.pop(p[0].name, None)
			if p[1] is not None:
				live_publish = (p[1].name, p[1].address)
				self.live_publish.pop(live_publish, None)

	def send_up(self, listing):
		if isinstance(self.connected, Connected):
			if listing.scope.value < self.directory_scope.value:
				self.send(listing, self.connected.proxy_address)

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
	self.accepted[self.return_address[-1]] = [message, set(), set()]	# Accepted, subs, pubs.
	return READY

def ObjectDirectory_READY_Closed(self, message):
	p = self.accepted.pop(self.return_address[-1], None)
	if p is None:
		return READY
	self.clear_listings(p[1], p[2])
	if isinstance(self.connected, Connected) and (p[1] or p[2]):
		self.send(ClearListings(p[1], p[2]), self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_Abandoned(self, message):
	p = self.accepted.pop(self.return_address[-1], None)
	if p is None:
		return READY
	self.clear_listings(p[1], p[2])
	if isinstance(self.connected, Connected) and (p[1] or p[2]):
		self.send(ClearListings(p[1], p[2]), self.connected.proxy_address)
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

	live_publish = (name, message.address)
	r = self.live_publish.get(live_publish, None)
	if r is not None:
		self.warning(f'Cannot publish "{message.name}" (already exists)')
		return READY

	published_id = uuid.uuid4()
	listing = Published(name=name, scope=scope, published_id=published_id, home_address=self.object_address)

	if not self.add_publisher(listing, None, message):
		return READY
	self.live_publish[live_publish] = published_id

	for s in self.find_subscribers(listing):
		self.create_route(s, listing)
	
	self.send_up(listing)
	return READY

def ObjectDirectory_READY_HostPort(self, message):
	d = self.progress()
	if d is None:
		self.complete(Faulted(f'cannot complete ListenForPeer (no message record)'))
		return READY
	listing, publish = d
	listing.listening_ipp = message		# Update with live network address.

	self.console(f'Published[{self.directory_scope}]', name=listing.name, listening=message)
	
	self.published[listing.name] = (listing, publish)
	self.listed_publish[listing.published_id] = (listing, publish)

	live_publish = (publish.name, publish.address)
	self.live_publish[live_publish] = listing.published_id

	for s in self.find_subscribers(listing):
		self.create_route(s, listing)
	self.send_up(listing)

	return READY

def ObjectDirectory_READY_SubscribeTo(self, message):
	search = message.search
	scope = message.scope

	live_subscribe = (search, self.return_address)
	r = self.live_subscribe.get(live_subscribe, None)
	if r is not None:
		self.warning(f'dup')
		return READY

	subscribed_id = uuid.uuid4()
	listing = Subscribed(search=search, scope=scope, subscribed_id=subscribed_id, home_address=self.object_address)
	if not self.add_subscriber(listing, None, message):
		return READY
	self.live_subscribe[live_subscribe] = subscribed_id

	for p in self.find_publishers(listing):
		self.create_route(listing, p)
	self.send_up(listing)

	return READY

def ObjectDirectory_READY_Published(self, message):
	a, sub, pub = self.accepted[self.return_address[-1]]
	if not self.add_publisher(message, pub, None):
		return READY
	for s in self.find_subscribers(message):
		self.create_route(s, message)
	self.send_up(message)

	return READY

def ObjectDirectory_READY_Subscribed(self, message):
	a, sub, pub = self.accepted[self.return_address[-1]]
	if not self.add_subscriber(message, sub, None):
		return READY
	for p in self.find_publishers(message):
		self.create_route(message, p)
	self.send_up(message)
	return READY

def ObjectDirectory_READY_PublishedDirectory(self, message):
	a, sub, pub = self.accepted[self.return_address[-1]]
	for p in message.published:
		if not self.add_publisher(p, pub, None):
			continue
		for s in self.find_subscribers(p):
			self.create_route(s, p)

	for s in message.subscribed:
		if not self.add_subscriber(s, sub, None):
			continue
		for p in self.find_publishers(s):
			self.create_route(s, p)

	if isinstance(self.connected, Connected):
		self.push_up()
	return READY

def ObjectDirectory_READY_ClearListings(self, message):
	self.clear_listings(message.subscribers, message.publishers)
	if isinstance(self.connected, Connected):
		self.send(message, self.connected.proxy_address)
	return READY

def ObjectDirectory_READY_ClearSubscriberRoute(self, message):
	subscribed_id = message.subscribed_id
	listing = self.listed_subscribe.get(subscribed_id, None)
	if listing is None:
		self.warning('no such subscription')
		return READY

	# Routing per listing
	subscriber = self.subscriber_routing.get(subscribed_id, None)
	if subscriber is None:
		return READY

	# Per matched name
	routing = subscriber.get(message.name, None)
	if routing is None:
		return READY

	if not delete_route(message, routing[1]):
		self.warning('already cleared by connector')
		return READY
	
	if len(routing[1]) == 0:
		subscriber.pop(message.name, None)
	return READY

def ObjectDirectory_READY_ClearPublisherRoute(self, message):
	p = self.listed_publish.get(message.published_id, None)
	if p is None:
		return READY
	self.send(Dropped(), p[1].address)
	return READY

def ObjectDirectory_READY_ResolveLibrary(self, message):
	p = self.published.get(message.name, None)
	if p is None:
		return READY
	self.forward(Available(), self.return_address, p[1].address)
	return READY

def find_route(route, routing):
	for r in routing:
		if r.route_id == route.route_id:
			return True
	return False

def best_route(routing):
	best = None
	for r in routing:
		if best is None or r.scope.value > best.scope.value:
			best = r
	return best

def add_route(route, routing):
	before = best_route(routing)
	routing.append(route)
	after = best_route(routing)
	return before, after

def delete_route(route, routing):
	d = None
	for i, r in enumerate(routing):
		if r.route_id == route.route_id:
			d = i
	if d is not None:
		routing.pop(d)
		return True
	return False

def find_route(route, routing):
	for r in routing:
		if r.route_id == route.route_id:
			return True
	return False

def ObjectDirectory_READY_RouteOverLoop(self, message):
	subscriber_id = message.subscriber_id

	listing = self.listed_subscribe.get(subscriber_id, None)
	if listing is None:
		self.warning('no such subscription')
		return READY

	# Routing per listing
	subscriber = self.subscriber_routing.get(subscriber_id, None)
	if subscriber is None:
		subscriber = {}
		self.subscriber_routing[subscriber_id] = subscriber

	# Per matched name
	routing = subscriber.get(message.name, None)
	if routing is None:
		routing = [None, []]
		subscriber[message.name] = routing

	if find_route(message, routing[1]):
		self.warning('duplicate route')
		return READY

	before, after = add_route(message, routing[1])

	if before is None:
		pass
	elif after.scope.value > before.scope.value:
		# An upgrade is now available
		return READY
	else:
		# Downgrade or no change.
		return READY
	routing[0] = after

	def clear_routes(value, kv):
		p = self.peer_connect.get(kv.ipp, None)
		if p is None:
			return
		for r in p:
			try:
				t = self.subscriber_routing[r.subscriber_id][r.name]
			except (KeyError, IndexError):
				continue
			delete_route(r, t[1])
			if len(t[1]) == 0:
				self.subscriber_routing[r.subscriber_id][r.name]
			if len(self.subscriber_routing[r.subscriber_id]) == 0:
				del self.subscriber_routing[r.subscriber_id]

	if isinstance(after, RouteOverLoop):
		listing = self.listed_subscribe.get(after.subscriber_id, None)
		p = self.peer_connect.get(after.ipp, None)
		if p is None:
			c = self.create(ConnectToPeer, after.ipp)
			self.begin(c, clear_routes, ipp=after.ipp)
			p = []
			self.peer_connect[after.ipp] = p
		address = listing[1].address
		r = RequestLoop(subscriber_id=after.subscriber_id, subscriber_address=address,
			publisher_id=after.publisher_id,
			route_id=after.route_id)
		self.forward(r, c, address)
		p.append(after)
	else:
		self.warning('not implemented')

	return READY

def ObjectDirectory_READY_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(message)
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
		Published, Subscribed,
		PublishedDirectory,
		ClearListings,
		ClearSubscriberRoute, ClearPublisherRoute,
		ResolveLibrary,
		RouteOverLoop,
		Returned,
		Stop,),
		()
	),
	CLEARING: (
		(T1,),
		()
	),
}

bind(ObjectDirectory, OBJECT_DIRECTORY_DISPATCH)
