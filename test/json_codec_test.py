# json_test.py
# Verify the encode/decode operation of the JSON codec.
import os

from unittest import TestCase
import layer_cake as lc
from layer_cake.noop_codec import CodecNoop
from test_message import *
__all__ = [
	'TestCodecJson',
]

class TestCodecJson(TestCase):
	# Somehow the default history of AutoTypes becomes
	# invalid during an initial bulk "retest". A manual
	# re-execution of each failed test passes. To get the bulk
	# operation going again, need to explicitly set.
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_codec(self):
		c = lc.CodecJson()

		# Simplest possible encode/decode cycle.
		s = c.encode(True, lc.Boolean())
		r = c.decode(s, lc.Boolean())

		assert r == True

	def test_auto(self):
		assert encode_decode(lc.CodecJson(), AutoTypes)

	def test_encode_failed(self):
		c = lc.CodecJson()
		t = lc.UserDefined(AutoTypes)
		r = lc.make(t)
		r.f = AutoTypes		 # CLOBBER

		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecRuntimeError as e:
			assert e.note.find('near "f"') != -1
			assert e.note.find('type/Unicode') != -1

	def test_decode_failed(self):
		c = lc.CodecJson()
		t = lc.UserDefined(AutoTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		s = c.encode(r, t)

		# CLOBBER
		s = s.replace('1.234', '"not-a-float"')
		try:
			s = c.decode(s, t)
			assert False
		except lc.CodecRuntimeError as e:
			assert e.note.find('near "c"') != -1
			assert e.note.find('str/Float8') != -1

	def test_plain(self):
		assert encode_decode(lc.CodecJson(), AutoTypes)

	def test_container(self):
		assert encode_decode(lc.CodecJson(), ContainerTypes)

	def test_special(self):
		c = lc.CodecJson(return_proxy=(9,))
		t = lc.UserDefined(SpecialTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Recover the application data from the given
		# shipment.
		try:
			b = c.decode(s, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		assert b.b == (3, 5)		# Loses the 7.
		assert b.c == (2, 4, 6, 9)  # Acquires the 9.

		b.b = (3, 5, 7)	 # Restore for comparison of others.
		b.c = (2, 4, 6)

		assert lc.equal_to(b, r)

	def test_time(self):
		assert encode_decode(lc.CodecJson(), TimeTypes)

	def test_time_encoding(self):
		c = lc.CodecJson()
		t = lc.UserDefined(TimeTypes)
		r = lc.make(t)

		# Set invalid data.
		r.a = -1.0
		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert e.note.find('cannot represent -1') != -1

	def test_time_decoding(self):
		c = lc.CodecJson()
		t = lc.UserDefined(TimeTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Fiddle with the representation.
		s = s.replace('+0100', '+no-such-zone')
		try:
			b = c.decode(s, t)
			assert False
		except lc.CodecRuntimeError as e:
			s = str(e)
			print(s)
			assert s.find('cannot recover WorldTime') != -1

	def test_pointer(self):
		c = lc.CodecJson()
		t = lc.UserDefined(PointerTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Recover the application data from the given
		# shipment.
		try:
			b = c.decode(s, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		assert lc.equal_to(b.a, r.a, lc.Boolean)
		assert lc.equal_to(b.b, r.b, lc.Boolean)
		# Cant do expected id checks because
		# no-op codec just passes data across.
		# There is no real encode/decode.
		# assert id(b.a) == id(b.b)
		# assert id(r.a) == id(r.b)
		# assert id(b.a) != id(r.a)
		assert lc.equal_to(b.c, r.c, lc.UserDefined(PlainTypes))
		assert isinstance(b.d, Item)
		assert isinstance(b.e, Item)
		assert isinstance(b.f, Cat)
		assert isinstance(b.g, State)

	def test_enumeration_fail(self):
		c = lc.CodecJson()
		t = lc.UserDefined(PlainTypes)
		r = lc.make(t)

		r.p = 0
		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecRuntimeError as e:
			assert e.note.find('near "p"') != -1
			assert e.note.find('int/Enumeration') != -1

	def test_array_misfit_short(self):
		c = lc.CodecJson()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		s = c.encode(r, t)

		# Replace the JSON array of 8 elements with 7.
		s = s.replace('["","","","","","","",""]', '["","","","","","",""]')
		try:
			s = c.decode(s, t)
		except lc.CodecRuntimeError as e:
			assert False
		assert len(s.a) == 8				# Expected length
		assert isinstance(s.a[7], type(None))	# Expected type

	def test_array_misfit_long(self):
		c = lc.CodecJson()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		s = c.encode(r, t)

		# Replace the JSON array of 8 elements with 9.
		s = s.replace('["","","","","","","",""]', '["","","","","","","","",""]')
		try:
			s = c.decode(s, t)
		except lc.CodecRuntimeError as e:
			assert False
		assert len(s.a) == 8	# Expected length.

	def test_array_misfit_encode(self):
		c = lc.CodecJson()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		r.a = [bytes()] * 7

		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecRuntimeError as e:
			assert e.note.find('near "a"') != -1
			assert e.note.find('7/8') != -1

	def test_not_trombone(self):
		x = lc.CodecJson(return_proxy=(26,))
		y = lc.CodecJson(return_proxy=(32,))
		t = lc.UserDefined(SpecialTypes)
		r = lc.make(t)

		try:
			s = x.encode(r, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Target address "b" moves onto the wire unchanged.
		# Usable address "c" is checked for tromboning and
		# its not - so also unchanged.
		assert s.find('"b":[3,5,7]') != -1
		assert s.find('"c":[2,4,6]') != -1

		try:
			b = y.decode(s, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Target address reduces by 1, i.e. the address of the remote
		# proxy is not relevant here and is shaved off.
		# Address grows by one, i.e. the address of the local
		# proxy that the message arrived on
		assert b.b == (3, 5)
		assert b.c == (2, 4, 6, 32)

	def test_trombone(self):
		x = lc.CodecJson(return_proxy=(6,))	# Remote client.
		y = lc.CodecJson(return_proxy=(9,))	# Local service.
		t = lc.UserDefined(SpecialTypes)
		r = lc.make(t)

		try:
			s = x.encode(r, t)		  # Ready for transfer over connection.
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Target address "b" moves onto the wire unchanged.
		# Usable address "c" has the 6 replaced with a 0 because
		# it matched the remote, client proxy, i.e. the 6 was
		# added on arrival in the client. The local service can
		# just forget the round trip ever happened, i.e. during
		# decode it will nip off the 0.
		assert s.find('"b":[3,5,7]') != -1
		assert s.find('"c":[2,4,0]') != -1

		try:
			b = y.decode(s, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Target address loses the 7 because that was the address
		# of the remote proxy - the underlying 5 is relevant to
		# this address space. The usable address has had the 0
		# removed and the adding of the return proxy has been
		# skipped, because this address has just arrived back to
		# where is was sent from.
		assert b.b == (3, 5)	# Lost the 7 as target route consumed as it goes.
		assert b.c == (2, 4)	# Lost the 6 rather than having 9 added.

	def test_incognito_encode(self):
		f = CodecNoop()
		c = lc.CodecJson()
		t = lc.UserDefined(ContainerTypes)
		d = lc.make(t)

		# Incognito only happens in the context of Any, i.e. when
		# reading an Any type there is the potential to receive a
		# an Incognito as a reflection of the local process not
		# having a registration of the object named in the Any
		# tuple. This doesnt happen in the "normal" reading of
		# an object where the expected type is provided by the
		# receiving object.

		# Encoding of Incognitos is about unfolding the type-word
		# tuple to give the chance of the next reader/receiver
		# of decoding in a successful fashion, i.e. a registration
		# is present in the local process.
		# First generate an instance of proper encoding.
		try:
			s = f.encode(d, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Handcraft an Incognito.
		tn = lc.type_to_text(t)
		dw = s['value']
		io = lc.Incognito(type_name=tn,decoded_word=dw)

		# Encoding an incognito should produce
		# an unfolded shipment. Note the use of the
		# Any type rather than UserDefined(ContainerTypes).
		try:
			s = c.encode(io, lc.Any())
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Normal decoding of a ContainerType in an
		# Any context.
		try:
			b = c.decode(s, lc.Any())
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		assert lc.equal_to(b, d)

	def test_incognito_decode(self):
		c = lc.CodecJson()
		t = lc.Any()
		r = ContainerTypes()

		# To simulate creation of an Incognito in the
		# library, first produce a proper shipment.
		try:
			s = c.encode(r, t)
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# Then fiddle the type to be a non-existent,
		# unregistered type.
		no_such_type = 'no-such-type'
		s = s.replace('"test_message.ContainerTypes"', '"%s"' % (no_such_type,))

		# Put the materials through a decode.
		try:
			b = c.decode(s, lc.Any())
		except lc.CodecRuntimeError as e:
			print(e.note)
			assert False

		# An Incognito is created inside the library.
		assert isinstance(b, lc.Incognito) and b.type_name == no_such_type

	def test_code_usage_return(self):
		try:
			c = lc.CodecJson(return_proxy=8)
			assert False
		except lc.CodecUsageError as e:
			assert True

	def test_code_usage_local(self):
		try:
			c = lc.CodecJson(return_proxy=(8,), local_termination=8)
			assert False
		except lc.CodecUsageError as e:
			assert True
