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

import uuid
import re
import ansar.create as ar
from .socketry import *
from .transporting import *
from .plumbing import *
from .cloud import *
from .model import *
from .instant import *

__all__ = [
	'pb',
	'find_overlap',
	'ScopeOfService',
	'publish',
	'subscribe',
	'retract',
	'clear',
	'key_service',
	'Published',
	'NotPublished',
	'Subscribed',
	'Available',
	'NotAvailable',
	'Delivered',
	'NotDelivered',
	'Clear',
	'Cleared',
	'Dropped',
	'scope_connection',
	'DirectoryEnquiry',
	'DirectoryReconnect',
	'DirectoryScope',
	'DirectoryAncestry',
	'ServiceDirectory',
	'RouteByRelay',
	'InboundByRelay',
	'OpenLoop',
]

#
#
def ipp_key(ipp):
	return f'{ipp.host}:{ipp.port}'

def find_overlap(table, address):
	a = address[-1]
	for k, v in table.items():
		if k[-1] == a:
			return k, v
	return None, None

# directory ... names and lookups and addresses relating to both
# sockets ..... dedicated sockets engine
# channel ..... back channel to sockets
# house ....... container of listen/connect service controllers.
pb = ar.Gas(directory=None, sockets=None, channel=None, house=None)

def create_directory(root):
	# Directory created in node_vector()
	# but stopped below.
	pb.sockets = root.create(SocketSelect)
	pb.channel = root.select(SocketChannel)
	pb.house = root.create(PubSub)

def stop_directory(root):
	root.send(ar.Stop(), pb.house)
	root.select(ar.Completed)
	pb.channel.send(ar.Stop(), root.address)
	root.select(ar.Completed)
	# Stop the directory started by
	# node_vector().
	if pb.directory is not None:
		root.send(ar.Stop(), pb.directory)
		# NOTE!
		# The root object did not create this
		# object so normal completion cannot be
		# used. The directory object is specifically
		# coded to respond to Stop with an Ack. As
		# well as completing.
		root.select(ar.Ack, seconds=5.0)

ar.AddOn(create_directory, stop_directory)

# Build the local published/subscribed objects.
#
ScopeOfService = ar.Enumeration(PROCESS=1, GROUP=2, HOST=3, LAN=4, WAN=5)

#
#
class PublishAsName(object):
	def __init__(self, requested_name=None, create_session=None, declared_scope=ScopeOfService.WAN):
		self.requested_name = requested_name
		self.create_session = create_session
		self.declared_scope = declared_scope

class Published(object):
	def __init__(self, published_name=None, declared_scope=ScopeOfService.WAN, listening_ipp=None):
		self.published_name = published_name
		self.declared_scope = declared_scope
		self.listening_ipp = listening_ipp or HostPort()

class NotPublished(object):
	def __init__(self, requested_name=None, reason=None):
		self.requested_name = requested_name
		self.reason = reason

class SubscribeToName(object):
	def __init__(self, requested_search=None, create_session=None, declared_scope=ScopeOfService.WAN):
		self.requested_search = requested_search
		self.create_session = create_session
		self.declared_scope = declared_scope

class Subscribed(object):
	def __init__(self, subscribed_search=None, declared_scope=ScopeOfService.WAN):
		self.subscribed_search = subscribed_search
		self.declared_scope = declared_scope

class Retract(object):
	def __init__(self, address=None):
		self.address = address

# The actual service directory with listings and searches.
#
class ServiceListing(object):
	def __init__(self, requested_name=None, agent_address=None, declared_scope=ScopeOfService.WAN, listening_ipp=None, connecting_ipp=None):
		self.requested_name = requested_name
		self.agent_address = agent_address
		self.declared_scope = declared_scope
		self.listening_ipp = listening_ipp or HostPort()
		self.connecting_ipp = connecting_ipp or HostPort()

class FindService(object):
	def __init__(self, requested_search=None, agent_address=None, declared_scope=ScopeOfService.WAN):
		self.requested_search = requested_search
		self.agent_address = agent_address
		self.declared_scope = declared_scope

class PushedDirectory(object):
	def __init__(self, listing=None, find=None):
		self.listing = listing
		self.find = find

	def empty(self):
		if len(self.listing) == 0 and len(self.find) == 0:
			return True
		return False

class UnlistService(object):
	def __init__(self, requested_name=None, agent_address=None, declared_scope=None):
		self.requested_name = requested_name
		self.agent_address = agent_address
		self.declared_scope = declared_scope

class UnlistFind(object):
	def __init__(self, subscribed_search=None, agent_address=None, declared_scope=None):
		self.subscribed_search = subscribed_search
		self.agent_address = agent_address
		self.declared_scope = declared_scope

class RetractRoute(object):
	def __init__(self, key=None):
		self.key = key

class TrimRoutes(object):
	def __init__(self, address=None):
		self.address = address

class CapRoutes(object):
	def __init__(self, service_scope=None):
		self.service_scope = service_scope

# Session messages to publish/listen controllers.
# Subscribe/client/calling/outbound end.
class Available(object):
	def __init__(self, key=None, agent_address=None):
		self.key = key
		self.agent_address = agent_address

class NotAvailable(object):
	def __init__(self, key=None, reason=None, agent_address=None):
		self.key = key
		self.reason = reason
		self.agent_address = agent_address

# Publish/service/answering/inbound end.
class Delivered(object):
	def __init__(self, key=None, agent_address=None):
		self.key = key
		self.agent_address = agent_address

class NotDelivered(object):
	def __init__(self, published_name=None, remote_address=None):
		self.published_name = published_name
		self.remote_address = remote_address

class Clear(object):
	def __init__(self, session=None, value=None):
		self.session = session
		self.value = value

class Cleared(object):
	def __init__(self, value=None):
		self.value = value

class Dropped(object):
	def __init__(self, reason=None):
		self.reason = reason

ENDING_SCHEMA = {
	'session': ar.Any,
	'value': ar.Any,
	'reason': str,
}

ar.bind(Clear, object_schema=ENDING_SCHEMA, copy_before_sending=False)
ar.bind(Cleared, object_schema=ENDING_SCHEMA, copy_before_sending=False)
ar.bind(Dropped, object_schema=ENDING_SCHEMA, copy_before_sending=False)

SHARED_SCHEMA = {
	#'key': ar.VectorOf(ar.Integer8()),
	'key': str,
	'name': str,
	'requested_name': str,
	'requested_search': str,
	'published_name': str,
	'subscribed_search': str,
	'create_session': ar.Type(),
	'published_name': str,
	'remote_address': ar.Address(),
	'session_address': ar.Address(),
	'declared_scope': ScopeOfService,
	'service_scope': ScopeOfService,
	'reason': ar.String(),
	'listening_ipp': ar.UserDefined(HostPort),
	'connecting_ipp': ar.UserDefined(HostPort),
	'parent_ipp': ar.UserDefined(HostPort),
	'child_ipp': ar.UserDefined(HostPort),
	'subscription': ar.UserDefined(Subscribed),
	'agent_address': ar.Address(),
	'address': ar.Address(),
}

ar.bind(Subscribed, object_schema=SHARED_SCHEMA)
ar.bind(Published, object_schema=SHARED_SCHEMA)
ar.bind(PublishAsName, object_schema=SHARED_SCHEMA)
ar.bind(SubscribeToName, object_schema=SHARED_SCHEMA)
ar.bind(Retract, object_schema=SHARED_SCHEMA)
ar.bind(ServiceListing, object_schema=SHARED_SCHEMA)
ar.bind(FindService, object_schema=SHARED_SCHEMA)
ar.bind(UnlistService, object_schema=SHARED_SCHEMA)
ar.bind(UnlistFind, object_schema=SHARED_SCHEMA)
ar.bind(Available, object_schema=SHARED_SCHEMA)
ar.bind(NotAvailable, object_schema=SHARED_SCHEMA)
ar.bind(Delivered, object_schema=SHARED_SCHEMA)
ar.bind(NotDelivered, object_schema=SHARED_SCHEMA)
ar.bind(TrimRoutes, object_schema=SHARED_SCHEMA)
ar.bind(CapRoutes, object_schema=SHARED_SCHEMA)
ar.bind(RetractRoute, object_schema=SHARED_SCHEMA)

COPY_SCHEMA = {
	'listing': ar.VectorOf(ar.UserDefined(ServiceListing)),
	'find': ar.VectorOf(ar.UserDefined(FindService)),
}

ar.bind(PushedDirectory, object_schema=COPY_SCHEMA)

#
#
class DirectoryScope(object):
	def __init__(self, scope=None, connecting_ipp=None, method=None, started=None, connected=None, lfa=None):
		self.scope = scope
		self.connecting_ipp = connecting_ipp or HostPort()
		self.method = method
		self.started = started
		self.connected = connected
		self.lfa = lfa or [0, 0, 0]

DIRECTORY_SCOPE_SCHEMA = {
	'scope' : ScopeOfService,
	'connecting_ipp': ar.UserDefined(HostPort),
	'method': ar.Unicode(),
	'started': ar.WorldTime(),
	'connected': ar.WorldTime(),
	'lfa': ar.ArrayOf(ar.Integer8(), 3),
}

ar.bind(DirectoryScope, object_schema=DIRECTORY_SCOPE_SCHEMA)

#
#
class DirectoryEnquiry(object):
	def __init__(self, scope=None, lineage=None):
		self.scope = scope
		self.lineage = lineage or ar.default_vector()

DIRECTORY_ENQUIRY_SCHEMA = {
	'scope': ScopeOfService,
	'lineage': ar.VectorOf(DirectoryScope),
}

ar.bind(DirectoryEnquiry, object_schema=DIRECTORY_ENQUIRY_SCHEMA)

#
#
class DirectoryReconnect(object):
	def __init__(self, scope=None, connect_above=None):
		self.scope = scope
		self.connect_above = connect_above

DIRECTORY_RECONNECT_SCHEMA = {
	'scope': ScopeOfService,
	'connect_above': ar.Any(),
}

ar.bind(DirectoryReconnect, object_schema=DIRECTORY_RECONNECT_SCHEMA)

#
#
class DirectoryAncestry(object):
	def __init__(self, lineage=None):
		self.lineage = lineage or ar.default_vector()

DIRECTORY_ANCESTRY_SCHEMA = {
	'lineage': ar.VectorOf(DirectoryScope),
}

ar.bind(DirectoryAncestry, object_schema=DIRECTORY_ANCESTRY_SCHEMA)

# All the distinct machine states used by this
# module.
class INITIAL: pass
class NORMAL: pass
class OPENING: pass
class PENDING: pass
class LATCHING: pass
class ACCEPTING: pass
class READY: pass
class LOOPED: pass
class ROUTING: pass
class CLEARING: pass
class GLARING: pass
class CLOSING: pass
class STANDBY: pass
class CARETAKER: pass
class COMPLETING: pass
class RELAYING: pass

def address_to_text(a):
	t = ','.join([f'{i:x}' for i in a])
	return t

# This is the object that owns and manages the routing between
# a subscriber and a service. It is created on a match and
# updates the two parties as needed. Routes are fairly static.
# They are only affected by changes to the directory tree. Routes
# are the basis for sessions. The session abstraction is in the
# SubscriptionAgent object using "loop" messages to establish
# a "subscriber loop" to a remote end over dedicated transports,
# i.e. not the same transports used by the directory tree.
class ServiceRoute(ar.Point, ar.StateMachine):
	def __init__(self, key, find_address, listing_address, connection):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.key = key
		self.find_address = find_address
		self.listing_address = listing_address
		self.connection = connection

def ServiceRoute_INITIAL_Start(self, message):
	if isinstance(self.connection, ServiceByRelay):
		relay_id = uuid.uuid4()
		self.send(RelayLookup(relay_id=relay_id), self.connection.relay_address)
		self.start(ar.T1, 5.0)
		return RELAYING
	outbound = self.connection.outbound(self.key)
	inbound = self.connection.inbound(self.key)

	out_type = outbound.__art__.name
	in_type = inbound.__art__.name

	out_address = address_to_text(self.find_address)
	in_address = address_to_text(self.listing_address)

	self.trace(f'Match sends "{out_type}" to [{out_address}]')
	self.trace(f'And "{in_type}" to [{in_address}]')

	self.send(outbound, self.find_address)
	self.send(inbound, self.listing_address)
	return NORMAL

def ServiceRoute_RELAYING_RelayRedirect(self, message):
	self.connection.redirect = message
	outbound = self.connection.outbound(self.key)
	inbound = self.connection.inbound(self.key)

	out_type = outbound.__art__.name
	in_type = inbound.__art__.name

	out_address = address_to_text(self.find_address)
	in_address = address_to_text(self.listing_address)

	self.trace(f'Match sends "{out_type}" to [{out_address}]')
	self.trace(f'And "{in_type}" to [{in_address}]')

	self.send(outbound, self.find_address)
	self.send(inbound, self.listing_address)
	return NORMAL

def ServiceRoute_RELAYING_T1(self, message):
	out_address = address_to_text(self.find_address)
	in_address = address_to_text(self.listing_address)

	self.trace(f'Failed relay from [{out_address}] to [{in_address}]')
	self.complete(ar.Aborted())

def ServiceRoute_NORMAL_Stop(self, message):
	out_address = address_to_text(self.find_address)
	in_address = address_to_text(self.listing_address)

	self.trace(f'Match sends RetractRoute to [{out_address}] and [{in_address}] and completes')
	
	self.send(RetractRoute(self.key), self.find_address)
	self.send(RetractRoute(self.key), self.listing_address)
	self.complete(ar.Aborted())

SERVICE_ROUTE_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	RELAYING: (
		(RelayRedirect, ar.T1), ()
	),
	NORMAL: (
		(ar.Stop,), ()
	),
}

ar.bind(ServiceRoute, SERVICE_ROUTE_DISPATCH)

# Messages from match object (ServiceRoute) to the two different
# ends of the relation. The PublishingAgent and SubscriptionAgent objects
# will receive and initiate "calls" based on these messages.
class RouteToAddress(object):
	def __init__(self, scope=None, address=None, key=None):
		self.scope = scope
		self.address = address
		self.key = key

class InboundFromAddress(object):
	def __init__(self, scope=None, address=None, key=None):
		self.scope = scope
		self.address = address
		self.key = key

class RouteOverConnected(object):
	def __init__(self, scope=None, connecting_ipp=None, key=None):
		self.scope = scope
		self.connecting_ipp = connecting_ipp or HostPort()
		self.key = key

class InboundOverAccepted(object):
	def __init__(self, scope=None, key=None):
		self.scope = scope
		self.key = key

class RouteByRelay():
	def __init__(self, scope=None, redirect=None, key=None):
		self.scope = scope
		self.redirect = redirect or RelayRedirect()
		self.key = key

class InboundByRelay():
	def __init__(self, scope=None, redirect=None, key=None):
		self.scope = scope
		self.redirect = redirect or RelayRedirect()
		self.key = key

IO_SCHEMA = {
	'address': ar.Address(),
	'key': str,
	'name': str,
	'connecting_ipp': ar.UserDefined(HostPort),
	'scope': ScopeOfService,
	'redirect': ar.UserDefined(RelayRedirect),
}

ar.bind(RouteToAddress, object_schema=IO_SCHEMA)
ar.bind(InboundFromAddress, object_schema=IO_SCHEMA)
ar.bind(RouteOverConnected, object_schema=IO_SCHEMA)
ar.bind(InboundOverAccepted, object_schema=IO_SCHEMA)
ar.bind(RouteByRelay, object_schema=IO_SCHEMA)
ar.bind(InboundByRelay, object_schema=IO_SCHEMA)

#
#
class OpenPeer(object):
	def __init__(self, connecting_ipp=None, key=None):
		self.connecting_ipp = connecting_ipp or HostPort()
		self.key = key

class PeerOpened(object):
	def __init__(self, connecting_ipp=None, key=None):
		self.connecting_ipp = connecting_ipp or HostPort()
		self.key = key

class NotPeered(object):
	def __init__(self, key=None, reason = None):
		self.key = key
		self.reason = reason

class ClosePeer(object):
	def __init__(self, connecting_ipp=None, key=None):
		self.connecting_ipp = connecting_ipp or HostPort()
		self.key = key

PEER_SCHEMA = {
	'connecting_ipp': ar.UserDefined(HostPort),
	'key': str,
	'reason': str,
}

ar.bind(OpenPeer, object_schema=PEER_SCHEMA)
ar.bind(PeerOpened, object_schema=PEER_SCHEMA)
ar.bind(NotPeered, object_schema=PEER_SCHEMA)
ar.bind(ClosePeer, object_schema=PEER_SCHEMA)

# Objects that capture the requirements for 3 different methods
# of connection between subscriber and publisher.
class DirectService(object):
	def __init__(self, find, listing):
		self.find = find
		self.listing = listing

	def outbound(self, key):
		return RouteToAddress(ScopeOfService.PROCESS, self.listing.agent_address, key)

	def inbound(self, key):
		return InboundFromAddress(ScopeOfService.PROCESS, self.find.agent_address, key)

# Between two objects needing a TCP connection from
# subscribing process to publishing process. Listening
# address needs tuning based on whether its intra-host
# or across a LAN.
class ServiceOverConnection(object):
	def __init__(self, scope, find, listing):
		self.scope = scope
		self.find = find
		self.listing = listing

	def outbound(self, key):
		return RouteOverConnected(self.scope, self.listing.connecting_ipp, key)

	def inbound(self, key):
		return InboundOverAccepted(self.scope, key)

# The extra step needed for relay setup. A query/response
# needed with the relay manager before the connection
# messages can be sent to the ends of the call.
class ServiceByRelay(object):
	def __init__(self, finding, listing, relay_address):
		self.relay_address = relay_address
		self.redirect = None

	def outbound(self, key):
		return RouteByRelay(ScopeOfService.WAN, self.redirect, key)

	def inbound(self, key):
		return InboundByRelay(ScopeOfService.WAN, self.redirect, key)

# The per-process part of the distributed name service.
# Accepts local listings and searches and creates matches.
# Receives listings and searches from below as well. All
# information forwarded to next level up.
def key_service(key):
	try:
		i = key.index(':')
	except ValueError:
		return None
	return key[i + 1:]

def overlapping_route(a, b):
	ra = reversed(a)
	rb = reversed(b)
	for x, y in zip(ra, rb):
		if x != y:
			return False
	return True

CONNECT_ABOVE = 'connect-above'
ACCEPT_BELOW = 'accept-below'

class ServiceDirectory(ar.Threaded, ar.StateMachine):
	def __init__(self, scope=None, connect_above=None, accept_below=None):
		ar.Threaded.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.scope = scope or ScopeOfService.PROCESS
		self.connect_above = connect_above
		self.accept_below = accept_below or HostPort()
		self.directory = {}
		self.find = {}
		self.origin = {}
		self.matched = {}
		self.connected_up = None
		self.not_connected = None
		self.connected = None
		self.listening = None
		self.accepted = {}
		self.started = None
		self.stopped = None

	def found(self, service_name, f, d):
		find = f[0]
		listing = d[0]
		find_address = find.agent_address
		find_matched = f[1]
		listing_address = listing.agent_address
		listing_matched = d[1]

		# As well as being unique within this directory the
		# connection engine in the subscriber agent relies on
		# content and layout of this key. Refer to
		# key_service().
		who = address_to_text(find_address)
		key = f'{who}:{listing.requested_name}'

		if key in self.matched:
			self.warning(f'Duplicate find/service match [{ScopeOfService.to_name(self.scope)}] "{key}"')
			return
		self.trace(f'Adds route [{ScopeOfService.to_name(self.scope)}] "{key}"')

		# Everything lines up - we have a relation. Connection details
		# are dependent on where this directory is running.
		if self.scope == ScopeOfService.PROCESS:
			a = self.create(ServiceRoute, key, find_address, listing_address, DirectService(find, listing))
		elif self.scope in (ScopeOfService.GROUP, ScopeOfService.HOST, ScopeOfService.LAN):
			a = self.create(ServiceRoute, key, find_address, listing_address, ServiceOverConnection(self.scope, find, listing))
		elif self.scope == ScopeOfService.WAN:
			a = self.create(ServiceRoute, key, find_address, listing_address, ServiceByRelay(find, listing, self.parent_address))
		else:
			self.warning(f'Directory at unknown scope "{self.scope}"')
		self.assign(a, key)
		self.matched[key] = a
		find_matched.add(key)
		listing_matched.add(key)

	def conclude_host(self, address, message):
		"""Determine a host address suitable for connection.

		Combine the network info accumulated for accepted connections
		and the information offered in a service listing to resolve
		the most appropriate host address to use for connection. Most
		significantly this means overlaying an "IP any" address with
		the address of the remote host available at the moment of
		accepting. This will resolve to either a local host (127.x)
		or LAN address (e.g. 192.x) as the calling process gets
		further away from the offering. That info is then sent to
		processes below this directory that will know the service
		host by the same address as this process remembers accepting
		from.
		"""
		try:
			# Is there a record of accepting a session with
			# the given proxy address.
			r, a = find_overlap(self.accepted, address)
		except KeyError:
			self.warning(f'Cannot resolve connection address for {message.requested_name} - no record of accepting')
			message.connecting_ipp.host = None
			return
		if message.listening_ipp.host == '0.0.0.0':
			message.connecting_ipp.host = a.accepted_ipp.host
		else:
			message.connecting_ipp.host = message.listening_ipp.host
		message.connecting_ipp.port = message.listening_ipp.port

	### PS-pub-10 Directory installs a new service.
	def add_listing(self, message):
		service_name = message.requested_name

		d = self.directory.get(service_name, None)
		if d is None:
			d = [message, set()]
			self.directory[service_name] = d
			self.trace(f'Added listing "{service_name}"')
		else:
			self.warning(f'Duplicate listing for "{service_name}"')
			d[0] = message

		# Match listing to finds.
		for _, f in self.find.items():
			dfa = f[2]
			m = dfa.match(service_name)
			if m:
				### PS-pub-10 New service matches existing search.
				self.found(service_name, f, d)

		return

		# Not duplicates - yet.
		if service_name in self.directory:
			self.warning(f'Duplicate listing for "{service_name}"')
			return

		# Add service to table
		d = [message, set()]
		self.directory[service_name] = d
		self.trace(f'Added listing "{service_name}"')

		# Match listing to finds.
		for _, f in self.find.items():
			dfa = f[2]
			m = dfa.match(service_name)
			if m:
				### PS-pub-10 New service matches existing search.
				self.found(service_name, f, d)

	### PS-sub-9 Directory installs a new search.
	def add_find(self, message):
		find_name = message.requested_search
		find_address = message.agent_address

		jf = address_to_text(find_address)
		k = f'{jf}/{find_name}'
		if k in self.find:
			self.warning(f'Duplicate find for "{k}"')
			return

		try:
			dfa = re.compile(find_name)
		except re.error as e:
			self.warning(f'Cannot compile expression "{e.msg}"')
			return

		# Add client to table
		f = [message, set(), dfa]
		self.find[k] = f
		self.trace(f'Added search "{k}"')

		# Match find to listings.
		for service_name, d in self.directory.items():
			m = dfa.match(service_name)
			if m:
				### PS-sub-9 New find matches existing service.
				self.found(service_name, f, d)

	def remove_listing(self, message):
		service_name = message.requested_name

		# Remove the entry and terminate any routes that
		# were based on its existence.
		# d = [message, set()]
		d = self.directory.pop(service_name, None)
		if d is None:
			self.warning(f'Unknown service listing for "{service_name}"')
			return
		self.trace(f'Removed listing "{service_name}" ({len(d[1])} matches to stop)')
		
		for k in d[1]:
			a = self.matched.get(k, None)
			if a:
				self.send(ar.Stop(), a)

	def remove_find(self, message):
		find_name = message.subscribed_search
		find_address = message.agent_address

		jf = address_to_text(find_address)
		k = f'{jf}/{find_name}'

		# Remove the entry and terminate any routes that
		# were based on its existence.
		# f = [message, set()]
		f = self.find.pop(k, None)
		if f is None:
			self.warning(f'Unknown find listing for {k}')
			return
		self.trace(f'Removed find "{k}" ({len(f[1])} matches to stop)')
		
		for k in f[1]:
			a = self.matched.get(k, None)
			if a:
				self.send(ar.Stop(), a)

	def top_of_directory(self):
		listing = [v[0] for k, v in self.directory.items() if v[0].declared_scope > self.scope]
		find = [v[0] for k, v in self.find.items() if v[0].declared_scope > self.scope]
		return PushedDirectory(listing, find)

	# self.directory[service_name] = [FindService, set()]
	# self.find[search_key] = [FindService, set()]
	#
	# All the finds that matched to a service.
	# for k in self.find[search_key][1]:
	#	a = self.match[k]
	#	self.send(Stop(), a)

	# All the services matched to a find.
	# for k in self.find[search_key][1]:
	#	a = self.match[k]
	#	self.send(Stop(), a)

	def lost_below(self, lost):
		# All those ServiceRoutes that are compromised by a missing
		# publisher or subscriber.
		broken = set()

		# Keys of those find/directory entries that can no longer
		# be reached due to loss of accepted.
		removing = set()
		for k, f in self.find.items():
			if overlapping_route(lost, f[0].agent_address):
				broken.update(f[1])
				removing.add(k)

		t = ','.join([r for r in removing])
		self.trace(f'Removing {len(removing)} finds ({t})')
		for k in removing:
			self.find.pop(k, None)

		removing.clear()
		for k, d in self.directory.items():
			if overlapping_route(lost, d[0].agent_address):
				broken.update(d[1])
				removing.add(k)
				
		t = ','.join([r for r in removing])
		self.trace(f'Removing {len(removing)} listings ({t})')
		for k in removing:
			self.directory.pop(k, None)

		t = ','.join([k for k in broken])
		self.trace(f'Stopping {len(broken)} routes ({t})')
		for k in broken:
			try:
				a = self.matched[k]
			except KeyError:
				continue
			self.send(ar.Stop(), a)

		if self.connected_up:
			self.send(TrimRoutes(lost), self.connected_up)

	def lost_above(self):
		self.connected_up = None
		lost = CapRoutes(self.scope)

		self.send(lost, self.address)

def settings_property_default(a, p, d):
	# Ugly but without this type-specific handling this
	# "generic" function wouldnt work for HostPorts.
	if isinstance(a, DirectoryAccess):
		empty = a.access_ipp.host is None
	elif isinstance(a, HostPort):
		empty = a.host is None
	else:
		empty = a is None

	if empty:
		# Plucking a value out of the Homebase object that
		# may not be there, e.g. running as a tool.
		if p is None or p[2] is None:
			return d
		return p[2]
	return a

def ServiceDirectory_INITIAL_Start(self, message):
	self.started = ar.world_now()

	self.trace(f'Scope of {ScopeOfService.to_name(self.scope)}')
	self.trace(f'Connecting up to "{ar.tof(self.connect_above)}"')
	self.trace(f'Listening below at "{ar.tof(self.accept_below)}"')

	# The upward connection to next higher directory.
	if isinstance(self.connect_above, HostPort):
		# A disabled up-link is denoted by a HostPort with with
		# a null host.
		if self.connect_above.host:
			a = self.create(ConnectService, self.connect_above, CONNECT_ABOVE)
			self.assign(a, CONNECT_ABOVE)
	elif isinstance(self.connect_above, InstantAccess):
		if self.connect_above.access_ipp.host:
			a = self.create(ConnectService, self.connect_above.access_ipp, CONNECT_ABOVE)
			self.assign(a, CONNECT_ABOVE)
	elif isinstance(self.connect_above, DirectoryAccess):
		if self.connect_above.access_ipp.host:
			a = self.create(ConnectDirectory, self.connect_above, CONNECT_ABOVE)
			self.assign(a, CONNECT_ABOVE)
	else:
		pass	# Connection arranged externally. May be a
				# Connected object for diagnostic purposes.

	# Acceptance of connections from lower directories.
	if isinstance(self.accept_below, HostPort):
		if self.accept_below.host is None:
			self.send(HostPort(host=None), self.parent_address)
		else:
			listen(self, self.accept_below, tag='directory-accept')
			return OPENING
	else:
		pass	# Acceptance arranged externally. May be a
				# Listening object for diagnosis.

	return NORMAL

def ServiceDirectory_OPENING_Listening(self, message):
	self.send(message.listening_ipp, self.parent_address)
	self.listening = message
	return NORMAL

def ServiceDirectory_OPENING_NotListening(self, message):
	f = ar.Failed(directory_listen=(message.error_text, 'directory cannot accept sub-directories'))
	self.complete(f)

def ServiceDirectory_OPENING_Stop(self, message):
	self.stopped = self.return_address
	self.send(ar.Ack(), self.stopped)
	self.complete(ar.Aborted())

def ServiceDirectory_OPENING_Accepted(self, message):
	# Using tail as the key ensures it works for
	# any object at the end of this proxy.
	self.accepted[self.return_address] = message
	return NORMAL

def ServiceDirectory_OPENING_Abandoned(self, message):
	# Using tail as the key ensures it works for
	# any object at the end of this proxy.
	m = self.accepted.pop(self.return_address, None)
	if m is None:
		self.warning(f'Abandoned by unknown client')
	return NORMAL

def ServiceDirectory_NORMAL_ServiceUp(self, message):
	ca = self.connect_above
	if isinstance(ca, InstantAccess):
		lookup = InstantLookup(ca.product_name, ca.product_instance)
		self.reply(lookup)
		return NORMAL

	if self.connected_up is None:
		c = self.top_of_directory()
		if not c.empty():
			self.reply(c)
		self.connected_up = self.return_address
		self.not_connected = None
		self.connected = ar.world_now()
	else:
		self.warning(f'Connected when already connected')
	return NORMAL

def ServiceDirectory_NORMAL_YourInstant(self, message):
	if self.connected_up is None:
		c = self.top_of_directory()
		if not c.empty():
			self.send(c, message.address)
		self.connected_up = message.address
		self.not_connected = None
		self.connected = ar.world_now()
	else:
		self.warning(f'Connected when already connected')
	return NORMAL

def ServiceDirectory_NORMAL_ServiceNotUp(self, message):
	self.not_connected = message.not_connected
	self.connected = None
	self.warning(f'Cannot connect ({message.not_connected.error_text})')
	return NORMAL

def ServiceDirectory_NORMAL_ServiceDown(self, message):
	if self.connected_up is not None:
		# Abnormal sockets failure. Connection to upper
		# levels should terminate with an Abandoned message.
		# This is a sockets fault on established transport.
		self.lost_above()
	return NORMAL

def ServiceDirectory_NORMAL_Abandoned(self, message):
	# Close/abandon of upward connection now handled
	# by the ConnectService object and mapped to ServiceDown

	self.lost_below(self.return_address)
	self.accepted.pop(self.return_address[-1], None)
	return NORMAL

def ServiceDirectory_NORMAL_Closed(self, message):
	return ServiceDirectory_NORMAL_Abandoned(self, message)

def ServiceDirectory_NORMAL_Listening(self, message):
	if self.listening is not None:
		self.warning('Listening and already doing so')
	self.listening = message
	return NORMAL

def ServiceDirectory_NORMAL_NotListening(self, message):
	if self.listening is None:
		self.warning('Not listening and already not doing so')
	self.listening = None
	# Done in the separate machine.
	#self.start(ar.T2, 10.0)
	return NORMAL

def ServiceDirectory_NORMAL_T2(self, message):
	# TBC - should be a repeat of INITIAL_Start handling
	# or nothing at all, i.e. handled by separate machine.
	if isinstance(self.accept_below, ar.HostPort) and self.accept_below.host:
		listen(self, self.accept_below)
	return NORMAL

def ServiceDirectory_NORMAL_Accepted(self, message):
	# Using tail as the key ensures it works for
	# any object at the end of this proxy.
	self.accepted[self.return_address] = message
	return NORMAL

def ServiceDirectory_NORMAL_Abandoned(self, message):
	# Using tail as the key ensures it works for
	# any object at the end of this proxy.
	m = self.accepted.pop(self.return_address, None)
	if m is None:
		self.warning(f'Abandoned by unknown sub-directory')
	return NORMAL

def ServiceDirectory_NORMAL_PushedDirectory(self, message):
	nl = len(message.listing)
	nf = len(message.find)

	self.trace(f'Pushed "{nl}" listings and "{nf}" finds')

	for s in message.listing:
		# Suppress those listings at lower levels.
		if s.declared_scope < self.scope:
			continue
		# Patch the connecting ipp for those scenarios involving
		# a secondary connection, i.e. a peer.
		if self.scope in (ScopeOfService.GROUP, ScopeOfService.HOST, ScopeOfService.LAN):
			self.conclude_host(self.return_address, s)

		self.add_listing(s)

	for f in message.find:
		# Suppress those listings at lower levels.
		if f.declared_scope < self.scope:
			continue
		self.add_find(f)

	if self.connected_up:
		self.send(message, self.connected_up)
	return NORMAL

### PS-pub-9 Directory accepts listing.
def ServiceDirectory_NORMAL_ServiceListing(self, message):
	# Suppress those listings at lower levels.
	if message.declared_scope < self.scope:
		return NORMAL
	if self.scope in (ScopeOfService.GROUP, ScopeOfService.HOST, ScopeOfService.LAN):
		### PS-pub-9 Directory patches listing IP-port.
		self.conclude_host(self.return_address, message)
	self.add_listing(message)

	### PS-pub-9 Directory propagates listing.
	if self.connected_up and message.declared_scope > self.scope:
		self.send(message, self.connected_up)
	return NORMAL

### PS-sub-8 Directory accepts find.
def ServiceDirectory_NORMAL_FindService(self, message):
	# Suppress those listings at lower levels.
	if message.declared_scope < self.scope:
		return NORMAL
	self.add_find(message)

	### PS-sub-8 Directory propagates find.
	if self.connected_up and message.declared_scope > self.scope:
		self.send(message, self.connected_up)
	return NORMAL

def ServiceDirectory_NORMAL_UnlistService(self, message):
	# Suppress those listings at lower levels.
	if message.declared_scope < self.scope:
		return NORMAL
	self.remove_listing(message)
	if self.connected_up and message.declared_scope > self.scope:
		self.send(message, self.connected_up)
	return NORMAL

def ServiceDirectory_NORMAL_UnlistFind(self, message):
	# Suppress those listings at lower levels.
	if message.declared_scope < self.scope:
		return NORMAL
	self.remove_find(message)
	if self.connected_up and message.declared_scope > self.scope:
		self.send(message, self.connected_up)
	return NORMAL

# COMPLETE OUTPUT
# SCOPE | ADDRESS (METHOD) | STARTED (SPAN) | CONNECTED (SPAN) | PUB-SUB (listings, searches, connections)
# WAN some.dns.name:32175 (ansar org, super-duper) - 2024-03-01T10:22:17 (32d) - (17/3/43)
# LAN 192.168.1.176:32175 (super-duper/demo/mr-ansar) - 2024-03-01T10:22:17 (32d) -  (4/2/16)
# HOST 127.0.0.1:32175 (static IP-port) - 2024-03-01T10:22:17 (32d) - (0/2/4)
# GROUP 127.0.0.1:43301 (ephemeral IP-port) - 2024-03-01T10:22:17 (32d) - (0/2/2)

# OR ...
# NOT CONNECTED some.dns.name:32175 - unreachable/connection refused
# LAN 192.168.1.176:32175 - product/instance/user (listings, searches, connections)
# ..
def scope_connection(self, s, c):
	if isinstance(c, HostPort):
		if c.host:
			if self.not_connected:
				method = self.not_connected.error_text
			else:
				method = 'standard host, port'
		else:
			method = 'disabled'
		s.connecting_ipp = c
		s.method = method
	elif isinstance(c, InstantAccess):
		m = f'{c.product_name}/{c.product_instance}'
		s.connecting_ipp = c.access_ipp
		s.method = m
	elif isinstance(c, DirectoryAccess):
		m = f'{c.account_id}/{c.directory_id}'
		s.connecting_ipp = c.access_ipp
		s.method = m

def ServiceDirectory_NORMAL_DirectoryEnquiry(self, message):
	# Here/this level of directory info.
	h = message.lineage[-1]

	listings = len(self.directory)
	finds = len(self.find)
	accepts = len(self.accepted)

	h.scope = self.scope
	h.started = self.started
	h.lfa = [listings, finds, accepts]

	if message.scope > self.scope and self.scope != ScopeOfService.WAN:
		# Above/next level of directory info.
		a = DirectoryScope(scope=None)
		scope_connection(self, a, self.connect_above)
		message.lineage.append(a)
		if self.connected_up:
			a.connected = self.connected
			self.forward(message, self.connected_up, self.return_address)
			return NORMAL

	self.reply(DirectoryAncestry(lineage=message.lineage))
	return NORMAL

def ServiceDirectory_NORMAL_DirectoryReconnect(self, message):
	if message.scope < self.scope:
		a = ScopeOfService.to_name(message.scope)
		b = ScopeOfService.to_name(self.scope)
		f = ar.Failed(low_scope=('reconnect for "{a}" received by directory at "{b}"', 'internal error'))
		self.reply(f)
		return NORMAL
	elif message.scope > self.scope:
		if not self.connected_up:
			a = ScopeOfService.to_name(message.scope)
			f = ar.Failed(broken_connection=('cannot reach directory at "{a}"', None))
			self.reply(f)
			return NORMAL
		self.forward(message, self.connected_up, self.return_address)
		return NORMAL

	self.forward(message, self.parent_address, self.return_address)
	return NORMAL

def ServiceDirectory_NORMAL_Completed(self, message):
	key = self.debrief()
	self.matched.pop(key, None)
	return NORMAL

def ServiceDirectory_NORMAL_Stop(self, message):
	self.stopped = self.return_address
	self.abort()
	if self.working():
		return CLEARING
	self.send(ar.Ack(), self.stopped)
	self.complete(ar.Aborted())

def ServiceDirectory_NORMAL_CapRoutes(self, message):
	self.forward(message, pb.house, self.return_address)

	self.trace(f'Broadcasting cap to {len(self.accepted)} sub-directories')
	for a in self.accepted.values():
		self.send(message, a.remote_address)
	return NORMAL

def ServiceDirectory_NORMAL_TrimRoutes(self, message):
	self.lost_below(message.address)
	return NORMAL

def ServiceDirectory_CLEARING_Completed(self, message):
	self.debrief()
	if self.working():
		return CLEARING
	self.send(ar.Ack(), self.stopped)
	self.complete(ar.Aborted())

SERVICE_DIRECTORY_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	OPENING: (
		(Listening, NotListening, Accepted, Abandoned, ar.Stop,), (ServiceUp, ServiceNotUp, ServiceDown)
	),
	NORMAL: (
		(ServiceUp, ServiceNotUp, ServiceDown, Closed, Abandoned,
		YourInstant,
		Listening, NotListening, Accepted, ar.T2,
		ar.Completed,
		PushedDirectory,
		ServiceListing, FindService,
		UnlistService, UnlistFind,
		CapRoutes, TrimRoutes,
		DirectoryEnquiry, DirectoryReconnect,
		ar.Stop), ()
	),
	CLEARING: (
		(ar.Completed), ()
	),
}

ar.bind(ServiceDirectory, SERVICE_DIRECTORY_DISPATCH)

# The preliminary exchange to trade end-point addresses
#
class OpenLoop(object):
	def __init__(self, subscriber_session=None, key=None):
		self.subscriber_session = subscriber_session
		self.key = key

class LoopOpened(object):
	def __init__(self, publisher_session=None, key=None):
		self.publisher_session = publisher_session
		self.key = key

class CloseLoop(object): pass

INTRODUCTION_SCHEMA = {
	'subscriber_session': ar.Address(),
	'publisher_session': ar.Address(),
	'key': str,
}

ar.bind(OpenLoop, object_schema=INTRODUCTION_SCHEMA)
ar.bind(LoopOpened, object_schema=INTRODUCTION_SCHEMA)
ar.bind(CloseLoop, object_schema=INTRODUCTION_SCHEMA)

#
#
class PublisherLoop(ar.Point, ar.StateMachine):
	def __init__(self, route, remote_session, remote_loop, publisher_address, create_session, relay_address):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.route = route
		self.key = route.key
		self.remote_session = remote_session
		self.remote_loop = remote_loop
		self.publisher_address = publisher_address
		self.create_session = create_session
		self.relay_address = relay_address

		self.session_address = None
		self.origin_address = None
		self.created_session = None
		self.closing = False
		self.value = None

	def close_route(self):
		# Just received or sent CloseLoop.
		if isinstance(self.route, InboundByRelay):
			self.send(CloseRelay(self.route.redirect), self.relay_address[self.route.key])

def PublisherLoop_INITIAL_Start(self, message):
	### PS-pub-7 Loop arranges session.
	cs = self.create_session
	if cs:
		# Create the ending function that swaps the Completed message to the parent for a
		# Clear message to the proxy.
		self.created_session = self.create(cs.object_type, *cs.args,
			controller_address=self.publisher_address, remote_address=self.remote_session,
			**cs.kw)
		self.session_address = self.created_session
		self.origin_address = self.created_session
	else:
		self.session_address = self.publisher_address
		self.origin_address = self.remote_session

	self.send(LoopOpened(self.session_address, self.key), self.remote_loop)
	self.forward(Delivered(self.key, self.address), self.publisher_address, self.origin_address)
	return LOOPED

# Methods of termination;
### PS-pub-8 Loop terminates by session completion.
def PublisherLoop_LOOPED_Completed(self, message):
	if self.created_session and self.return_address == self.created_session:
		self.forward(Cleared(message.value), self.publisher_address, self.origin_address)
		self.send(CloseLoop(), self.remote_loop)
		self.close_route()
		self.complete(ar.Aborted())
	self.warning('Unexpected termination')
	return LOOPED

### PS-pub-8 Loop terminates by local clear().
def PublisherLoop_LOOPED_Close(self, message):
	self.closing, self.value = True, message.value
	self.send(CloseLoop(), self.remote_loop)
	if self.created_session:
		self.send(ar.Stop(), self.created_session)
		return CLEARING
	self.close_route()

	self.forward(Cleared(message.value), self.publisher_address, self.origin_address)
	self.complete(ar.Aborted())

### PS-pub-8 Loop terminates by remote close.
def PublisherLoop_LOOPED_CloseLoop(self, message):
	if self.created_session:
		self.send(ar.Stop(), self.created_session)
		return CLEARING
	self.close_route()

	self.forward(Dropped(), self.publisher_address, self.origin_address)
	self.complete(ar.Aborted())

### PS-pub-8 Loop terminates by local exit.
def PublisherLoop_LOOPED_Stop(self, message):
	self.send(CloseLoop(), self.remote_loop)
	if self.created_session:
		self.send(message, self.created_session)
		return CLEARING
	self.close_route()

	self.forward(Dropped(), self.publisher_address, self.origin_address)
	self.complete(ar.Aborted())

def PublisherLoop_CLEARING_Completed(self, message):
	if self.created_session is None or self.return_address != self.created_session:
		return CLEARING
	self.create_session = None
	self.close_route()

	if self.closing:
		self.forward(Cleared(self.value), self.publisher_address, self.origin_address)
	else:
		self.forward(Dropped(), self.publisher_address, self.origin_address)
	self.complete(ar.Aborted())

PUBLISHER_LOOP_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	LOOPED: (
		(ar.Completed, Close, CloseLoop, ar.Stop,), ()
	),
	CLEARING: (
		(ar.Completed,), ()
	),
}

ar.bind(PublisherLoop, PUBLISHER_LOOP_DISPATCH, thread='published')

# An object to maintain a listen on behalf of a published
# name. Enters name and listen into the service directory.
class PublishingAgent(ar.Point, ar.StateMachine):
	def __init__(self, requested_name, publisher_address, create_session, declared_scope):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.requested_name = requested_name
		self.publisher_address = publisher_address
		self.create_session = create_session
		self.declared_scope = declared_scope
		self.listening = None
		self.matching = {}
		self.loop = {}
		self.relay = {}
		self.peered = {}
		self.relay_address = {}

def PublishingAgent_INITIAL_Start(self, message):
	if self.declared_scope == ScopeOfService.PROCESS:
		### PS-pub-3 Agent sends listing to directory.
		self.send(ServiceListing(self.requested_name, self.address, self.declared_scope), pb.directory)
		self.send(Published(self.requested_name, self.declared_scope), self.publisher_address)
		return READY
	elif self.declared_scope in (ScopeOfService.GROUP, ScopeOfService.HOST):
		### PS-pub-3 Agent arranges for inbound listen.
		pb.channel.send(ListenForStream(LocalPort(0)), self.address)
		return PENDING
	elif self.declared_scope in (ScopeOfService.LAN, ScopeOfService.WAN):
		pb.channel.send(ListenForStream(HostPort('0.0.0.0', 0)), self.address)
		return PENDING
	return READY

def PublishingAgent_PENDING_Listening(self, message):
	self.listening = message
	self.send(ServiceListing(self.requested_name, self.address, self.declared_scope, message.listening_ipp), pb.directory)
	self.send(Published(self.requested_name, self.declared_scope, message.listening_ipp), self.publisher_address)
	return READY

def PublishingAgent_PENDING_NotListening(self, message):
	r = message.requested_ipp
	t = message.error_text
	self.warning(f'Cannot allocate a listen for {r.host}:{r.port} ({t})')
	self.start(ar.T1, 60.0)
	return GLARING

def PublishingAgent_PENDING_Stop(self, message):
	self.send(UnlistService(self.requested_name, self.address, self.declared_scope), pb.directory)
	self.complete(ar.Aborted())

def PublishingAgent_GLARING_T1(self, message):
	if self.declared_scope in (ScopeOfService.GROUP, ScopeOfService.HOST):
		pb.channel.send(ListenForStream(LocalPort(0)), self.address)
		return PENDING
	elif self.declared_scope in (ScopeOfService.LAN, ScopeOfService.WAN):
		pb.channel.send(ListenForStream(HostPort('0.0.0.0', 0)), self.address)
		return PENDING
	return READY

def PublishingAgent_GLARING_Stop(self, message):
	self.send(UnlistService(self.requested_name, self.address, self.declared_scope), pb.directory)
	self.complete(ar.Aborted())

def looped(self, inbound, open, return_address):
	if inbound is None or open is None or return_address is None:
		return
	key = open.key
	### PS-pub-6 Agent creates local loop.
	a = self.create(PublisherLoop, inbound, open.subscriber_session, return_address,
		self.publisher_address, self.create_session,
		self.relay_address)
	self.assign(a, key)
	self.loop[key] = a

### PS-pub-4 Agent accepts internal route.
def PublishingAgent_READY_InboundFromAddress(self, message):
	key = message.key

	try:
		m = self.matching[key]
	except KeyError:
		m = [message, None, None]
		self.matching[key] = m
		self.trace(f'Added direct route [{ScopeOfService.to_name(message.scope)}]({key})')
		return READY
	looped(self, message, m[1], m[2])
	return READY

### PS-pub-4 Agent accepts peer route.

def PublishingAgent_READY_InboundOverAccepted(self, message):
	key = message.key

	try:
		m = self.matching[key]
	except KeyError:
		m = [message, None, None]
		self.matching[key] = m
		self.trace(f'Added peer route [{ScopeOfService.to_name(message.scope)}]({key})')
		return READY
	looped(self, message, m[1], m[2])
	return READY

def PublishingAgent_READY_InboundByRelay(self, message):
	key = message.key
	try:
		relay = self.relay[key]
		self.warning(f'Duplicate relay "{key}" (ignored)')
		return READY
	except KeyError:
		relay = message
		self.relay[key] = relay

	ipp = relay.redirect.redirect_ipp
	k = ipp_key(ipp)

	try:
		r = self.peered[k]
		r[1][key] = relay
		n = len(r[1])
		self.trace(f'Peer for relay "{key}" already known ({n} routes pending)')
	except KeyError:
		r = [None, {key: relay}]
		self.peered[k] = r

		self.trace(f'Opening peer "{k}" (relay {key})')
		self.send(OpenPeer(ipp, key), pb.house)
		return READY

	if r[0] is None:
		return READY

	self.send(relay, r[0])
	self.relay_address[key] = r[0]

	# Assume the same state as for other route types, i.e.
	# ready for the OpenLoop that is sure to follow.
	try:
		m = self.matching[key]
	except KeyError:
		m = [relay, None, None]
		self.matching[key] = m
		self.trace(f'Added relay peer [{ScopeOfService.to_name(relay.scope)}]({key})')
		return READY
	looped(self, message, m[1], m[2])
	return READY
	

def PublishingAgent_READY_PeerOpened(self, message):
	k = ipp_key(message.connecting_ipp)
	try:
		r = self.peered[k]
	except KeyError:
		self.warning(f'Unknown peer opened"{k}"')
		return READY
	r[0] = self.return_address

	for key, relay in r[1].items():
		self.reply(relay)
		self.relay_address[key] = self.return_address

		# Assume the same state as for other route types, i.e.
		# ready for the OpenLoop that is sure to follow.
		try:
			m = self.matching[key]
		except KeyError:
			m = [relay, None, None]
			self.matching[key] = m
			self.trace(f'Added relay peer [{ScopeOfService.to_name(relay.scope)}]({key})')
			continue
		looped(self, message, m[1], m[2])
	return READY

def PublishingAgent_READY_RetractRoute(self, message):
	key = message.key

	m = self.matching.pop(key, None)
	if m is None:
		self.trace(f'Unknown key "{key}"')
		return READY

	if m[0] is None:
		self.trace(f'Known key "{key}" never routed')
		return READY

	self.trace(f'Retracted route [{ScopeOfService.to_name(m[0].scope)}]({key})')
	return READY

### PS-pub-5 Agent accepts remote loop.
def PublishingAgent_READY_OpenLoop(self, message):
	key = message.key
	try:
		m = self.matching[key]
	except KeyError:
		m = [None, message, self.return_address]
		self.matching[key] = m
		return READY
	looped(self, m[0], message, self.return_address)
	return READY

def PublishingAgent_READY_CapRoutes(self, message):
	self.trace(f'Scope cap {message.service_scope}, {len(self.matching)} routes to consider')

	removing = set()
	for k, m in self.matching.items():
		if message.service_scope < m[0].scope:
			removing.add(k)

	self.trace(f'Removing {len(removing)} routes')
	for k in removing:
		m = self.matching.pop(k, None)
		if m is None:
			continue
		m0 = m[0]
		if m0 is None:
			continue
		self.trace(f'Capped route [{ScopeOfService.to_name(m0.scope)}]({k})')
	return READY

def PublishingAgent_READY_Clear(self, message):
	if message.session is None:
		for a in self.loop.values():
			self.send(Close(message.value), a)
		return READY

	key = message.session.key
	try:
		a = self.loop[key]
	except KeyError:
		return READY
	self.send(Close(message.value), a)

	return READY

def PublishingAgent_READY_Completed(self, message):
	key = self.debrief()
	self.loop.pop(key, None)
	return READY

def PublishingAgent_READY_Stop(self, message):
	if self.working():
		self.abort()
		return CLEARING
	self.send(UnlistService(self.requested_name, self.address, self.declared_scope), pb.directory)
	self.complete(ar.Aborted())

def PublishingAgent_CLEARING_Completed(self, message):
	key = self.debrief()
	self.loop.pop(key, None)
	if self.working():
		return CLEARING
	self.send(UnlistService(self.requested_name, self.address, self.declared_scope), pb.directory)
	self.complete(ar.Aborted())

PUBLISHING_AGENT_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	PENDING: (
		(Listening, NotListening, ar.Stop), ()
	),
	GLARING: (
		(ar.T1, ar.Stop), ()
	),
	READY: (
		(InboundFromAddress, InboundOverAccepted, InboundByRelay, PeerOpened,
		RetractRoute, CapRoutes,
		OpenLoop, Clear, ar.Completed, ar.Stop), ()
	),
	CLEARING: (
		(ar.Completed,), ()
	),
}

ar.bind(PublishingAgent, PUBLISHING_AGENT_DISPATCH, thread='published')

class ShorterRoute(object): pass

ar.bind(ShorterRoute)

# States of the machine.
#
class EMPTY: pass			# No routes available.
class PEERING: pass			# Acquiring a peer-to-peer tansport
class RETRY: pass			# Acquiring a peer-to-peer tansport
class LOOPING: pass			# Acquiring a session
class HOLDING: pass			# Short pause before jumping to better route.

# T1, T2 and T3
SECONDS_OF_GLARING = 10.0
SECONDS_OF_LOOPING = 5.0
SECONDS_OF_HOLDING = 30.0

# Pick out the best route in the
# given table.
def best_route(table):
	scope, route = None, None
	for s, r in table.items():
		if scope is None or s < scope:
			scope, route = s, r
	return scope, route

def find_route(table, key):
	for s, r in table.items():
		if r.key == key:
			return s
	return None

class SubscriberLoop(ar.Point, ar.StateMachine):
	def __init__(self, routing_table, subscriber_address, create_session):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.routing_table = routing_table
		self.subscriber_address = subscriber_address
		self.create_session = create_session

		# Context of a routing attempt
		self.opened_route = None
		self.opened_retry = None
		self.relay_address = None

		# Context of a looped route
		self.latch = None
		self.remote_session = None
		self.session_address = None
		self.origin_address = None

	def open_loop(self, key, remote_agent):
		# WARNING - ADDRESS OF LATCH CHANGES
		t = address_to_text(remote_agent)
		self.trace(f'Initiate latch/loop to [{t}] ({key})')
		a = self.create(ar.Latch, key, self.subscriber_address)
		self.assign(a, 0)
		self.latch = a
		self.send(OpenLoop(a, key), remote_agent)
		self.start(ar.T2, SECONDS_OF_LOOPING)
		return LOOPING

	def open_peer(self, key, ipp, retry=False):
		self.trace(f'Requests peer {ipp.host}:{ipp.port} ({key})')
		self.send(OpenPeer(ipp, key), pb.house)
		if retry:
			return RETRY
		# About to potentially ask a socket to connect.
		# Remember what to do if it fails and there needs
		# to be an appropriate pause before the next move.
		s = local_private_public(ipp.host)
		r = ip_retry(s)
		self.trace(f'Selected "{ScopeOfIP.to_name(s)}" for retry timeouts')
		self.opened_retry = iter(ar.smart_intervals(r))
		return PEERING

	def open_relay(self, key, redirect, retry=False):
		ipp = redirect.redirect_ipp
		self.trace(f'Requests relay {ipp.host}:{ipp.port} ({key})')
		self.send(OpenPeer(ipp, key), pb.house)
		if retry:
			return RETRY
		# About to potentially ask a socket to connect.
		# Remember what to do if it fails and there needs
		# to be an appropriate pause before the next move.
		s = local_private_public(ipp.host)
		r = ip_retry(s)
		self.trace(f'Selected "{ScopeOfIP.to_name(s)}" for retry timeouts')
		self.opened_retry = iter(ar.smart_intervals(r))
		return RELAYING

	### PS-sub-6 Loop initiates route.
	def open_route(self, route):
		self.trace(f'Initiate route [{ScopeOfService.to_name(route.scope)}]({route.key})')

		retry = id(route) == id(self.opened_route)
		if isinstance(route, RouteToAddress):
			self.opened_route = route
			return self.open_loop(route.key, route.address)
		elif isinstance(route, RouteOverConnected):
			self.opened_route = route
			return self.open_peer(route.key, route.connecting_ipp, retry)
		elif isinstance(route, RouteByRelay):
			self.opened_route = route
			return self.open_relay(route.key, route.redirect, retry)
		else:
			self.warning(f'Unknown route type')
			return self.current_state

	def glare(self):
		def timeout():
			if self.opened_retry is None:
				return SECONDS_OF_GLARING
			try:
				t = next(self.opened_retry)
			except StopIteration:
				return SECONDS_OF_GLARING
			return t
		t = timeout()
		self.trace(f'Calculated glare of "{t}" seconds')
		self.start(ar.T1, t)
		return GLARING

### PS-sub-5 Loop starts.
def SubscriberLoop_INITIAL_Start(self, message):
	scope, route = best_route(self.routing_table)
	if scope is None:
		return EMPTY
	return self.open_route(route)

def SubscriberLoop_EMPTY_ShorterRoute(self, message):
	scope, route = best_route(self.routing_table)
	if scope is None:
		return EMPTY
	return self.open_route(route)

def SubscriberLoop_EMPTY_Stop(self, message):
	self.complete(ar.Aborted())

# PEERING.
def SubscriberLoop_PEERING_PeerOpened(self, message):
	if message.key != self.opened_route.key:
		return PEERING
	return self.open_loop(message.key, self.return_address)

def SubscriberLoop_PEERING_NotPeered(self, message):
	if message.key != self.opened_route.key:
		return PEERING
	name = key_service(message.key)
	self.trace(f'Cannot peer to {name} ({message.reason})')
	self.forward(NotAvailable(message.key, message.reason, self.parent_address), self.subscriber_address, self.address)
	return self.glare()

# RELAYING.
def SubscriberLoop_RELAYING_PeerOpened(self, message):
	if message.key != self.opened_route.key:
		return RELAYING
	self.reply(self.opened_route)
	self.relay_address = self.return_address
	return self.open_loop(message.key, self.return_address)

def SubscriberLoop_RELAYING_NotPeered(self, message):
	if message.key != self.opened_route.key:
		return RELAYING
	name = key_service(message.key)
	self.trace(f'Cannot relay to {name} ({message.reason})')
	self.forward(NotAvailable(message.key, message.reason, self.parent_address), self.subscriber_address, self.address)
	return self.glare()

# RETRY.
def SubscriberLoop_RETRY_PeerOpened(self, message):
	if message.key != self.opened_route.key:
		return RETRY
	return self.open_loop(message.key, self.return_address)

def SubscriberLoop_RETRY_NotPeered(self, message):
	if message.key != self.opened_route.key:
		return RETRY
	name = key_service(message.key)
	# No session control message on a retry.
	self.trace(f'Cannot peer to {name} ({message.reason})')
	return self.glare()

# LOOPING.
def SubscriberLoop_LOOPING_LoopOpened(self, message):
	if message.key != self.opened_route.key:
		return LOOPING
	self.remote_loop = self.return_address
	self.remote_session = message.publisher_session
	if self.create_session:
		cs = self.create_session
		session = self.create(cs.object_type, *cs.args,
			controller_address=self.subscriber_address, remote_address=self.remote_session,
			**cs.kw)
		self.assign(session, 1)			# 0 (zero) is the latch
		self.session_address = session
		self.origin_address = session
		# ABDICATE slot to session
		# self.alias = self.abdicate_to(session)
		# Latch clears additional session alias on stop
		hand = ar.SwitchOver(session)
	else:
		self.session_address = self.subscriber_address
		self.origin_address = self.remote_session
		# ABDICATE slot to controller
		# Latch clears additional session alias on stop
		hand = ar.SwitchOver()
	# Sending session control message from Latch is flawed - doesnt know
	# about "origin_address".
	s = address_to_text(self.subscriber_address)
	p = address_to_text(self.origin_address)
	self.trace(f'Loop opened between subscriber [{s}] and publisher [{p}]')
	self.forward(Available(message.key, self.parent_address), self.subscriber_address, self.origin_address)
	self.send(hand, self.latch)
	# LATCH MUST CONTINUE FOR THOSE MESSAGES THAT WERE
	# SITTING IN THE QUEUE AFTER THE HANDOVER MESSAGE
	return LATCHING

def SubscriberLoop_LOOPING_T2(self, message):
	# Nobody to update. Cant send CloseLoop - dont know the remote loop.
	# Could clear peer and send a different message to the agent.
	# Dont know if its a retry here... dang.
	# self.forward(NotAvailable(message.key, 'Subscriber loop took too long', self.parent_address), self.subscriber_address, self.address)
	return self.glare()

def SubscriberLoop_LATCHING_Ack(self, message):
	try:
		# Latch has relocated.
		# Remove the old entry.
		del self.address_job[self.latch]
	except KeyError:
		self.warning(f'Where is the latch entry?')
	self.assign(self.return_address, 0)
	return LOOPED

### PS-sub-7 Loop terminates by session object.
def SubscriberLoop_LOOPED_Completed(self, message):
	d = self.debrief()
	if d == 1:
		self.forward(Cleared(message.value), self.subscriber_address, self.origin_address)
	else:
		r = f'Unexpected completion (debrief {d}, value {message.value})'
		self.warning(r)
		self.forward(Dropped(r), self.subscriber_address, self.origin_address)

	self.send(CloseLoop(), self.remote_loop)
	if self.working():
		self.abort()
		return CLEARING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	return self.glare()

### PS-sub-7 Loop terminates by local clear.
def SubscriberLoop_LOOPED_Close(self, message):
	self.forward(Cleared(message.value), self.subscriber_address, self.origin_address)

	self.send(CloseLoop(), self.remote_loop)
	if self.working():
		self.abort()
		return CLEARING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	return self.glare()

### PS-sub-7 Loop terminates by remote close.
def SubscriberLoop_LOOPED_CloseLoop(self, message):
	self.forward(Dropped('Remote abandon'), self.subscriber_address, self.origin_address)

	if self.working():
		self.abort()
		return CLEARING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	return self.glare()

### PS-sub-7 Loop terminates by loss of peer.
def SubscriberLoop_LOOPED_NotPeered(self, message):
	# Lost peer so CloseLoop a waste of time.
	name = key_service(message.key)
	r = f'Lost peer to {name} ({message.reason})'
	self.trace(r)
	self.forward(Dropped(r), self.subscriber_address, self.origin_address)

	if self.working():
		self.abort()
		return CLEARING

	# Sending CloseRelay also a waste of time.
	# Must be detected at the relay.

	return self.glare()

### PS-sub-7 Loop terminates by local exit.
def SubscriberLoop_LOOPED_Stop(self, message):
	self.forward(Dropped('Stop'), self.subscriber_address, self.origin_address)

	self.send(CloseLoop(), self.remote_loop)
	if self.working():
		self.abort()
		return COMPLETING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	self.complete(ar.Aborted())

### PS-sub-7 Loop considers termination by better route.
def SubscriberLoop_LOOPED_ShorterRoute(self, message):
	self.trace('Hold for better route')
	self.start(ar.T3, SECONDS_OF_HOLDING)
	return HOLDING

def SubscriberLoop_HOLDING_T3(self, message):
	scope, route = best_route(self.routing_table)

	# After that delay for any message flutter,
	# is there still a better route?
	closer = scope < self.opened_route.scope
	if not closer:
		self.trace('Route information no better than current')
		return LOOPED
	self.trace(f'Bouncing session to better route [{ScopeOfService.to_name(scope)}]({route.key})')

	self.forward(Dropped('Shorter route'), self.subscriber_address, self.origin_address)

	self.send(CloseLoop(), self.remote_loop)
	if self.working():
		self.abort()
		return ROUTING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	return self.open_route(route)

# Termination of session by session object.
def SubscriberLoop_HOLDING_Completed(self, message):
	return SubscriberLoop_LOOPED_Completed(self, message)

def SubscriberLoop_HOLDING_Close(self, message):
	return SubscriberLoop_LOOPED_Close(self, message)

# End of session by remote party.
def SubscriberLoop_HOLDING_CloseLoop(self, message):
	return SubscriberLoop_LOOPED_CloseLoop(self, message)

def SubscriberLoop_HOLDING_NotPeered(self, message):
	return SubscriberLoop_LOOPED_NotPeered(self, message)

def SubscriberLoop_HOLDING_Stop(self, message):
	return SubscriberLoop_LOOPED_Stop(self, message)

def SubscriberLoop_ROUTING_Completed(self, message):
	self.debrief()
	if self.working():
		return ROUTING

	# Committed now but still need to re-evaluate.
	# It is possible for the re-routing process to
	# end up on a worse route. This sounds counter-intuitive
	# but its also a better reflection of the state
	# of the directory. There is a reasonable chance
	# that the re-routing wouldve happened anyway.
	scope, route = best_route(self.routing_table)
	if scope is None:
		return EMPTY

	return self.open_route(route)

def SubscriberLoop_ROUTING_Close(self, message):
	return ROUTING		# Keep going.

def SubscriberLoop_ROUTING_Stop(self, message):
	return COMPLETING	# Switch to termination.

def SubscriberLoop_CLEARING_Completed(self, message):
	self.debrief()
	if self.working():
		return CLEARING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	return self.glare()

def SubscriberLoop_CLEARING_Close(self, message):
	return CLEARING		# Keep going.

def SubscriberLoop_CLEARING_Stop(self, message):
	return COMPLETING	# Switch to termination.

def SubscriberLoop_COMPLETING_Completed(self, message):
	d = self.debrief()
	if self.working():
		return COMPLETING

	if isinstance(self.opened_route, RouteByRelay):
		self.send(CloseRelay(self.opened_route.redirect), self.relay_address)

	self.complete(ar.Aborted())

def SubscriberLoop_GLARING_T1(self, message):
	scope, route = best_route(self.routing_table)
	if scope is None:
		return EMPTY
	return self.open_route(route)

def SubscriberLoop_GLARING_Close(self, message):
	self.complete(message.value)

def SubscriberLoop_GLARING_Stop(self, message):
	self.complete(ar.Aborted())

SUBSCRIBER_LOOP_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	EMPTY: (
		(ar.Stop, ShorterRoute), ()
	),
	PEERING: (
		(PeerOpened, NotPeered), (ShorterRoute, Close, ar.Stop)
	),
	RELAYING: (
		(PeerOpened, NotPeered), (ShorterRoute, Close, ar.Stop)
	),
	RETRY: (
		(PeerOpened, NotPeered), (ShorterRoute, Close, ar.Stop)
	),
	LOOPING: (
		(LoopOpened, ar.T2), (ar.Completed, NotPeered, ShorterRoute, Close, ar.Stop)
	),
	LATCHING: (
		(ar.Ack,), (CloseLoop, ar.Completed, NotPeered, ShorterRoute, Close, ar.Stop)
	),
	LOOPED: (
		(CloseLoop, ar.Completed, NotPeered, ShorterRoute, Close, ar.Stop), ()
	),
	HOLDING: (
		(ar.T3, CloseLoop, ar.Completed, NotPeered, Close, ar.Stop), ()
	),
	ROUTING: (
		(ar.Completed, Close, ar.Stop), ()
	),
	CLEARING: (
		(ar.Completed, Close, ar.Stop), ()
	),
	GLARING: (
		(ar.T1, Close, ar.Stop), ()
	),
	COMPLETING: (
		(ar.Completed,), ()
	),
}

# WARNING agent and loop MUST be on same thread.
ar.bind(SubscriberLoop, SUBSCRIBER_LOOP_DISPATCH, thread='subscribed')

# An object that represents a unique instance of a subscriber object
# and a requested search, i.e. each subscriber can have multiple
# active searches (as long as they are different) and each search can
# match multiple publishers.
class SubscriptionAgent(ar.Point, ar.StateMachine):
	def __init__(self, requested_search, subscriber_address, create_session, declared_scope):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.requested_search = requested_search
		self.subscriber_address = subscriber_address
		self.create_session = create_session
		self.declared_scope = declared_scope
		self.service_route = {}		# service_route[name][scope] = route
		self.route_loop = {}

# Register interest in services matching pattern.
def SubscriptionAgent_INITIAL_Start(self, message):
	### PS-sub-3 Agent sends find to directory.
	self.send(FindService(self.requested_search, self.address, self.declared_scope), pb.directory)
	return READY

# Routes arrive from directories. This is the first moment of discovering
# new matching service names. Instantiate per-match object as needed,
# that will initiate and manage actual session with remote.
### PS-sub-4 Agent accepts internal route.

def SubscriptionAgent_READY_RouteToAddress(self, message):
	key = message.key
	name = key_service(key)
	scope = ScopeOfService.PROCESS
	t = address_to_text(message.address)

	try:
		a = self.route_loop[name]
		routing_table = self.service_route[name]
	except KeyError:
		routing_table = {}
		routing_table[scope] = message
		self.service_route[name] = routing_table
		### PS-sub-4 Agent creates loop.
		a = self.create(SubscriberLoop, routing_table, self.subscriber_address, self.create_session)
		self.assign(a, name)
		self.route_loop[name] = a
		self.trace(f'Add service "{name}" and direct route [{ScopeOfService.to_name(scope)}]({t})')
		return READY

	self.trace(f'Add direct route [{ScopeOfService.to_name(scope)}]({t})')

	# Loop already exists. Load the additional routing info
	# and ping the loop if the new stuff is better.
	# NOT REALLY GOING TO BE BETTER THAN PROCESS BUT
	# COVERS SCENARIO WHERE TABLE IS EMPTY
	best_scope, _ = best_route(routing_table)
	routing_table[scope] = message
	if best_scope is None or scope < best_scope:
		self.trace('Subscription agent detects better route')
		self.send(ShorterRoute(), a)
	return READY

### PS-sub-4 Agent accepts peer route.

def SubscriptionAgent_READY_RouteOverConnected(self, message):
	key = message.key
	name = key_service(key)
	scope = message.scope
	ipp = message.connecting_ipp

	t = f'{ipp.host}:{ipp.port}'

	try:
		a = self.route_loop[name]
		routing_table = self.service_route[name]
	except KeyError:
		routing_table = {}
		routing_table[scope] = message
		self.service_route[name] = routing_table
		### PS-sub-4 Agent creates loop.
		a = self.create(SubscriberLoop, routing_table, self.subscriber_address, self.create_session)
		self.assign(a, name)
		self.route_loop[name] = a
		self.trace(f'Add service "{name}" and peer route [{ScopeOfService.to_name(scope)}]({t})')
		return READY

	self.trace(f'Add/update peer route [{ScopeOfService.to_name(scope)}]({t})')

	# Loop already exists. Load the additional routing info
	# and ping the loop if the new stuff is better.
	best_scope, _ = best_route(routing_table)
	routing_table[scope] = message
	if best_scope is None or scope < best_scope:
		self.trace('Subscription agent detects better route')
		self.send(ShorterRoute(), a)
	return READY

def SubscriptionAgent_READY_RouteByRelay(self, message):
	# NEED TO - connect to initiate the connection to the redirect
	# in the hope that the far end has also joined.
	key = message.key
	name = key_service(key)
	scope = message.scope
	ipp = message.redirect.redirect_ipp

	t = f'{ipp.host}:{ipp.port}'

	try:
		a = self.route_loop[name]
		routing_table = self.service_route[name]
	except KeyError:
		routing_table = {}
		routing_table[scope] = message
		self.service_route[name] = routing_table
		### PS-sub-4 Agent creates loop.
		a = self.create(SubscriberLoop, routing_table, self.subscriber_address, self.create_session)
		self.assign(a, name)
		self.route_loop[name] = a
		self.trace(f'Add service "{name}" and peer route [{ScopeOfService.to_name(scope)}]({t})')
		return READY

	self.trace(f'Add/update peer route [{ScopeOfService.to_name(scope)}]({t})')

	# Loop already exists. Load the additional routing info
	# and ping the loop if the new stuff is better.
	best_scope, _ = best_route(routing_table)
	routing_table[scope] = message
	if best_scope is None or scope < best_scope:
		self.trace('Subscription agent detects better route')
		self.send(ShorterRoute(), a)
	return READY

def SubscriptionAgent_READY_RetractRoute(self, message):
	key = message.key
	name = key_service(key)

	try:
		routing_table = self.service_route[name]
	except KeyError:
		self.trace(f'Unknown service {name}')
		return READY

	scope = find_route(routing_table, key)
	if scope:
		r = routing_table.pop(scope, None)
		if r is None:
			self.warning(f'Find/pop failed {key}')
			return READY
		if isinstance(r, RouteByRelay):
			ipp = r.redirect.redirect_ipp
			self.send(ClosePeer(ipp, key), pb.house)
		self.trace(f'Retracted route [{ScopeOfService.to_name(scope)}]({key})')
	else:
		self.trace(f'Unknown route {key}')
	return READY

def SubscriptionAgent_READY_CapRoutes(self, message):
	for routing_table in self.service_route.values():
		for s in range(message.service_scope + 1, ScopeOfService.WAN + 1):
			r = routing_table.pop(s, None)
			if r is None:
				continue
			if isinstance(r, RouteByRelay):
				ipp = r.redirect.redirect_ipp
				self.send(ClosePeer(ipp, r.key), pb.house)
			self.trace(f'Capped route [{ScopeOfService.to_name(s)}]({r.key})')
	return READY

def SubscriptionAgent_READY_Clear(self, message):
	if message.session is None:
		self.warning('No session included')
		return READY

	key = message.session.key
	name = key_service(key)
	try:
		a = self.route_loop[name]
	except KeyError:
		self.warning('Clear of unknown name {name}')
		return READY
	self.send(Close(message.value), a)
	return READY

def SubscriptionAgent_READY_Completed(self, message):
	name = self.debrief()
	self.service_route.pop(name, None)
	return READY

def SubscriptionAgent_READY_Stop(self, message):
	if self.working():
		self.abort()
		return COMPLETING
	self.send(UnlistFind(self.requested_search, self.address, self.declared_scope), pb.directory)
	self.complete(ar.Aborted())

def SubscriptionAgent_COMPLETING_Completed(self, message):
	name = self.debrief()
	r = self.service_route.pop(name, None)
	if r is None:
		self.warning('Unexpected completion of {name}')

	if self.working():
		return COMPLETING
	self.send(UnlistFind(self.requested_search, self.address, self.declared_scope), pb.directory)
	self.complete(ar.Aborted())

SUBSCRIPTION_AGENT_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	READY: (
		(RouteToAddress, RouteOverConnected, RouteByRelay, RetractRoute, CapRoutes,
		Clear,
		ar.Completed, ar.Stop), ()
	),
	COMPLETING: (
		(ar.Completed,), ()
	),
}

# WARNING agent and loop MUST be on same thread.
ar.bind(SubscriptionAgent, SUBSCRIPTION_AGENT_DISPATCH, thread='subscribed')

# Container of publish/subscibe objects. Need something
# to manage their existence and being separate keeps
# directory simpler.
class PubSub(ar.Threaded, ar.StateMachine):
	def __init__(self):
		ar.Threaded.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.published = {}
		self.subscribed = {}
		self.opened_peer = {}

def PubSub_INITIAL_Start(self, message):
	return NORMAL

### PS-pub-1 Process the app request
def PubSub_NORMAL_PublishAsName(self, message):
	try:
		a = self.published[message.requested_name]
		self.reply(NotPublished(message.requested_name, 'already published'))
		return NORMAL
	except KeyError:
		pass
	### PS-pub-2 Create the agent
	a = self.create(PublishingAgent, message.requested_name, self.return_address, message.create_session, message.declared_scope)
	p = [message, self.return_address]
	self.assign(a, p)
	self.published[message.requested_name] = a
	return NORMAL

### PS-sub-1 Process the app request
def PubSub_NORMAL_SubscribeToName(self, message):
	k = address_to_text(self.return_address)
	k += ':'
	k += message.requested_search
	try:
		a = self.subscribed[k]
	except KeyError:
		### PS-sub-2 Create the agent
		a = self.create(SubscriptionAgent, message.requested_search, self.return_address, message.create_session, message.declared_scope)
		s = [message, self.return_address]
		self.assign(a, s)
		self.subscribed[k] = a
	self.forward(Subscribed(message.requested_search, message.declared_scope), self.return_address, a)
	return NORMAL

def PubSub_NORMAL_Retract(self, message):
	self.trace(f'Retracting service/search at [{address_to_text(message.address)}]')
	for t, a in self.running():
		if t[1] == message.address:
			self.send(ar.Stop(), a)
	return NORMAL

def PubSub_NORMAL_Completed(self, message):
	ma = self.debrief()
	m, a = ma
	if isinstance(m, PublishAsName):
		p = self.published.pop(m.requested_name, None)
		if p is None:
			self.warning(f'Completion of unknown publication key {m.requested_name}')
	elif isinstance(m, SubscribeToName):
		search = m.requested_search
		k = address_to_text(a)
		k += ':'
		k += search
		s = self.subscribed.pop(k, None)
		if s is None:
			self.warning(f'Completion of unknown subscription key {k}')
	else:
		self.warning(f'Completion of unknown type {type(m)}')
	return NORMAL

#
#
def PubSub_NORMAL_OpenPeer(self, message):
	k = ipp_key(message.connecting_ipp)

	key = message.key
	who = self.return_address
	try:
		# Peer already requested.
		peer, opened_by = self.opened_peer[k]
		opened_by[who] = key
	except KeyError:
		# A previously unmentioned peer.
		self.trace(f'Connect to peer {k}')
		peer = None
		opened_by = {}
		opened_by[who] = key
		self.opened_peer[k] = [peer, opened_by]
		connect(self, message.connecting_ipp)

	if peer is None:	# Waiting for result of connect().
		return NORMAL

	# Good to go.
	self.forward(PeerOpened(connecting_ipp=message.connecting_ipp, key=key), who, peer)
	return NORMAL

def PubSub_NORMAL_Connected(self, message):
	k = ipp_key(message.requested_ipp)

	try:
		# Must already exist.
		po = self.opened_peer[k]
		peer, opened_by = po
	except KeyError:
		self.warning(f'Connected to unknown peer {k}')
		self.reply(Close())
		return NORMAL

	peer = self.return_address
	po[0] = peer
	for who, key in opened_by.items():
		self.forward(PeerOpened(connecting_ipp=message.requested_ipp, key=key), who, peer)

	return NORMAL

def PubSub_NORMAL_NotConnected(self, message):
	k = ipp_key(message.requested_ipp)

	try:
		# Must already exist.
		po = self.opened_peer[k]
		peer, opened_by = po
	except KeyError:
		self.warning(f'Incomplete connect to unknown peer {k}')
		return NORMAL

	# Advise interested parties that peering failed.
	reason = message.error_text
	for who, key in opened_by.items():
		self.send(NotPeered(key, reason), who)

	# Remove record of the attempt to force a fresh connect
	# process the next time around.
	self.opened_peer.pop(k, None)
	return NORMAL

def find_peer(self):
	for k, v in self.opened_peer.items():
		peer, opened_by = v
		if peer == self.return_address:
			return peer, opened_by, k
	return None, None, None

def PubSub_NORMAL_Abandoned(self, message):
	peer, opened_by, k = find_peer(self)
	if peer is None:
		self.warning('Close/abandon of unknown peer connection')
		return NORMAL

	# Advise interested parties.
	for who, key in opened_by.items():
		self.send(NotPeered(key, 'Network close/abandon'), who)

	# Force a fresh connect processs.
	self.opened_peer.pop(k, None)
	return NORMAL

def PubSub_NORMAL_Closed(self, message):
	# Should be nobody left to do.
	return NORMAL

def PubSub_NORMAL_ClosePeer(self, message):
	k = ipp_key(message.connecting_ipp)
	who = self.return_address
	try:
		# Peer already requested.
		peer, opened_by = self.opened_peer[k]
	except KeyError:
		# A previously unmentioned peer.
		self.trace(f'Closing of unknown peer "{k}"')
		return NORMAL

	del opened_by[who]
	if peer is None:	# Waiting for result of connect().
		return NORMAL

	if len(opened_by) < 1:
		self.send(Close(), peer)
		po = self.opened_peer.pop(k, None)
		if po is None:
			self.trace(f'Discard of unknown peer "{k}"')
	return NORMAL

def PubSub_NORMAL_CapRoutes(self, message):
	self.trace(f'Capping services and searches to [{ScopeOfService.to_name(message.service_scope)}]')
	for m, a in self.running():
		if not isinstance(m, list) or len(m) != 2:
			continue
		if isinstance(m[0], (PublishAsName, SubscribeToName)):
			self.send(message, a)
		else:
			self.warning(f'Cannot cap unknown type {type(m)}')
	return NORMAL

def PubSub_NORMAL_Stop(self, message):
	if self.working():
		self.abort()
		return COMPLETING

	self.complete(ar.Aborted())

def PubSub_COMPLETING_Completed(self, message):
	self.debrief()
	if self.working():
		return COMPLETING

	# This clears the publish/subscribe objects but
	# not the peer connections. Leave that to the
	# framework.
	self.complete(ar.Aborted())

PUBSUB_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	NORMAL: (
		(PublishAsName,	SubscribeToName, Retract,
		OpenPeer, Connected, NotConnected, ClosePeer,
		Closed, Abandoned,
		CapRoutes,
		ar.Completed, ar.Stop), ()
	),
	COMPLETING: (
		(ar.Completed), (Closed, Abandoned)
	),
}

ar.bind(PubSub, PUBSUB_DISPATCH)

# The public interface to the directory service.
#

### PS-pub-0 Start of publish
def publish(self, requested_name, create_session=None, declared_scope=ScopeOfService.WAN):
	self.send(PublishAsName(requested_name, create_session, declared_scope), pb.house)

### PS-sub-0 Start of subscribe
def subscribe(self, requested_search, create_session=None, declared_scope=ScopeOfService.WAN):
	self.send(SubscribeToName(requested_search, create_session, declared_scope), pb.house)

def clear(self, session, value=None):
	self.send(Clear(session, value), session.agent_address)

def retract(self):
	self.send(Retract(self.address), pb.house)

