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
__docformat__ = 'restructuredtext'

import errno
import platform
import queue
import threading
import socket
import select
import re
import uuid
from nacl.public import PrivateKey, PublicKey, Box
from enum import Enum
from datetime import datetime

from .general_purpose import *
from .ip_networking import *
from .object_space import *
from .convert_memory import *
from .virtual_memory import *
from .message_memory import *
from .convert_type import *
from .virtual_codec import *
from .json_codec import *
from .virtual_runtime import *
from .virtual_point import *
from .point_runtime import *
from .point_machine import *
from .object_runtime import *
from .bind_type import *
from .http import ApiServerStream, ApiClientSession, ApiClientStream

__all__ = [
	'ListenForStream',
	'ConnectStream',
	'Listening',
	'Accepted',
	'Connected',
	'NotListening',
	'NotAccepted',
	'NotConnected',
	'EndOfTransport',
	'Close',
	'Closed',
	'listen',
	'connect',
	'stop_listening',
]

# Platform dependent operation. Initially - windows doesnt
# like partial socket close.
PLATFORM_SYSTEM = platform.system()

if PLATFORM_SYSTEM == 'Windows':
	SHUT_SOCKET = socket.SHUT_RDWR
else:
	SHUT_SOCKET = socket.SHUT_RD

TS = Gas(sockets=None, channel=None)

# Machine states.
class INITIAL: pass
class PENDING: pass
class NORMAL: pass
class CHECKING: pass
class CLEARING: pass
class PAUSING: pass

# Control messages sent to the sockets thread
# via the control channel.
class ListenForStream(object):
	"""Session request, open a server presence.

	:param lid: unique id for this listen request
	:type lid: UUID
	:param requested_ipp: IP and port requested by the application
	:type requested_ipp: HostPort
	:param encrypted: enable encryption
	:type encrypted: bool
	:param http_server: list of classes
	:type http_server: list
	:param default_to_request: default to :class:`~.HttpRequest`
	:type default_to_request: bool
	:param ansar_client: expect layer cake encodings
	:type ansar_client: bool
	"""
	def __init__(self, lid: UUID=None, requested_ipp: HostPort=None, encrypted: bool=False,
			http_server: list[Type]=None, default_to_request: bool=True, ansar_client: bool=False):
		self.lid = lid
		self.requested_ipp = requested_ipp or HostPort()
		self.encrypted = encrypted
		self.http_server = http_server or []
		self.default_to_request = default_to_request
		self.ansar_client = ansar_client

class ConnectStream(object):
	"""
	Session request, open a transport to an address.

	:param requested_ipp: IP and port requested by the application
	:type requested_ipp: HostPort
	:param encrypted: enable encryption
	:type encrypted: bool
	:param self_checking: monitor the connection
	:type self_checking: bool
	:param http_client: inserted as the path in the request URI
	:type http_client: str
	:param layer_cake_json: enable layer cake JSON body
	:type layer_cake_json: bool
	"""
	def __init__(self, requested_ipp: HostPort=None, encrypted: bool=False, self_checking: bool=False,
			http_client: str=None, layer_cake_json: bool=False):
		self.requested_ipp = requested_ipp or HostPort()
		self.encrypted = encrypted
		self.self_checking = self_checking
		self.http_client = http_client
		self.layer_cake_json = layer_cake_json

class StopListening(object):
	def __init__(self, lid: UUID=None):
		self.lid = lid

# Update messages from sockets thread to app.
class Listening(object):
	"""Session notification, server presence established.

	:param request: original listen request
	:type request: ListenForStream
	:param listening_ipp: network address in use
	:type listening_ipp: HostPort
	:param controller_address: object that requested the listen
	:type controller_address: :ref:`address<lc-address>`
	"""
	def __init__(self, request: ListenForStream=None,
			listening_ipp: HostPort=None,
			controller_address: Address=None):
		self.request = request
		self.listening_ipp = listening_ipp or HostPort()
		self.controller_address = controller_address or NO_SUCH_ADDRESS

class Accepted(object):
	"""Session notification, transport to client established.

	:param listening: listening server
	:type listening: Listening
	:param opened_ipp: network address of accepted transport
	:type opened_ipp: HostPort
	:param proxy_address: address of remote party
	:type proxy_address: :ref:`address<lc-address>`
	:param opened_at: moment of acceptance
	:type opened_at: datetime
	"""
	def __init__(self, listening: Listening=None,
			opened_ipp: HostPort=None,
			proxy_address: Address=None,
			opened_at: datetime=None):
		self.listening = listening or Listening()
		self.opened_ipp = opened_ipp or HostPort()
		self.proxy_address = proxy_address or NO_SUCH_ADDRESS
		self.opened_at = opened_at

class Connected(object):
	"""Session notification, transport to server established.

	:param request: original connect request
	:type request: ConnectStream
	:param opened_ipp: network address of connected transport
	:type opened_ipp: HostPort
	:param proxy_address: address of remote party
	:type proxy_address: :ref:`address<lc-address>`
	:param opened_at: moment of connection
	:type opened_at: datetime
	"""
	def __init__(self, request: ConnectStream=None, opened_ipp: HostPort=None,
			proxy_address: Address=None,
			opened_at: datetime=None):
		self.request = request or ConnectStream()
		self.opened_ipp = opened_ipp or HostPort()
		self.proxy_address = proxy_address or NO_SUCH_ADDRESS
		self.opened_at = opened_at

class NotListening(Faulted):
	"""Session notification, server not established.

	:param request: original listen request
	:type request: ListenForStream
	:param error_code: platform error number
	:type error_code: int
	:param error_text: platform error message
	:type error_text: str
	"""
	def __init__(self, request: ListenForStream=None, error_code: int=0, error_text: str=None):
		self.request = request or ListenForStream()
		requested_ipp = self.request.requested_ipp
		note = '' if not error_text else f' ({error_text})'
		if requested_ipp.host is None or requested_ipp.port is None:
			Faulted.__init__(self, f'cannot stop listen"{note}')
			return
		note = '' if not error_text else f' ({error_text})'
		Faulted.__init__(self, f'cannot listen at "{requested_ipp}"{note}', error_code=error_code)

class NotAccepted(Faulted):
	"""Session notification, transport to client not established.

	:param listening: listening server
	:type listening: Listening
	:param error_code: platform error number
	:type error_code: int
	:param error_text: platform error message
	:type error_text: str
	"""
	def __init__(self, listening: Listening=None, error_code: int=0, error_text: str=None):
		self.listening = listening or Listening()
		listening_ipp = self.listening.listening_ipp
		note = '' if not error_text else f' ({error_text})'
		Faulted.__init__(self, f'cannot accept at "{listening_ipp}"{note}', error_code=error_code)

class NotConnected(Faulted):
	"""Session notification, transport to server not established.

	:param request: original connect request
	:type request: ConnectStream
	:param error_code: platform error number
	:type error_code: int
	:param error_text: platform error message
	:type error_text: str
	"""
	def __init__(self, request: ConnectStream=None, error_code: int=0, error_text: str=None):
		self.request = request or ConnectStream()
		requested_ipp = self.request.requested_ipp
		note = '' if not error_text else f' ({error_text})'
		Faulted.__init__(self, f'cannot connect to "{requested_ipp}"{note}', error_code=error_code)

bind(ListenForStream)
bind(ConnectStream)
bind(StopListening)
bind(Listening, copy_before_sending=False)
bind(Accepted)
bind(Connected)
bind(NotListening, explanation=Unicode(), exit_status=Integer8())
bind(NotAccepted, explanation=Unicode(), exit_status=Integer8())
bind(NotConnected, explanation=Unicode(), exit_status=Integer8())

# Session termination messages. Handshake between app
# and sockets thread to cleanly terminate a connection.

class EndOfTransport(Enum):
	"""
	Enumeration of the reasons that a connect/listen transport might close.

	* ON_REQUEST - local process sent a Closed.
	* ABANDONED_BY_REMOTE - transport abandoned by network or remote.
	* WENT_STALE - transport closed by keep-alive machinery.
	* OUTBOUND_STREAMING - fault during outboud serialization.
	* INBOUND_STREAMING - fault during inboud serialization.
	"""
	ON_REQUEST=1
	ABANDONED_BY_REMOTE=2
	WENT_STALE=3
	OUTBOUND_STREAMING=4
	INBOUND_STREAMING=5

class Close(object):
	"""Session control, terminate the messaging transport.

	:param value: completion value for the session
	:type value: any
	:param reason: what prompted the termination
	:type reason: EndOfTransport
	:param note: short diagnostic
	:type note: str
	:param error_code: platform error code
	:type error_code: int
	"""
	def __init__(self, value: Any=None, reason: EndOfTransport=None, note: str=None, error_code: int=None):
		self.value = value
		self.reason = reason or EndOfTransport.ON_REQUEST
		self.note = note
		self.error_code = error_code

class Closed(object):
	"""
	Session notification, local termination of the messaging transport.

	:param value: completion value for the session
	:type value: any
	:param reason: what prompted the termination
	:type reason: EndOfTransport
	:param note: short diagnostic
	:type note: str
	:param error_code: platform error code
	:type error_code: int
	:param opened_ipp: network address of terminated transport
	:type opened_ipp: HostPort
	:param opened_at: moment of termination
	:type opened_at: datetime
	"""
	def __init__(self, value: Any=None, reason: EndOfTransport=None,
			note: str=None, error_code: int=None,
			opened_ipp: HostPort=None, opened_at: datetime=None):
		self.value = value
		self.reason = reason or EndOfTransport.ON_REQUEST
		self.note = note
		self.error_code = error_code
		self.opened_ipp = opened_ipp or HostPort()
		self.opened_at = opened_at

bind(Close, copy_before_sending=False)
bind(Closed, copy_before_sending=False)

#
#
class Shutdown(object):
	def __init__(self, s=None, close: Close=None):
		self.s = s
		self.close = close or Close()

class Bump(object):
	def __init__(self, s=None):
		self.s = s

bind(Shutdown, not_portable=True)
bind(Bump, not_portable=True)

# Classes representing open sockets for one reason or another;
# - ControlChannel.... accepted end of backdoor into sockets loop.
# - TcpServer ........ an active listen
# - TcpClient ........ an active connect
# - TcpTransport ........ established transport, child of listen or connect

class ControlChannel(object):
	def __init__(self, s):
		self.s = s

class TcpServer(object):
	def __init__(self, s, request, listening, controller_address):
		self.s = s
		self.request = request
		self.listening = listening
		self.controller_address = controller_address

	def encrypted(self):
		return self.request.encrypted

class TcpClient(object):
	def __init__(self, s, request, connected, controller_address):
		self.s = s
		self.request = request
		self.connected = connected
		self.controller_address = controller_address

	def encrypted(self):
		return self.request.encrypted

	def self_checking(self):
		return self.request.self_checking

# Underlying network constraints.
#
TCP_RECV = 4096
TCP_SEND = 4096
UDP_RECV = 4096
UDP_SEND = 4096

# Security/reliability behaviours.
#
NUMBER_OF_DIGITS = (7 * 3) + 2
GIANT_FRAME = 1048576

#
#
class Header(object):
	def __init__(self, to_address=None, return_address=None, tunnel: bool=False):
		self.to_address = to_address
		self.return_address = return_address
		self.tunnel = tunnel

bind(Header, to_address=TargetAddress(), return_address=Address())

HEADING = UserDefined(Header)
BOOK = MapOf(Unicode(),Address())

#
#
class Relay(object):
	def __init__(self, block: bytearray=None, address_book: dict[str, Address]=None):
		self.block = block
		self.address_book = address_book

bind(Relay)

# Conversion of messages to on-the-wire blocks, and back again.
# The default, fully typed, async, bidirectional messaging.
class MessageStream(object):
	def __init__(self, transport):
		self.transport = transport

		# Specific to input decoding.
		self.analysis_state = 1
		self.size_byte = bytearray()
		self.size_len = []
		self.frame_size = 0
		self.frame_byte = bytearray()

		# Inbound FSM processing of a frame.
		def s1(c):
			if c in b'0123456789,':
				nd = len(self.size_byte)
				if nd < NUMBER_OF_DIGITS:
					self.size_byte.append(c)
					return 1
				raise OverflowError(f'unlikely frame size with {nd} digits')
			elif c == 10:	# ord('\n')
				a = self.size_byte.split(b',')
				if len(a) != 3:
					raise ValueError(f'unexpected dimension')
				for b in a:
					if not b or not b.isdigit():
						raise ValueError(f'mangled frame dimensions')
				s0 = int(a[0])
				s1 = int(a[1])
				s2 = int(a[2])
				self.size_len = [s0, s1, s2]
				if s0 > s2 or (s0 + s1) > s2:
					raise ValueError(f'unlikely frame offsets')
				self.jump_size = s2
				if self.jump_size > GIANT_FRAME:
					raise OverflowError(f'oversize frame of {self.jump_size} bytes')
				elif self.jump_size == 0:
					return 3
				return 2
			raise ValueError(f'frame with unexpected {c} in digits')

		def s2(c):
			self.frame_byte.append(c)
			self.jump_size -= 1
			if self.jump_size == 0:
				return 3
			return 2

		def s3(c):
			if c == 10:
				return 0
			raise ValueError(f'unexpected {c} at end-of-frame')

		self.shift = {
			1: s1,
			2: s2,
			3: s3,
		}

	# Push a message onto the byte stream.
	def	message_to_block(self, mtr):
		m, t, r = mtr
		encoded_bytes = self.transport.encoded_bytes
		tunnel = False
		key_box = self.transport.key_box
		codec = self.transport.codec

		# Types significant to streaming.
		# Be nice to move DH detection elsewhere.
		if isinstance(m, tuple) and isinstance(m[1], Block):
			if m[0] is not None:
				tunnel = True
		elif isinstance(m, Diffie):
			self.transport.private_key = PrivateKey.generate()
			public_bytes = self.transport.private_key.public_key.encode()
			m.public_key = bytearray(public_bytes)
		elif isinstance(m, Hellman):
			self.transport.private_key = PrivateKey.generate()
			shared_bytes = bytes(m.public_key)
			shared_key = PublicKey(shared_bytes)
			self.transport.key_box = Box(self.transport.private_key, shared_key)
			public_bytes = self.transport.private_key.public_key.encode()
			m.public_key = bytearray(public_bytes)

		# Bring the parts together.
		# 1. Header
		h = Header(t, r, tunnel)
		e = codec.encode(h, HEADING)
		b0 = e.encode('utf-8')
		n0 = len(b0)

		# 2. Message body - 1 of following 3.
		if tunnel:
			# b1 = m.block
			b1 = m[0]
			n1 = len(b1)
			s = codec.encode({}, BOOK)
		elif isinstance(m, Relay):
			b1 = m.block
			n1 = len(b1)
			s = codec.encode(m.address_book, BOOK)
		else:
			address_book = {}
			e = codec.encode(m, Any(), address_book=address_book)
			b1 = e.encode('utf-8')
			n1 = len(b1)
			s = codec.encode(address_book, BOOK)

		# 3. Mutated addresses.
		b2 = s.encode('utf-8')

		# Combine into 1 and optionally encrypt.
		b0 += b1
		b0 += b2
		if key_box:
			b0 = key_box.encrypt(b0)
		n3 = len(b0)

		# Put frame on the transport.
		n = f'{n0},{n1},{n3}'
		encoded_bytes += n.encode('ascii')
		encoded_bytes += b'\n'
		encoded_bytes += b0
		encoded_bytes += b'\n'

	# Complete zero or more messages, using the given block.
	def recover_message(self, received, sockets):
		# Need a loop here because of encryption handshaking.
		codec = self.transport.codec
		proxy_address = self.transport.proxy_address
		diffie_hellman = self.transport.diffie_hellman

		for h, b_, a in self.recover_frame(received):
			s = h.decode('utf-8')
			header = codec.decode(s, HEADING)
			s = a.decode('utf-8')
			address_book = codec.decode(s, BOOK)

			to_address = header.to_address
			return_address = header.return_address

			if header.tunnel:					# Binary block - directly from the frame.
				body = bytearray(b_)
				body = cast_to(body, bytearray_type)

			elif len(header.to_address) > 1:	# Passing through. Just received and headed back out.
				body = Relay(b_, address_book)

			else:
				# Need to recover the fully-typed message.
				s = b_.decode('utf-8')
				body = codec.decode(s, Any(), address_book=address_book)

				#for address, path in space:
				#	poke(body, address, path)

				# Handling of encryption handshaking and keep-alives.
				if isinstance(body, Diffie):
					sockets.send(Hellman(body.public_key), proxy_address)
					if not diffie_hellman:
						continue
					h = diffie_hellman[0]
					body, to_address, return_address = h
				elif isinstance(body, Hellman):
					public_bytes = bytes(body.public_key)
					public_key = PublicKey(public_bytes)
					self.transport.key_box = Box(self.transport.private_key, public_key)
					if not diffie_hellman:
						continue
					h = diffie_hellman[0]
					body, to_address, return_address = h
				elif isinstance(body, KeepAlive):
					sockets.send(body, return_address)
					continue
				else:
					pass	# Normal application messaging.

			yield body, to_address, return_address

	# Pull zero or more frames from the given block.
	def recover_frame(self, received):
		key_box = self.transport.key_box
		for c in received:
			next = self.shift[self.analysis_state](c)
			if next:
				self.analysis_state = next
				continue

			# Completed frame.
			f = bytes(self.frame_byte)
			if key_box:
				f = key_box.decrypt(f)

			# Breakout parts and yield.
			n0 = self.size_len[0]
			n1 = self.size_len[1]
			b2 = n0 + n1
			yield f[0:n0], f[n0:b2], f[b2:]

			# Restart.
			self.analysis_state = 1
			self.size_byte = bytearray()
			self.size_len = []
			self.frame_size = 0
			self.frame_byte = bytearray()

# Generic section of all network messaging.
class TcpTransport(object):
	def __init__(self, messaging_type, parent, controller_address, opened):
		self.messaging = messaging_type(self)
		self.parent = parent
		self.controller_address = controller_address
		self.return_proxy = None
		self.local_termination = None
		self.proxy_address = None

		self.codec = None

		self.pending = []			# Messages not yet in the loop.
		self.lock = threading.RLock()		# Safe sharing and empty detection.
		self.messages_to_encode = deque()

		self.encoded_bytes = bytearray()

		self.diffie_hellman = None
		self.private_key = None
		self.key_box = None

		self.opened = opened
		self.closing = None

	def set_routing(self, return_proxy, local_termination, proxy_address):
		# Define addresses for message forwarding.
		# return_proxy ........ address that response should go back to.
		# local_termination ... address of default target, actor or session.
		# proxy_address ...... source address of connection updates, session or proxy.
		self.codec = CodecJson(return_proxy=return_proxy, local_termination=local_termination)
		self.return_proxy = return_proxy
		self.local_termination = local_termination
		self.proxy_address = proxy_address

	# Output
	# Application to proxy.
	def put(self, m, t, r):
		try:
			self.lock.acquire()
			empty = len(self.pending) == 0
			t3 = (m, t, r)
			self.pending.append(t3)
		finally:
			self.lock.release()
		return empty

	def drain(self, a):
		try:
			self.lock.acquire()
			count = len(self.pending)
			a.extend(self.pending)
			self.pending = []
		finally:
			self.lock.release()
		return count

	# Proxy to transport.
	def send_a_block(self, s):
		t = self.queue_to_block()
		if t == 0:
			return False
		n = t if t <= TCP_SEND else TCP_SEND
		chunk = self.encoded_bytes[:n]
		n = s.send(chunk)
		if n:
			self.encoded_bytes = self.encoded_bytes[n:]
			return True
		return False

	def queue_to_block(self):
		encoded_bytes = self.encoded_bytes
		while len(encoded_bytes) < TCP_SEND:
			if len(self.messages_to_encode) == 0:
				added = self.drain(self.messages_to_encode)
				if added == 0:
					break
			# The message and to-return addresses.
			mtr = self.messages_to_encode.popleft()
			self.messaging.message_to_block(mtr)

		# Bytes available for a send.
		return len(encoded_bytes)

	# Input.
	def receive_a_message(self, received, sockets):
		for body, to_address, return_address in self.messaging.recover_message(received, sockets):
			sockets.forward(body, to_address, return_address)

#
#
class KeepAlive(object):
	def __init__(self, seconds=0.0):
		self.seconds = seconds

class StillThere(object):
	def __init__(self, seconds=0.0):
		self.seconds = seconds

bind(KeepAlive, copy_before_sending=False, execution_trace=True, message_trail=True)
bind(StillThere, copy_before_sending=False, execution_trace=True, message_trail=True)

IDLE_TRANSPORT = 60.0
RESPONSIVE_TRANSPORT = 5.0

DELAYED_KEEPALIVE = T1
REQUESTED_CHECK = T2

class SocketKeeper(Point, StateMachine):
	def __init__(self, proxy_address=None, expecting=None):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.proxy_address = proxy_address
		self.expecting = expecting
		self.keeper_address = None

	def originate(self, message, address):
		s = spread_out(IDLE_TRANSPORT, 5)
		self.send(message(s), address)
		return s

def SocketKeeper_INITIAL_Start(self, message):
	if self.expecting is None:
		self.start(T1, IDLE_TRANSPORT / 4.0)
		return PAUSING

	self.keeper_address = self.proxy_address
	self.start(T2, self.expecting)
	return PENDING

def SocketKeeper_PAUSING_T1(self, message):
	s = self.originate(KeepAlive, self.proxy_address)
	self.start(T3, s + 3.0)						# Expect response.
	return CHECKING

def SocketKeeper_PAUSING_Stop(self, message):
	self.complete(Aborted())

def SocketKeeper_PENDING_T2(self, message):		# Fulfil expectation and start own cycle.
	s = self.originate(StillThere, self.keeper_address)
	self.start(T3, s + 5.0)						# Expect response.
	return CHECKING

def SocketKeeper_PENDING_Stop(self, message):
	self.complete(Aborted())

def SocketKeeper_CHECKING_StillThere(self, message):
	self.keeper_address = self.return_address
	self.cancel(T3)
	self.start(T2, message.seconds)						# All good. Keep going.
	return PENDING

def SocketKeeper_CHECKING_T3(self, message):
	self.send(Close(), self.remote_address)
	self.complete(TimedOut(T3))

def SocketKeeper_CHECKING_Stop(self, message):
	self.complete(Aborted())

SOCKET_KEEPER_DISPATCH = {
	INITIAL: (
		(Start,), ()
	),
	PAUSING: (
		(T1, Stop), ()
	),
	PENDING: (
		(T2, Stop), ()
	),
	CHECKING: (
		(StillThere, T3, Stop), ()
	),
}

bind(SocketKeeper, SOCKET_KEEPER_DISPATCH, thread='keeper', execution_trace=False)

#
#
class SocketProxy(Point, StateMachine):
	"""Local representation of an object at remote end of a network connection.

	:param s: associated network connection
	:type s: socket descriptor
	:param channel: async socket loop
	:type channel: internal
	:param transport: associated buffering
	:type transport: internal
	"""
	def __init__(self, s, channel, transport, self_checking=False):
		Point.__init__(self)
		StateMachine.__init__(self, INITIAL)
		self.s = s
		self.channel = channel
		self.transport = transport
		self.self_checking = self_checking
		self.keeper = None
		self.checked = 0
	
	def first_few(self):
		if self.checked > 4:
			return False
		self.checked += 1
		return True

SOCKET_DOWN = (errno.ECONNRESET, errno.EHOSTDOWN, errno.ENETDOWN, errno.ENETRESET)

def SocketProxy_INITIAL_Start(self, message):
	if self.self_checking:
		self.keeper = self.create(SocketKeeper, self.object_address)
	return NORMAL

def SocketProxy_NORMAL_KeepAlive(self, message):
	self.keeper = self.create(SocketKeeper, self.object_address, message.seconds)
	return NORMAL

def SocketProxy_NORMAL_Unknown(self, message):
	message = cast_to(message, self.received_type)
	empty = self.transport.put(message, self.to_address, self.return_address)
	if empty:
		self.channel.send(Bump(self.s), self.object_address)
	return NORMAL

def SocketProxy_NORMAL_Close(self, message):
	self.channel.send(Shutdown(self.s, message), self.object_address)
	if self.keeper:
		self.send(Stop(), self.keeper)
		return CLEARING
	self.complete()

def SocketProxy_NORMAL_Stop(self, message):
	# Close created internally by ListenConnect.
	self.channel.send(Shutdown(self.s), self.object_address)
	if self.keeper:
		self.send(Stop(), self.keeper)
		return CLEARING
	self.complete()

def SocketProxy_CLEARING_Returned(self, message):
	self.complete()

TCP_PROXY_DISPATCH = {
	INITIAL: (
		(Start,),
		()
	),
	NORMAL: (
		(KeepAlive, Unknown, Close, Stop),
		()
	),
	CLEARING: (
		(Returned,),
		()
	),
}

bind(SocketProxy, TCP_PROXY_DISPATCH, thread='socketry')

#
#
class Diffie(object):
	def __init__(self, public_key: bytearray=None):
		self.public_key = public_key

class Hellman(object):
	def __init__(self, public_key: bytearray=None):
		self.public_key = public_key

bind(Diffie, copy_before_sending=False)
bind(Hellman, copy_before_sending=False)



# Signals from the network represented
# as distinct classes - for dispatching.
class ReceiveBlock: pass
class ReadyToSend: pass
class BrokenTransport: pass

# CONTROL CHANNEL
# First two functions are for handling the 1-byte events
# coming across the control socket.
def ControlChannel_ReceiveBlock(self, control, s):
	s.recv(1)					   # Consume the bump.
	mr = self.pending.get()

	# This second jump is to simulate the common handling of control
	# channel events and select events.
	c = type(mr[0])
	try:
		f = SELECT_TABLE[(ControlChannel, c)]
	except KeyError:
		self.warning(f'unknown message received on control channel ({c})')
		return
	f(self, control, mr)

def ControlChannel_BrokenTransport(self, control, s):
	self.fault('control channel broken')
	self.clear_out(s)

# The rest of them handle the simulated receive of the
# actual message.
def ControlChannel_ListenForStream(self, control, mr):
	m, r = mr
	requested_ipp = m.requested_ipp

	if not self.running:
		nl = NotListening(m, error_code=0, error_text='sockets shutting down')
		self.send(nl, r)
		return

	try:
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error as e:
		nl = NotListening(m, error_code=e.errno, error_text=str(e))
		self.send(nl, r)
		return

	def server_not_listening(e):
		server.close()
		nl = NotListening(m, error_code=e.errno, error_text=str(e))
		self.send(nl, r)

	try:
		server.setblocking(False)
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind(requested_ipp.inet())
		server.listen(5)
	except (socket.herror, socket.gaierror, socket.error) as e:
		server_not_listening(e)
		return
	except OverflowError as e:
		server.close()
		nl = NotListening(m, error_code=0, error_text=str(e))
		self.send(nl, r)
		return

	hap = server.getsockname()
	listening_ipp = HostPort(hap[0], hap[1])

	note = ' (encrypted)' if m.encrypted else ''
	self.trace(f'Listening{note} on "{listening_ipp}", requested "{requested_ipp}"')

	listening = Listening(m, listening_ipp=listening_ipp, controller_address=r)

	self.networking[server] = TcpServer(server, m, listening, r)
	self.receiving.append(server)
	self.faulting.append(server)

	self.lid[m.lid] = server

	self.send(listening, r)

def close_ending(proxy):
	def ending(value, parent, address, object_type):
		send_a_message(Close(value), proxy, address)
	return ending

def open_stream(self, parent, s, opened):
	controller_address = parent.controller_address
	self_checking = False
	ts = MessageStream

	if isinstance(parent, TcpClient):
		self_checking = parent.self_checking()
		if parent.request.http_client:
			ts = ApiClientStream
	elif isinstance(parent, TcpServer):
		if len(parent.request.http_server) > 0:
			ts = ApiServerStream

	transport = TcpTransport(ts, parent, controller_address, opened)
	proxy_address = self.create(SocketProxy, s, self.channel, transport, self_checking=self_checking, object_ending=no_ending)

	if ts == ApiClientStream:
		ending = close_ending(proxy_address)
		session_address = self.create(ApiClientSession,
			controller_address=controller_address, proxy_address=proxy_address,
			object_ending=ending)
		transport.set_routing(proxy_address, session_address, session_address)
	else:
		transport.set_routing(proxy_address, controller_address, proxy_address)

	self.networking[s] = transport
	return transport, proxy_address

def ControlChannel_ConnectStream(self, control, mr):
	m, r = mr
	requested_ipp = m.requested_ipp

	if not self.running:
		nc = NotConnected(m, 0, 'sockets shutting down')
		self.send(nc, r)
		return

	try:
		client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client.setblocking(False)
	except socket.error as e:
		self.send(NotConnected(m, e.errno, str(e)), r)
		return

	def client_not_connected(e):
		client.close()
		self.send(NotConnected(m, e.errno, str(e)), r)

	try:
		e = client.connect_ex(requested_ipp.inet())
		if e:
			# Connect request cannot complete. Check for codes indicating
			# async issue. If not it's a real error.
			if e not in (errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN):
				client.close()
				self.send(NotConnected(m, e, 'Connect incomplete and no pending indication.'), r)
				return

			# Build a transient "session" that just exists to catch
			# an initial, either send or fault (a receive is treated
			# as an error). True session is constructed on receiving
			# a "normal" send event.
			pending = TcpClient(client, m, None, r)

			self.networking[client] = pending
			self.receiving.append(client)
			self.sending.append(client)
			self.faulting.append(client)
			return

	except (socket.herror, socket.gaierror, socket.error) as e:
		client_not_connected(e)
		return
	except OverflowError as e:
		client.close()
		self.send(NotConnected(m, 0, str(e)), r)
		return

	hap = client.getsockname()
	opened_ipp = HostPort(hap[0], hap[1])
	connected = Connected(m, opened_ipp=opened_ipp, opened_at=world_now())

	parent = TcpClient(client, m, connected, r)
	transport, proxy_address = open_stream(self, parent, client, connected)
	connected.proxy_address = proxy_address

	self.networking[client] = transport
	self.receiving.append(client)
	self.sending.append(client)
	self.faulting.append(client)

	if m.encrypted:
		self.trace(f'Connected (encrypted) to "{requested_ipp}", at local address "{opened_ipp}"')
		not_connected = NotConnected(m, None, None)
		transport.diffie_hellman = (
			(connected, r, transport.proxy_address),
			(not_connected, r))
		# Start the exchange. Public key filled out during
		# streaming.
		self.send(Diffie(), proxy_address)
		return
	self.trace(f'Connected to "{requested_ipp}", at local address ""{opened_ipp}"')

	self.forward(connected, r, transport.proxy_address)

def ControlChannel_StopListening(self, control, mr):
	m, r = mr

	if not self.running:
		nl = NotListening(ListenForStream(lid=m.lid), 0, 'sockets shutting down')
		self.send(nl, r)
		return

	server = self.lid.get(m.lid, None)
	if server is None:
		e = f'no such entry "{m.lid}"'
		self.warning(e)
		not_listening = NotListening(ListenForStream(lid=m.lid), 0, e)
		self.send(not_listening, r)
		return
	server.shutdown(socket.SHUT_RDWR)

def ControlChannel_Stop(self, control, mr):
	m, r = mr

	if not self.running:
		return

	# Initiate the teardown of all application sockets.
	for k, v in self.networking.items():
		if isinstance(v, TcpTransport):
			self.send(Stop(), v.proxy_address)			# Take out proxy as well.
			#k.shutdown(socket.SHUT_RDWR)				# Direct to socket.
		elif isinstance(v, (TcpServer, TcpClient)):
			k.shutdown(socket.SHUT_RDWR)				# Direct to socket.

	# Mark the ListenConnect state. When the
	# socket count drops to 0, the instance
	# will return.
	self.running = False

def ControlChannel_Bump(self, control, mr):
	m, r = mr
	if m.s.fileno() < 0:
		# Catches the situation where the socket has been abandoned
		# by the remote and the notification to the proxy arrives behind
		# the bump.
		return
	try:
		self.sending.index(m.s)
		return
	except ValueError:
		pass
	self.sending.append(m.s)

def ControlChannel_Shutdown(self, control, mr):
	m, r = mr
	try:
		transport = self.networking[m.s]
	except KeyError:
		# Already cleared by Abandoned codepath.
		return
	transport.closing = m.close
	m.s.shutdown(SHUT_SOCKET)

# Dispatch of socket signals;
# - ReceiveBlock ...... there are bytes to recv
# - ReadyToSend ....... an opportunity to send
# - BrokenTransport ... error on socket
# and server/client/connection;
# - TcpServer ......... listen waiting to accept
# - TcpClient ......... partial connect
# - TcpTransport ......... established connection

def TcpServer_ReceiveBlock(self, server, s):
	listening = server.listening
	request = server.request

	try:
		accepted, hap = s.accept()
		accepted.setblocking(False)
	except socket.error as e:
		#if e.errno == 22:
		self.clear_out(s)
		not_listening = NotListening(request, e.errno, str(e))
		self.send(not_listening, server.controller_address)
		return
		#not_accepted = NotAccepted(listening, e.errno, str(e))
		#self.send(not_accepted, server.controller_address)
		#return

	if not self.running:
		# Do not add to operational tables, i.e. networking[].
		accepted.shutdown(socket.SHUT_RDWR)
		accepted.close()
		return
		
	transport, proxy_address = open_stream(self, server, accepted, None)
	self.receiving.append(accepted)
	self.sending.append(accepted)
	self.faulting.append(accepted)

	opened_ipp = HostPort(hap[0], hap[1])

	opened_at = world_now()
	accepted = Accepted(listening=listening,
		opened_ipp=opened_ipp, proxy_address=transport.proxy_address,
		opened_at=opened_at)
	transport.opened = accepted

	if request.encrypted:
		self.trace(f'Accepted (encrypted) "{opened_ipp}", listening "{listening.listening_ipp}"')
		not_accepted = NotAccepted(listening, None, None)
		transport.diffie_hellman = (
			(accepted, server.controller_address, transport.proxy_address),
			(not_accepted, server.controller_address))
		return
	self.trace(f'Accepted "{opened_ipp}", listening "{listening.listening_ipp}"')

	self.forward(accepted, server.controller_address, transport.proxy_address)

def TcpServer_BrokenTransport(self, server, s):
	listening = server.listening
	self.send(NotListening(listening.listening_ipp, 0, "signaled by networking subsystem"), server.controller_address)
	self.clear_out(s, TcpServer)

#
def TcpClient_ReceiveBlock(self, selector, s):
	client = s
	request = selector.request

	hap = client.getsockname()
	opened_ipp = HostPort(hap[0], hap[1])
	requested_ipp = request.requested_ipp

	try:
		scrap = s.recv(TCP_RECV)

		# No exception. New transport.
		connected = Connected(request, opened_ipp=opened_ipp, opened_at=world_now())

		selector.connected = connected
		transport, proxy_address = open_stream(self, selector, client, connected)
		connected.proxy_address = proxy_address

		self.trace(f'Connected to "{requested_ipp}", at local address "{opened_ipp}"')

		if selector.encrypted():
			self.trace(f'Connected (encrypted) to "{requested_ipp}", at local address "{opened_ipp}"')
			not_connected = NotConnected(request, None, None)
			transport.diffie_hellman = (
				(connected, transport.controller_address, transport.proxy_address),
				(not_connected, selector.controller_address))
			self.send(Diffie(), proxy_address)
			return
		self.trace(f'Connected to "{requested_ipp}", at local address "{opened_ipp}"')

		self.forward(connected, transport.controller_address, transport.proxy_address)

		if not scrap:
			return

		try:
			transport.receive_a_message(scrap, self)
		except (CodecError, OverflowError, ValueError) as e:
			self.warning(f'cannot receive_a_message ({e})')
			c = Close(value=None, reason=EndOfTransport.INBOUND_STREAMING, note=str(e))
			close_by_socket(transport, c, s)
		return

	except socket.error as e:
		self.send(NotConnected(request, e.errno, str(e)), selector.controller_address)
		self.clear_out(s, TcpClient)
		return

def TcpClient_ReadyToSend(self, selector, s):
	client = s
	request = selector.request

	hap = client.getsockname()
	opened_ipp = HostPort(hap[0], hap[1])
	requested_ipp = request.requested_ipp

	connected = Connected(request, opened_ipp=opened_ipp, opened_at=world_now())
	selector.connected = connected

	transport, proxy_address = open_stream(self, selector, client, connected)
	connected.proxy_address = proxy_address

	if selector.encrypted():
		self.trace(f'Connected (encrypted) to "{requested_ipp}", at local address "{opened_ipp}"')
		not_connected = NotConnected(request, None, None)
		transport.diffie_hellman = (
			(connected, transport.controller_address, transport.proxy_address),
			(not_connected, selector.controller_address))
		# Start the exchange of public keys.
		self.send(Diffie(), proxy_address)
		return
	self.trace(f'Connected to "{requested_ipp}", at local address "{opened_ipp}"')

	self.forward(connected, transport.controller_address, transport.proxy_address)

def TcpClient_BrokenTransport(self, selector, s):
	request = selector.request
	requested_ipp = request.requested_ipp

	text = 'fault on pending connect, unreachable, no service at that address or blocked'
	self.send(NotConnected(request, 0, text), selector.controller_address)
	self.clear_out(s, TcpClient)

#
def close_by_socket(transport, close, s):
	transport.closing = close
	s.shutdown(SHUT_SOCKET)

def clear_out_session(self, transport, s, reason=None, note=None, error_code=None):
	ipp = transport.opened.opened_ipp

	if transport.closing:
		close = transport.closing
		c = Closed(value=close.value,
			reason=close.reason,
			note=close.note,
			error_code=close.error_code,
			opened_ipp=ipp,
			opened_at=transport.opened.opened_at)
	else:
		self.send(Stop(), transport.proxy_address)
		c = Closed(value=None,
			reason=reason,
			note=note,
			error_code=error_code,
			opened_ipp=ipp,
			opened_at=transport.opened.opened_at)

	self.forward(c, transport.controller_address, transport.proxy_address)
	self.clear_out(s, TcpTransport)

def TcpTransport_ReadyToSend(self, transport, s):
	try:
		if transport.send_a_block(s):
			return
	except (CodecError, OverflowError, ValueError) as e:
		self.warning(f'cannot send_a_block ({e})')
		c = Close(value=None, reason=EndOfTransport.OUTBOUND_STREAMING, note=str(e))
		close_by_socket(transport, c, s)
		return

	# Had nothing to send.
	try:
		self.sending.remove(s)
	except ValueError:
		pass

# A network transport for the purpose of exchanging
# messages between machines.

def TcpTransport_ReceiveBlock(self, transport, s):
	try:
		scrap = s.recv(TCP_RECV)
		if not scrap:
			clear_out_session(self, transport, s, reason=EndOfTransport.ABANDONED_BY_REMOTE)
			return

		try:
			transport.receive_a_message(scrap, self)
		except (CodecError, OverflowError, ValueError) as e:
			self.warning(f'Cannot receive_a_message ({e})')
			c = Close(value=None, reason=EndOfTransport.INBOUND_STREAMING, note=str(e))
			close_by_socket(transport, c, s)
		return

	except socket.error as e:
		# if e.errno == errno.ECONNREFUSED:
		#	self.warning('Connection refused')
		# elif e.errno not in SOCKET_DOWN:
		#	self.fault(f'Socket termination ({e})')
		clear_out_session(self, transport, s, reason=EndOfTransport.INBOUND_STREAMING, note=str(e), error_code=e.errno)
		return

def TcpTransport_BrokenTransport(self, selector, s):
	clear_out_session(self, selector, s, reason=EndOfTransport.INBOUND_STREAMING, note='broken transport')

#
def control_channel():
	'''Create a listen-connect pair for control channel to engine.'''
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.setblocking(False)
	server.bind(("127.0.0.1", 0))
	server.listen(1)

	server_address = server.getsockname()

	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.setblocking(False)
	e = client.connect_ex(server_address)

	readable, writable, exceptional = select.select([server], [], [server])
	if not readable:
		client.close()
		server.close()
		raise RuntimeError('Forming control channel, select has not received connect notification.')

	accepted, client_address = server.accept()
	accepted.setblocking(False)

	accept_address = accepted.getsockname()

	return server, accepted, client

def control_close(lac):
	# Close the listen and the connect. Accepted
	# will be closed by ListenConnect.
	lac[2].close()
	lac[0].close()

#
#
BUMP = b'X'

class SocketChannel(object):
	def __init__(self, pending=None, client=None):
		'''
		This is the per-object client end of the control
		channel into the network I/O loop.
		'''
		self.pending = pending
		self.client = client

	def send(self, message, address):
		self.pending.put((message, address))
		buffered = self.client.send(BUMP)
		if buffered != 1:
			raise RuntimeError('Control channel not accepting commands.')

# Damn. Sent from sockets thread to creator. They
# need it to inject messages into loop.
bind(SocketChannel, not_portable=True, copy_before_sending=False)

#
SELECT_TABLE = {
	# Handling of inbound control messages.
	(ControlChannel, ReceiveBlock):	 	ControlChannel_ReceiveBlock,		# Signals down the control channel.
	(ControlChannel, BrokenTransport):  ControlChannel_BrokenTransport,

	# Made to look as if the select thread can actually receive
	# sockets signals and application messages. Called from above.
	(ControlChannel, ListenForStream):	ControlChannel_ListenForStream,		# Process signals to sockets.
	(ControlChannel, ConnectStream):	ControlChannel_ConnectStream,
	(ControlChannel, Shutdown):		 	ControlChannel_Shutdown,
	(ControlChannel, Bump):			 	ControlChannel_Bump,
	(ControlChannel, StopListening):	ControlChannel_StopListening,
	(ControlChannel, Stop):		  		ControlChannel_Stop,

	# Operational sockets
	(TcpServer,	ReceiveBlock):	   		TcpServer_ReceiveBlock,			# Accept inbound connections.
	(TcpServer,	BrokenTransport):		TcpServer_BrokenTransport,

	(TcpClient, ReceiveBlock):			TcpClient_ReceiveBlock,			# Deferred connections.
	(TcpClient, ReadyToSend):		 	TcpClient_ReadyToSend,
	(TcpClient, BrokenTransport):	 	TcpClient_BrokenTransport,

	(TcpTransport, ReceiveBlock):		TcpTransport_ReceiveBlock,
	(TcpTransport, ReadyToSend):		TcpTransport_ReadyToSend,
	(TcpTransport, BrokenTransport):	TcpTransport_BrokenTransport,
}

class ListenConnect(Threaded, Stateless):
	def __init__(self):
		Threaded.__init__(self)
		Stateless.__init__(self)

		# Construct the control channel and access object.
		self.pending = queue.Queue()
		self.lac = control_channel()
		self.channel = SocketChannel(self.pending, self.lac[2])

		# Load control details into socket tables.
		self.listening = self.lac[0]
		self.accepted = self.lac[1]
		self.networking = {
			self.accepted: ControlChannel(self.accepted),	# Receives 1-byte BUMPs.
		}

		# Active socket lists for select.
		self.receiving = [self.accepted]
		self.sending = []
		self.faulting = self.receiving + self.sending

		self.lid = {}

		# Live.
		self.running = True

	def clear_out(self, s, expected=None):
		# Remove the specified socket from operations.
		try:
			t = self.networking[s]
		except KeyError:
			self.warning('Attempt to remove unknown socket')
			return None

		if expected and not isinstance(t, expected):
			self.warning(f'unexpected networking object {t} (expecting {expected})')
			return None

		def find():
			for lid, server in self.lid.items():
				if server == s:
					return lid
			return None
		f = find()
		if f is not None:
			del self.lid[f]

		del self.networking[s]
		try:
			self.receiving.remove(s)
		except ValueError:
			pass
		try:
			self.sending.remove(s)
		except ValueError:
			pass
		try:
			self.faulting.remove(s)
		except ValueError:
			pass
		s.close()
		return t

def ListenConnect_Start(self, message):
	# Provide channel details to parent for access
	# by application.
	self.send(self.channel, self.parent_address)

	while self.running or len(self.networking) > 1:
		R, S, F = select.select(self.receiving, self.sending, self.faulting)

		for r in R:
			try:
				a = self.networking[r]
				c = a.__class__
				j = SELECT_TABLE[(c, ReceiveBlock)]
			except KeyError:
				continue
			except ValueError:
				continue
			j(self, a, r)

		for s in S:
			try:
				a = self.networking[s]
				c = a.__class__
				j = SELECT_TABLE[(c, ReadyToSend)]
			except KeyError:
				continue
			except ValueError:
				continue
			j(self, a, s)

		for f in F:
			try:
				a = self.networking[f]
				c = a.__class__
				j = SELECT_TABLE[(c, BrokenTransport)]
			except KeyError:
				continue
			except ValueError:
				continue
			j(self, a, f)

	control_close(self.lac)
	self.complete(Ack())

bind(ListenConnect, (Start,))

# Managed creation of socket engine.
def create_sockets(root):
	TS.sockets = root.create(ListenConnect)
	m, i = root.select(SocketChannel)
	TS.channel = m

def stop_sockets(root):
	TS.channel.send(Stop(), root.object_address)
	root.select()

AddOn(create_sockets, stop_sockets)

# Interface to the engine.
def listen(self, requested_ipp: HostPort, encrypted: bool=False,
			http_server: list[Type]=None, default_to_request: bool=True, ansar_client: bool=False):
	"""
	Establishes a network presence at the specified IP
	address and port number. Returns UUID.

	:param self: asynchronous identity
	:type self: :class:`~.Point`
	:param requested_ipp: network address to listen at
	:type requested_ipp: HostPort
	:param encrypted: enable encryption
	:type encrypted: bool
	:param http_server: enable HTTP with list of expected requests
	:type http_server: list
	:param default_to_request: enable default conversion into HttpRequests
	:type default_to_request: bool
	:param ansar_client: enable layer cake json
	:type ansar_client: bool
	:rtype: UUID
	"""
	lid = uuid.uuid4()
	ls = ListenForStream(lid=lid, requested_ipp=requested_ipp, encrypted=encrypted, http_server=http_server, default_to_request=default_to_request, ansar_client=ansar_client)
	TS.channel.send(ls, self.object_address)
	return lid

def connect(self, requested_ipp, encrypted: bool=False, self_checking: bool=False,
			http_client: str=None, layer_cake_json: bool=False):
	"""
	Initiates a network connection to the specified IP
	address and port number.

	:param self: asynchronous identity
	:type self: :class:`~.Point`
	:param requested_ipp: host and port to connect to
	:type requested_ipp: :class:`~.HostPort`
	:param encrypted: enable encryption
	:type encrypted: bool
	:param self_checking: enable keep-alives
	:type self_checking: bool
	:param http_client: leading part of the outgoing request URI
	:type http_client: str
	:param layer_cake_json: is the remote server ansar-enabled
	:type layer_cake_json: bool
	"""
	cs = ConnectStream(requested_ipp=requested_ipp, encrypted=encrypted, self_checking=self_checking, http_client=http_client, layer_cake_json=layer_cake_json)
	TS.channel.send(cs, self.object_address)

def stop_listening(self, lid):
	"""
	Shutdown the listen port with the specified identity.

	:param self: asynchronous identity
	:type self: :class:`~.Point`
	:param lid: UUID assigned at time of :func:`~.listen`
	:type lid: UUID
	:rtype: None
	"""
	TS.channel.send(StopListening(lid), self.object_address)
