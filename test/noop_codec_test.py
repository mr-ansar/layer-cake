# codec_test.py
# Verify the transformations between application data and
# encoder-ready state (and the reverse). This is purely about
# reworking of Python data so that encoding/decoding (say
# in json) proceeds without problems. Encoder-ready data has
# detail like classes and python dicts stripped out.
from unittest import TestCase
from test_message import *

import uuid
import layer_cake as lc
from layer_cake.noop_codec import CodecNoop

__all__ = [
	'TestCodecNoop',
]

class TestCodecNoop(TestCase):
	def test_codec(self):
		c = CodecNoop()

		# Generate the shipment. Recover the boolean.
		s = c.encode(True, lc.Boolean())
		b = c.decode(s, lc.Boolean())

		assert b == True

		s = c.encode(False, lc.Boolean())
		b = c.decode(s, lc.Boolean())

		assert b == False

	def test_auto_schema(self):
		art = AutoTypes.__art__
		schema = art.schema

		assert isinstance(schema['a'], lc.Boolean)
		assert isinstance(schema['b'], lc.Integer8)
		assert isinstance(schema['c'], lc.Float8)
		assert isinstance(schema['d'], lc.Block)
		assert isinstance(schema['e'], lc.String)
		assert isinstance(schema['f'], lc.Unicode)
		assert isinstance(schema['g'], lc.UUID)

	def test_auto_init(self):
		a = AutoTypes()

		assert isinstance(a.a, bool)
		assert isinstance(a.b, int)
		assert isinstance(a.c, float)
		assert isinstance(a.d, bytearray)
		assert isinstance(a.e, bytes)
		assert isinstance(a.f, str)
		assert isinstance(a.g, uuid.UUID)

	def test_auto(self):
		assert encode_decode(CodecNoop(), AutoTypes)

	def test_encode_failed(self):
		c = CodecNoop()
		t = lc.UserDefined(AutoTypes)
		r = lc.make(t)
		r.f = AutoTypes		 # CLOBBER

		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecError as e:
			assert e.note.find('near "f"') != -1
			assert e.note.find('type/Unicode') != -1

	def test_decode_failed(self):
		c = CodecNoop()
		t = lc.UserDefined(AutoTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		s = c.encode(r, t)

		# CLOBBER
		s['value']['f'] = AutoTypes
		try:
			s = c.decode(s, t)
			assert False
		except lc.CodecError as e:
			assert e.note.find('near "f"') != -1
			assert e.note.find('type/Unicode') != -1

	def test_decode_unkown_member(self):
		c = CodecNoop()
		t = lc.UserDefined(AutoTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		s = c.encode(r, t)

		# CLOBBER
		s['value']['extraneous'] = 8	# Ignored.
		try:
			s = c.decode(s, t)
			assert True
		except lc.CodecError as e:
			assert False

	def test_encode_pointer(self):
		c = CodecNoop()
		t = lc.UserDefined(PointerTypes)
		r = PointerTypes()

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			assert False

		try:
			s = c.decode(s, t)
			assert True
		except lc.CodecError as e:
			assert False

	def test_encode_space_pointer(self):
		c = CodecNoop()
		t = lc.UserDefined(PointerTypes)
		r = PointerTypes()

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		space = []
		try:
			s = c.encode(r, t, space=space)
		except lc.CodecError as e:
			assert False

		try:
			s = c.decode(s, t, space)
			assert True
		except lc.CodecError as e:
			assert False

	def test_encode_space_address(self):
		c = CodecNoop()
		t = lc.UserDefined(SpecialTypes)
		r = SpecialTypes()

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		space = []
		try:
			s = c.encode(r, t, space=space)
		except lc.CodecError as e:
			assert False

		try:
			s = c.decode(s, t, space)
			assert True
		except lc.CodecError as e:
			assert False

	def test_nested_link(self):
		c = CodecNoop()
		t = lc.UserDefined(PointerTypes)
		r = PointerTypes()

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			assert False

		s['pointer'][5][1]['next'] = 'no such reference'
		try:
			s = c.decode(s, t)
			assert False
		except lc.CodecError as e:
			assert True

	def test_nested_array(self):
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = ContainerTypes()

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			assert False

		s['value']['g'][3][3] = 0.125
		try:
			s = c.decode(s, t)
			assert False
		except lc.CodecError as e:
			assert True

	def test_plain(self):
		assert encode_decode(CodecNoop(), PlainTypes)

	def test_container(self):
		assert encode_decode(CodecNoop(), ContainerTypes)

	def test_special(self):
		c = CodecNoop(return_proxy=(9,))
		t = lc.UserDefined(SpecialTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Recover the application data from the given
		# shipment.
		try:
			b = c.decode(s, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		assert b.b == (3, 5)		# Loses the 7.
		assert b.c == (2, 4, 6, 9)  # Acquires the 9.

		b.b = (3, 5, 7)	 # Restore for comparison of others.
		b.c = (2, 4, 6)

		assert lc.equal_to(b, r)

	def test_time(self):
		assert encode_decode(CodecNoop(), TimeTypes)

	def test_time_encoding(self):
		c = CodecNoop()
		t = lc.UserDefined(TimeTypes)
		r = lc.make(t)

		# Set invalid data.
		r.a = -1.0
		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecError as e:
			print(e.note)
			assert e.note.find('cannot represent -1') != -1

	def test_time_decoding(self):
		c = CodecNoop()
		t = lc.UserDefined(TimeTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Fiddle with the representation.
		s['value']['c'] = s['value']['c'].replace('+0100', '+no-such-zone')
		try:
			b = c.decode(s, t)
			assert False
		except lc.CodecError as e:
			s = str(e)
			print(s)
			assert s.find('cannot recover WorldTime') != -1

	def test_pointer(self):
		c = CodecNoop()
		t = lc.UserDefined(PointerTypes)
		r = lc.make(t)

		# Generate the shipment, i.e. a value, an optional
		# version tag and an optional dict of pointer values.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Recover the application data from the given
		# shipment.
		try:
			b = c.decode(s, t)
		except lc.CodecError as e:
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

	def test_enumeration_pass(self):
		c = CodecNoop()
		t = lc.UserDefined(PlainTypes)
		plain = PlainTypes()

		plain.p = MACHINE_STATE.INITIAL
		try:
			s = c.encode(plain, t)
			pass
		except lc.CodecError as e:
			assert False

		assert s['value']['p'] == 'INITIAL'

		s['value']['p'] = 'RUBBISH'
		try:
			v = c.decode(s, t)
			assert False
		except lc.CodecError as e:
			assert e.note.find('near "p"') != -1
			assert e.note.find('no number for "RUBBISH"') != -1

	def test_array_misfit_short(self):
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		s = c.encode(r, t)

		# CLOBBER
		s['value']['a'] = [''] * 7
		try:
			r = c.decode(s, t)
		except lc.CodecError as e:
			assert False

		assert len(r.a) == 8
		assert isinstance(r.a[7], type(None))

	def test_array_misfit_long(self):
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		s = c.encode(r, t)

		# CLOBBER
		s['value']['a'] = [''] * 9
		try:
			r = c.decode(s, t)
		except lc.CodecError as e:
			assert False

		assert len(r.a) == 8

	def test_array_misfit_encode(self):
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		r.a = [bytes()] * 7

		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecError as e:
			assert e.note.find('near "a"') != -1
			assert e.note.find('7/8') != -1

	def test_not_trombone(self):
		x = CodecNoop(return_proxy=(26,))
		y = CodecNoop(return_proxy=(32,))
		t = lc.UserDefined(SpecialTypes)
		r = lc.make(t)

		try:
			s = x.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Target address "b" moves onto the wire unchanged.
		# Usable address "c" is checked for tromboning and
		# its not - so also unchanged.
		assert s['value']['b'] == [3, 5, 7]
		assert s['value']['c'] == [2, 4, 6]

		try:
			b = y.decode(s, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Target address reduces by 1, i.e. the address of the remote
		# proxy is not relevant here and is shaved off.
		# Address grows by one, i.e. the address of the local
		# proxy that the message arrived on
		assert b.b == (3, 5)
		assert b.c == (2, 4, 6, 32)

	def test_trombone(self):
		x = CodecNoop(return_proxy=(6,))	# Remote client.
		y = CodecNoop(return_proxy=(9,))	# Local service.
		t = lc.UserDefined(SpecialTypes)
		r = lc.make(t)

		try:
			s = x.encode(r, t)		  # Ready for transfer over connection.
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Target address "b" moves onto the wire unchanged.
		# Usable address "c" has the 6 replaced with a 0 because
		# it matched the remote, client proxy, i.e. the 6 was
		# added on arrival in the client. The local service can
		# just forget the round trip ever happened, i.e. during
		# decode it will nip off the 0.
		assert s['value']['b'] == [3, 5, 7]
		assert s['value']['c'] == [2, 4, 0]

		try:
			b = y.decode(s, t)
		except lc.CodecError as e:
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
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		# Incognito only happens in the context of Any, i.e. when
		# reading an Any type there is the potential to receive
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
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Handcraft an Incognito.
		tn = lc.type_to_text(lc.UserDefined(ContainerTypes))
		dw = s['value']
		io = lc.Incognito(type_name=tn,decoded_word=dw)

		# Encoding an incognito should produce
		# an unfolded shipment. Note the use of the
		# Any type rather than UserDefined(ContainerTypes).
		try:
			s = c.encode(io, lc.Any())
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Normal decoding of a ContainerType in an
		# Any context.
		try:
			b = c.decode(s, lc.Any())
		except lc.CodecError as e:
			print(e.note)
			assert False

		assert lc.equal_to(b, r)

	def test_incognito_decode(self):
		c = CodecNoop()
		t = lc.Any()
		r = ContainerTypes()

		# To simulate creation of an Incognito in the
		# library, first produce a proper shipment.
		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		# Then fiddle the type to be a non-existent,
		# unregistered type.
		no_such_type = 'no.such.type'
		s['value'][0] = no_such_type

		# Put the materials through a decode.
		try:
			b = c.decode(s, lc.Any())
		except lc.CodecError as e:
			print(e.note)
			assert False

		# An Incognito is created inside the library.
		assert isinstance(b, lc.Incognito) and b.type_name == no_such_type

	def test_guaranteed_encode(self):
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)
		r.f = None

		try:
			s = c.encode(r, t)
			assert False
		except lc.CodecError as e:
			assert e.note.find('near "f"') != -1
			assert e.note.find('null value detected for structural') != -1


	def test_guaranteed_decode(self):
		c = CodecNoop()
		t = lc.UserDefined(ContainerTypes)
		r = lc.make(t)

		try:
			s = c.encode(r, t)
		except lc.CodecError as e:
			print(e.note)
			assert False

		s['value']['e'] = None

		try:
			b = c.decode(s, t)
		except lc.CodecError as e:
			assert e.note.find('near "e"') != -1
			assert e.note.find('null value detected for structural') != -1

