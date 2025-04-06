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
"""A hierarchical directory of named addresses, expressions of interest and matches.

.
"""
__docformat__ = 'restructuredtext'

from enum import Enum
from datetime import datetime
import uuid
import re
from collections import deque

from .general_purpose import *
from .command_line import *
from .ip_networking import *
from .virtual_memory import *
from .convert_memory import *
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
	'NotPublished',
	'NotSubscribed',
	'ObjectDirectory',
	'Available',
	'Delivered',
	'Dropped',
]

CONNECT_GRACE = 5.0

# Activate/update the directory-to-directory connections.
class ConnectTo(object):
	def __init__(self, ipp: HostPort=None):
		self.ipp = ipp or HostPort()

class AcceptAt(object):
	def __init__(self, ipp: HostPort=None):
		self.ipp = ipp or HostPort()

bind(ConnectTo)
bind(AcceptAt)

# Declare publish/subscribe within the host process.
# Sent by the application objects.
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

# Internal record of pub/subs held within each directory in the tree.
# Propagated up the hierarchy.
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

# When pub/sub fails.
class NotPublished(Faulted):
	def __init__(self, name: str=None, scope: ScopeOfDirectory=None, note: str=None):
		self.name = name
		self.scope = scope
		self.note = note
		Faulted.__init__(self,f'cannot publish as "{name}"', note)

class NotSubscribed(Faulted):
	def __init__(self, search: str=None, scope: ScopeOfDirectory=None, note: str=None):
		self.search = search
		self.scope = scope
		self.note = note
		Faulted.__init__(self,f'cannot subscribe to "{search}"', note)

bind(NotPublished, explanation=str, error_code=int, exit_status=int)
bind(NotSubscribed, explanation=str, error_code=int, exit_status=int)

# Bulk transfer of listings between directories, e.g. on
# reconnect to parent.
class PublishedDirectory(object):
	def __init__(self, published: list[Published]=None, subscribed: list[Subscribed]=None):
		self.published = published or []
		self.subscribed = subscribed or []

bind(PublishedDirectory)

# When an accepted directory is lost, all the pub/sub listings
# originating from that connection are cleared out of the hierarchy.
class ClearListings(object):
	def __init__(self, subscribers: set[UUID]=None, publishers: set[UUID]=None):
		self.subscribers = subscribers or set()
		self.publishers = publishers or set()

bind(ClearListings)

# Custom message from route to loadable library process.
class ResolveLibrary(object):
	def __init__(self, name: str=None):
		self.name = name

bind(ResolveLibrary)

# Messages from route to pub/sub home processes to inform the
# receivers of another routing option.
# Base class for all.
class SubscriberRoute(object):
	def __init__(self, route_id: UUID=None, scope: ScopeOfDirectory=None, subscribed_id: UUID=None, published_id: UUID=None, name: str=None):
		self.route_id = route_id
		self.scope = scope
		self.subscribed_id = subscribed_id
		self.published_id = published_id
		self.name = name

# Derived class for RouteOverConnect.
class RouteOverLoop(SubscriberRoute):
	def __init__(self, route_id: UUID=None, scope: ScopeOfDirectory=None, subscribed_id: UUID=None, published_id: UUID=None, ipp: HostPort=None, name: str=None):
		# Base members.
		self.route_id = route_id
		self.scope = scope
		self.subscribed_id = subscribed_id
		self.published_id = published_id
		self.name = name
		# Specialized members.
		self.ipp = ipp

class RouteToAddress(SubscriberRoute):
	def __init__(self, route_id: UUID=None, scope: ScopeOfDirectory=None, subscribed_id: UUID=None, published_id: UUID=None, name: str=None):
		# Base members.
		self.route_id = route_id
		self.scope = scope
		self.subscribed_id = subscribed_id
		self.published_id = published_id
		self.name = name

# Messages from route to pub/sub host processes, to delete the given route.
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

# To prompt the directory into choosing another route.
class RerouteSubscriber(object):
	def __init__(self, subscribed_id: UUID=None, name: str=None):
		self.subscribed_id = subscribed_id
		self.name = name

bind(SubscriberRoute)
bind(RouteOverLoop)
bind(ClearSubscriberRoute)
bind(ClearPublisherRoute)
bind(RerouteSubscriber)

# From directory to connector
class RequestLoop(object):
	def __init__(self, subscribed_id: UUID=None, name: str=None, subscriber_address: Address=None, published_id: UUID=None, route_id: UUID=None):
		self.subscribed_id = subscribed_id
		self.name = name
		self.subscriber_address = subscriber_address
		self.published_id = published_id
		self.route_id = route_id

# Connector to remote, i.e. ListenForPeer.
class OpenLoop(object):
	def __init__(self, route_id: UUID=None, published_id: UUID=None, address: Address=None):
		self.route_id = route_id
		self.published_id = published_id
		self.address = address

# Reply from remote ListenToPeer.
class LoopOpened(object):
	def __init__(self, address: Address=None):
		self.address = address

# A nudge to push the subscriber off the current routing
# and on to a better one, i.e. an upgrade.
class DropLoop(object):
	def __init__(self, route_id: UUID=None, address: Address=None):
		self.route_id = route_id
		self.address = address

class LoopDropped(object):
	def __init__(self, address: Address=None):
		self.address = address

class CloseLoop(object):
	def __init__(self, route_id: UUID=None, address: Address=None):
		self.route_id = route_id
		self.address = address

class LoopClosed(object):
	def __init__(self, address: Address=None):
		self.address = address

bind(RequestLoop)
bind(OpenLoop)
bind(LoopOpened)
bind(DropLoop)
bind(LoopDropped)
bind(CloseLoop)
bind(LoopClosed)

#
class Available(object):
	def __init__(self, route_id: UUID=None, address: Address=None, opened_at: datetime=None):
		self.route_id = route_id
		self.address = address
		self.opened_at = opened_at

class Delivered(object):
	def __init__(self, route_id: UUID=None, address: Address=None, opened_at: datetime=None):
		self.route_id = route_id
		self.address = address
		self.opened_at = opened_at

class Dropped(object):
	def __init__(self, route_id: UUID=None, address: Address=None, closed_at: datetime=None):
		self.route_id = route_id
		self.address = address
		self.closed_at = closed_at

bind(Available)
bind(Delivered)
bind(Dropped)

#
class INITIAL: pass
class PENDING: pass
class READY: pass
class CLEARING: pass

#
class ScheduledReroute(Point, Stateless):
	def __init__(self, subscribed_id: UUID=None, name: str=None, seconds: float=2.0):
		Point.__init__(self)
		Stateless.__init__(self)
		self.subscribed_id = subscribed_id
		self.name = name
		self.seconds = seconds

def ScheduledReroute_Start(self, message):
	self.start(T1, self.seconds)

def ScheduledReroute_T1(self, message):
	self.send(RerouteSubscriber(subscribed_id=self.subscribed_id, name=self.name), self.parent_address)
	self.complete()

bind(ScheduledReroute, (Start, T1))

#
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
			self.forward(Dropped(route_id=v.route_id, address=k, closed_at=world_now()), self.address, k)
	return READY

def ListeningForPeer_READY_Abandoned(self, message):
	p = self.accepted.pop(self.return_address[-1], None)
	if p is not None:
		for k, v in p.items():
			self.forward(Dropped(route_id=v.route_id, address=k, closed_at=world_now()), self.address, k)
	return READY

def ListeningForPeer_READY_OpenLoop(self, message):
	self.accepted[self.return_address[-1]][message.address] = message

	self.send(LoopOpened(self.address), self.return_address)
	d = Delivered(route_id=message.route_id, address=message.address, opened_at=world_now())
	self.forward(d, self.address, message.address)
	return READY

def ListeningForPeer_READY_CloseLoop(self, message):
	self.accepted[self.return_address[-1]].pop(message.address, None)

	self.send(LoopClosed(self.address), self.return_address)
	d = Dropped(route_id=message.route_id, address=message.address, closed_at=world_now())
	self.forward(d, self.address, message.address)
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
request_table_type = def_type(list[RequestLoop])

class ConnectToPeer(Point, StateMachine):
	def __init__(self, ipp: HostPort=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.ipp = ipp
		self.request = []
		self.available = []
	
	def not_available(self):
		for a in self.available:
			self.forward(Dropped(route_id=a[0].route_id, address=a[2], closed_at=world_now()), a[1], a[2])

def ConnectToPeer_INITIAL_Start(self, message):
	connect(self, self.ipp)
	return PENDING

def ConnectToPeer_PENDING_Connected(self, message):
	self.connected = message

	def looped(loop, kv):
		if isinstance(loop, LoopOpened):
			a = Available(route_id=kv.route_id, address=loop.address, opened_at=world_now())
			self.forward(a, kv.address, loop.address)
			self.available.append((a, kv.address, loop.address))
			return
		if isinstance(self.connected, Connected):
			self.send(Close(), self.connected.proxy_address)
		self.not_available()
		self.complete(self.request)

	# Send OpenLoop on behalf of each client.
	for r in self.request:
		address = r.subscriber_address
		open = OpenLoop(route_id=r.route_id, published_id=r.published_id, address=address)
		a = self.create(GetResponse, open, self.connected.proxy_address, seconds=CONNECT_GRACE)
		self.begin(a, looped, route_id=r.route_id, address=address)
	return READY

def ConnectToPeer_PENDING_NotConnected(self, message):
	self.complete(self.request)

def ConnectToPeer_PENDING_RequestLoop(self, message):
	self.request.append(message)
	return PENDING

def ConnectToPeer_READY_RequestLoop(self, message):
	self.request.append(message)

	def looped(loop, kv):
		if isinstance(loop, LoopOpened):
			a = Available(route_id=kv.route_id, address=kv.address, opened_at=world_now())
			self.forward(a, kv.address, loop.address)
			return READY
		if isinstance(self.connected, Connected):
			self.send(Close(), self.connected.proxy_address)
		self.complete(self.request)

	address = message.subscriber_address
	open = OpenLoop(route_id=message.route_id, published_id=message.published_id, address=address)
	a = self.create(GetResponse, open, self.connected.proxy_address, seconds=CONNECT_GRACE)
	self.begin(a, looped, route_id=message.route_id, address=address)
	return READY

def ConnectToPeer_READY_DropLoop(self, message):
	def closed(loop, kv):
		if isinstance(loop, LoopClosed):
			a = Dropped(route_id=kv.route_id, address=kv.address, closed_at=world_now())
			self.forward(a, kv.address, loop.address)
			self.send(LoopDropped(), self.parent_address)
			return READY
		if isinstance(self.connected, Connected):
			self.send(Close(), self.connected.proxy_address)
		self.complete(self.request)

	address = message.subscriber_address
	open = CloseLoop(route_id=message.route_id, published_id=message.published_id, address=address)
	a = self.create(GetResponse, open, self.connected.proxy_address, seconds=CONNECT_GRACE)
	self.begin(a, closed, route_id=message.route_id, address=address)
	return READY

def ConnectToPeer_READY_CloseLoop(self, message):
	def closed(value, kv):
		if not isinstance(value, LoopClosed):
			self.warning(f'Unexpected close response ({value})')
			return
		message = kv.message
		if not delete_route(message.route_id, self.request):
			return READY
		d = None
		for i, a in enumerate(self.available):
			if a[0].route_id == message.route_id:
				d = i
				break
		if d is not None:
			self.forward(Dropped(route_id=a[0].route_id, address=a[2], closed_at=world_now()), a[1], a[2])
			self.available.pop(d)

		if len(self.request) == 0:
			self.start(T1, 30.0)
	
	a = self.create(GetResponse, message, self.connected.proxy_address, seconds=CONNECT_GRACE)
	self.begin(a, closed, message=message)
	return READY

def ConnectToPeer_PENDING_CloseLoop(self, message):
	self.reply(LoopClosed())
	if not delete_route(message.route_id, self.request):
		return PENDING

	if len(self.request) == 0:
		self.start(T1, 30.0)
	return PENDING

def ConnectToPeer_READY_T1(self, message):
	if len(self.request) == 0:
		self.send(Close(), self.connected.proxy_address)

def ConnectToPeer_READY_Closed(self, message):
	self.not_available()
	self.complete(self.request)

def ConnectToPeer_READY_Abandoned(self, message):
	self.not_available()
	self.complete(self.request)

def ConnectToPeer_READY_Returned(self, message):
	d = self.debrief()
	if isinstance(d, OnReturned):
		d(message)
	return READY

def ConnectToPeer_READY_Stop(self, message):
	self.complete(self.request)

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
		Stop,
		T1),
		()
	),
}

bind(ConnectToPeer, CONNECT_TO_PEER_DISPATCH, return_type=request_table_type)

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
		subscribed_id=self.subscriber.subscribed_id, published_id=self.publisher.published_id,
		ipp=self.publisher.listening_ipp, name=self.publisher.name)

	self.send(r, self.subscriber.home_address)
	return READY

def RouteOverConnect_READY_Stop(self, message):
	s = self.subscriber
	p = self.publisher
	self.send(ClearSubscriberRoute(subscribed_id=s.subscribed_id, name=p.name, route_id=self.route_id), s.home_address)
	self.send(ClearPublisherRoute(published_id=p.published_id, name=p.name, route_id=self.route_id), p.home_address)
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
class RouteInProcess(Point, StateMachine):
	def __init__(self, route_id: UUID=None, subscriber: Subscribed=None, publisher: Published=None, subscriber_address: Address=None, publish_as: PublishAs=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.route_id = route_id
		self.subscriber = subscriber
		self.publisher = publisher
		self.subscriber_address = subscriber_address
		self.publish_as = publish_as

def RouteInProcess_INITIAL_Start(self, message):
	if self.publish_as is None:
		self.forward(ResolveLibrary(self.publisher.name), self.publisher.home_address, self.subscriber_address)
		return READY

	r = RouteToAddress(route_id=self.route_id, scope=ScopeOfDirectory.PROCESS,
		subscribed_id=self.subscribed_id, published_id=self.published_id, name=self.name)

	self.send(r, self.subscriber.home_address)
	return READY

def RouteInProcess_READY_Stop(self, message):
	s = self.subscriber
	p = self.publisher
	self.send(ClearSubscriberRoute(subscribed_id=s.subscribed_id, name=p.name, route_id=self.route_id), s.home_address)
	self.send(ClearPublisherRoute(published_id=p.published_id, name=p.name, route_id=self.route_id), p.home_address)
	self.complete(Aborted())

ROUTE_IN_PROCESS_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	READY: (
		(Stop,),
		()
	),
}

bind(RouteInProcess, ROUTE_IN_PROCESS_DISPATCH)

#
REROUTE_AFTER_ABANDONED = 30.0		# Reroute after disconnect but give opportunity for recovery, i.e. FALLBACK
REROUTE_AFTER_UPGRADE = 2.0			# Reroute due to arrival of a better routing option, i.e. UPGRADE

DEFERRED_CHECK_FOR_UNUSED = 30.0	# Route removed from ConnectToPeer. See if its empty for this long.

class ObjectDirectory(Threaded, StateMachine):
	def __init__(self, directory_scope: ScopeOfDirectory=None, connect_to_directory: HostPort=None, accept_directories_at: HostPort=None):
		Threaded.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.directory_scope = directory_scope or ScopeOfDirectory.PROCESS
		self.connect_to_directory = connect_to_directory or HostPort()
		self.accept_directories_at = accept_directories_at or HostPort()

		# Links to the upper and lower parts of the hierarchy.
		self.connected = None
		self.listening = None
		self.accepted = {}				# Remember who connects from below and what they provide.
		self.pending_enquiry = set()

		# Keep the db clean.
		self.unique_publish = {}
		self.unique_subscribe = {}

		# For quick lookup and distribution.
		self.listed_publish = {}
		self.listed_subscribe = {}

		# For quick matching.
		self.published = {}
		self.subscribed = {}

		# Routed listings.
		self.routed_publish = {}
		self.routed_subscribe = {}

		# Routing tables for active loops.
		self.subscriber_routing = {}

		# Connections across group, host and lan domains.
		self.peer_connect = {}

	def add_publisher(self, listing, origin, publish):
		name = listing.name
		scope = listing.scope

		# Existence - by id.
		lp = self.listed_publish.get(listing.published_id, None)
		if lp is not None:
			self.warning(f'cannot publish "{name}" (already listed)')
			return False

		# And search name.
		lp = self.published.get(name, None)
		if lp is not None:
			self.warning(f'cannot publish "{name}" (already matching)')
			return False

		if publish:
			# Publishing object is in this process. Is an
			# access point required.
			if scope.value < ScopeOfDirectory.PROCESS.value:
				a = self.create(ListeningForPeer, name, scope, publish.address)
				self.assign(a, (listing, publish))
				return False

		elif self.directory_scope == ScopeOfDirectory.LAN:
			# This directory overlooks a LAN. Overwrite the given
			# listening ip (0.0.0.0) with the ip provided by sockets.
			a, sub, pub = self.accepted.get(self.return_address[-1])
			listing.listening_ipp = HostPort(a.opened_ipp.host, listing.listening_ipp.port)

		elif self.directory_scope in (ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
			# This directory overlooks a HOST or GROUP. Overwrite whatever
			# was provided with the loopback address.
			listing.listening_ipp = HostPort('127.0.0.1', listing.listening_ipp.port)
		elif self.directory_scope in (ScopeOfDirectory.PROCESS, ScopeOfDirectory.LIBRARY):
			pass
		else:
			self.warning(f'Scope [{self.directory_scope}] not implemented')
			return False

		self.console(f'Published[{self.directory_scope}]', name=name, listening=listing.listening_ipp)

		lp = (listing, publish)
		self.published[name] = lp
		self.listed_publish[listing.published_id] = lp

		if origin is not None:
			origin.add(listing.published_id)
		return True

	def add_subscriber(self, listing, origin, subscribe):
		search = listing.search
		scope = listing.scope
		subscribed_id = listing.subscribed_id

		# Existence - by id.
		ls = self.listed_subscribe.get(listing.subscribed_id, None)
		if ls is not None:
			self.warning(f'Cannot subscribe "{search}" (id already listed)')
			return False

		# and search. Build out required structure.
		sr = self.subscribed.get(search, None)
		if sr is None:
			try:
				# Keep a single pre-compiled search machine.
				r = re.compile(listing.search)
			except re.error as e:
				t = str(e)
				self.warning(f'Cannot subscribe to {search}[{scope}] ({t})')
				return False
			s = {}
			sr = [s, r]
			self.subscribed[search] = sr
		else:
			s = sr[0]

		# Existence of subscriber.
		if subscribed_id in s:
			self.warning(f'Cannot subscribe {search}[{scope}] (already listed)')
			return False

		self.console(f'Subscribed[{self.directory_scope}]', search=search)

		ls = (listing, subscribe)
		s[subscribed_id] = ls
		self.listed_subscribe[subscribed_id] = ls

		if origin is not None:
			origin.add(listing.subscribed_id)
		return True

	def find_subscribers(self, published):
		# Turn a search into a flat list of matching subscribers.
		for k, v in self.subscribed.items():
			m = v[1].match(published.name)
			if m:
				for s in v[0].values():
					yield s[0]

	def find_publishers(self, subscribed):
		# Turn a search into a flat list of matching publishers.
		sr = self.subscribed.get(subscribed.search, None)
		if sr is None:
			return
		machine = sr[1]
		for k, lp in self.published.items():
			m = machine.match(k)
			if m:
				yield lp[0]

	def create_route(self, subscriber, publisher):
		self.console(f'Route[{self.directory_scope}]', name=publisher.name)
		# There is a match at this scope between given sub and pub.
		# Create the appropriate route object and record its existence.
		# Communication with relevant directories is up to the route.

		route_id = uuid.uuid4()
		if self.directory_scope in (ScopeOfDirectory.LAN, ScopeOfDirectory.HOST, ScopeOfDirectory.GROUP):
			r = self.create(RouteOverConnect, route_id=route_id, scope=self.directory_scope, subscriber=subscriber, publisher=publisher)

		elif self.directory_scope == ScopeOfDirectory.PROCESS:
			s = self.listed_subscribe[subscriber.subscribed_id][1]
			p = self.listed_publish[publisher.published_id][1]

			r = self.create(RouteInProcess, route_id=route_id,
				subscriber=subscriber, publisher=publisher,
				subscriber_address=s.address, publish_as=p)

		else:
			self.warning(f'Cannot route "{publisher.name}" at [{self.directory_scope}]')
			return

		# When this publisher is cleared, nudge this route.
		pr = self.routed_publish.get(publisher.published_id, None)
		if pr is None:
			pr = [publisher, set()]
			self.routed_publish[publisher.published_id] = pr
		pr[1].add(r)

		# When this subscriber is cleared, nudge this route.
		sr = self.routed_subscribe.get(subscriber.subscribed_id, None)
		if sr is None:
			sr = [subscriber, set()]
			self.routed_subscribe[subscriber.subscribed_id] = sr
		sr[1].add(r)

		# When the route terminates, clear out the links.
		def clear(value, kv):
			pr = self.routed_publish.get(kv.published_id)
			if pr is not None:
				pr[1].discard(kv.route)

			sr = self.routed_subscribe.get(kv.subscribed_id)
			if sr is not None:
				sr[1].discard(kv.route)

		self.begin(r, clear, subscribed_id=subscriber.subscribed_id, published_id=publisher.published_id, route=r)

	def clear_listings(self, subscribers, publishers):
		stop = Stop()
		for s in subscribers:
			r = self.routed_subscribe.get(s, None)
			if r:
				for a in r[1]:
					self.send(stop, a)
			p = self.listed_subscribe.pop(s, None)
			if p is None:
				continue
			g = self.subscribed.get(p[0].search, None)
			if g is None:
				continue
			a, sub = g
			a.pop(s, None)
			if p[1] is not None:
				unique_subscribe = (p[1].search, p[1].address)
				self.unique_subscribe.pop(unique_subscribe, None)

		for p in publishers:
			r = self.routed_publish.get(p, None)
			if r:
				for a in r[1]:
					self.send(stop, a)
			p = self.listed_publish.pop(p, None)
			if p is None:
				continue
			self.published.pop(p[0].name, None)
			if p[1] is not None:
				unique_publish = p[1].name
				self.unique_publish.pop(unique_publish, None)

	def open_route(self, route):
		# Initiate the given route.
		# Housekeeping for RouteOverLoop.
		def clear_ipp(value, kv):
			requested, p, a = cast_back(value)
			self.console('Clearing peer connection', ipp=kv.ipp, requests=len(requested))
			p = self.peer_connect.pop(kv.ipp, None)
			if p is None:
				return

			for r in requested:
				try:
					routing = self.subscriber_routing[r.subscribed_id][r.name]
				except (KeyError, IndexError):
					continue

				if routing[0] is None:
					continue
				if r.route_id == routing[0].route_id:
					routing[0] = None
					self.create(ScheduledReroute, r.subscribed_id, r.name, seconds=REROUTE_AFTER_ABANDONED)

		# Per route type.
		if isinstance(route, RouteOverLoop):
			listing = self.listed_subscribe.get(route.subscribed_id, None)
			c = self.peer_connect.get(route.ipp, None)
			if c is None:
				c = self.create(ConnectToPeer, route.ipp)
				self.begin(c, clear_ipp, ipp=route.ipp)
				self.peer_connect[route.ipp] = c
			address = listing[1].address
			r = RequestLoop(subscribed_id=route.subscribed_id, name=route.name, subscriber_address=address,
				published_id=route.published_id,
				route_id=route.route_id)
			self.forward(r, c, address)

		elif isinstance(route, RouteToAddress):
			s = self.listed_subscribe.get(route.subscribed_id, None)
			p = self.listed_publish.get(route.published_id, None)
			opened_at = world_now()
			a = Available(route_id=self.route_id, address=p[1].address, opened_at=opened_at)
			d = Delivered(route_id=self.route_id, address=s[1].address, opened_at=opened_at)
			self.forward(a, s[1].address, p[1].address)
			self.forward(d, p[1].address, s[1].address)
		else:
			self.warning('not implemented')

	def drop_route(self, listing, route):
		if isinstance(route, RouteOverLoop):
			c = self.peer_connect.get(route.ipp, None)
			if c is None:
				return
			self.send(CloseLoop(route_id=route.route_id, address=listing[1].address), c)

		elif isinstance(route, RouteToAddress):
			closed_at = world_now()
			s = Dropped(route_id=self.route_id, address=self.publisher[1].address, closed_at=closed_at)
			p = Dropped(route_id=self.route_id, address=self.subscriber[1].address, closed_at=closed_at)
			self.forward(s, self.subscriber[1].address, self.publisher[1].address)
			self.forward(p, self.publisher[1].address, self.subscriber[1].address)

		# For all types of dropped route.
		self.create(ScheduledReroute, route.subscribed_id, route.name, REROUTE_AFTER_UPGRADE)

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

	unique_publish = name
	r = self.unique_publish.get(unique_publish, None)
	if r is not None:
		self.reply(NotPublished(name=name, scope=scope, note=f'already published'))
		return READY

	published_id = uuid.uuid4()
	listing = Published(name=name, scope=scope, published_id=published_id, home_address=self.object_address)

	if not self.add_publisher(listing, None, message):
		return READY
	self.unique_publish[unique_publish] = published_id
	if self.directory_scope.value < ScopeOfDirectory.LIBRARY.value:
		self.send(listing, message.address)

	for s in self.find_subscribers(listing):
		self.create_route(s, listing)
	self.send_up(listing)
	return READY

def ObjectDirectory_READY_HostPort(self, message):
	d = self.progress()
	if d is None:
		self.warning(f'cannot complete ListenForPeer (no message record)')
		return READY
	listing, publish = d
	listing.listening_ipp = message		# Update with live network address.

	self.console(f'Published[{self.directory_scope}]', name=listing.name, listening=message)
	
	self.published[listing.name] = (listing, publish)
	self.listed_publish[listing.published_id] = (listing, publish)

	unique_publish = publish.name
	self.unique_publish[unique_publish] = listing.published_id
	self.send(listing, publish.address)

	for s in self.find_subscribers(listing):
		self.create_route(s, listing)
	self.send_up(listing)

	return READY

def ObjectDirectory_READY_SubscribeTo(self, message):
	search = message.search
	scope = message.scope

	unique_subscribe = (search, self.return_address)
	r = self.unique_subscribe.get(unique_subscribe, None)
	if r is not None:
		self.reply(NotSubscribed(search=search, scope=scope, note=f'already subscribed'))
		return READY

	subscribed_id = uuid.uuid4()
	listing = Subscribed(search=search, scope=scope, subscribed_id=subscribed_id, home_address=self.object_address)
	if not self.add_subscriber(listing, None, message):
		self.reply(NotSubscribed(search=search, scope=scope, note=f'duplicates/search expression'))
		return READY
	self.unique_subscribe[unique_subscribe] = subscribed_id
	self.send(listing, message.address)

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
		self.warning('No such subscription')
		return READY

	# Find the routing table.
	subscriber = self.subscriber_routing.get(subscribed_id, None)
	if subscriber is None:
		return READY

	routing = subscriber.get(message.name, None)
	if routing is None:
		return READY

	# Delete the route.
	if not delete_route(message.route_id, routing[1]):
		self.warning('Unknown route')
		return READY

	# Clear out empty vessels.
	if len(routing[1]) == 0:
		subscriber.pop(message.name, None)

	if len(subscriber) == 0:
		self.subscriber_routing.pop(subscribed_id, None)
	return READY

def ObjectDirectory_READY_ClearPublisherRoute(self, message):
	p = self.listed_publish.get(message.published_id, None)
	if p is None:
		return READY
	# So far there is no action required on the
	# publisher side.
	return READY

def ObjectDirectory_READY_ResolveLibrary(self, message):
	p = self.published.get(message.name, None)
	if p is None:
		return READY
	address = p[1].address
	self.forward(Available(address=address), self.return_address, address)
	return READY

def find_route(route, routing):
	for r in routing:
		if r.scope == route.scope:
			return True
	return False

def shortest_route(routing):
	best = None
	for r in routing:
		if best is None or r.scope.value > best.scope.value:
			best = r
	return best

def add_route(route, routing):
	before = shortest_route(routing)
	routing.append(route)
	shortest = shortest_route(routing)
	return before, shortest

def delete_route(route_id, routing):
	d = None
	for i, r in enumerate(routing):
		if r.route_id == route_id:
			d = i
	if d is not None:
		r = routing.pop(d)
		return r
	return None

def ObjectDirectory_READY_SubscriberRoute(self, message):
	subscribed_id = message.subscribed_id

	# Add the route to the routing[subscriber][name] table.
	# Evaluate the (changed) routing options.
	# If no current loop, initiate the best option.
	listing = self.listed_subscribe.get(subscribed_id, None)
	if listing is None or listing[1] is None:
		self.warning('No such subscription or not the home directory')
		return READY

	# Routing per listing
	subscriber = self.subscriber_routing.get(subscribed_id, None)
	if subscriber is None:
		subscriber = {}
		self.subscriber_routing[subscribed_id] = subscriber

	# Per matched name
	routing = subscriber.get(message.name, None)
	if routing is None:
		routing = [None, []]
		subscriber[message.name] = routing

	# Final checks.
	if find_route(message, routing[1]):
		self.warning(f'Duplicate route at [{message.scope}]')
		return READY

	# Evaluate what affect the addition of this route will
	# have on this subscriber-to-name connection effort.
	before, shortest = add_route(message, routing[1])

	if routing[0] is None:	# No current attempt to connect.
		pass
	elif before is None:	# Table had been emptied.
		pass
	elif shortest.scope.value > before.scope.value:
		r = routing[0]
		routing[0] = None
		self.drop_route(listing, r)
		return READY
	else:
		# Longer route was added.
		return READY

	routing[0] = shortest
	self.open_route(shortest)
	return READY

def ObjectDirectory_READY_RerouteSubscriber(self, message):
	subscribed_id = message.subscribed_id
	name = message.name

	try:
		routing = self.subscriber_routing[subscribed_id][name]
	except (KeyError, IndexError):
		return READY

	if routing[0] is not None:		# Routed by some other means.
		return READY

	shortest = shortest_route(routing[1])	# Get the best.
	if shortest is None:					# Nothing there.
		return READY
	routing[0] = shortest
	self.open_route(shortest)
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
		RerouteSubscriber,
		ResolveLibrary,
		SubscriberRoute,
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
