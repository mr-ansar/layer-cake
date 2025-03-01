#
#
import os
import time
import datetime
import pytz
import pytz.exceptions
from unittest import TestCase
import layer_cake as lc
from dateutil.tz import gettz


__all__ = [
	'TestConvertMemory',
]


class TestConvertMemory(TestCase):
	def test_clock(self):
		# Make use of the now/at/span/break family
		# of functions provided for the ClockTime
		# type.
		a = lc.clock_now()
		b = lc.clock_at(1963, 3, 26)
		c = lc.clock_span(days=365)
		d = a - b
		y = int(d / c)

		assert a > b
		assert lc.clock_break(b)[0] == 1963
		assert y >= 58

		e = lc.clock_span(hours=1, minutes=12, seconds=5, milliseconds=2, microseconds=3)
		e = e * 3
		f = b + e

		g = lc.clock_break(f)

		assert g[0] == 1963 and g[1] == 3 and g[2] == 26
		assert g[3] == 3 and g[4] == 36
		assert g[5] == 16	   # Rounds second up to next int? nb: f is negative.
		assert g[6] == 1

		a = lc.clock_at(1963, 3, 26)
		t = time.ctime(a)

		assert t.find('Tue') != -1 and t.find('Mar') != -1
		assert t.find('26') != -1 and t.find('1963') != -1

	def test_world(self):
		# Make use of the now/at/delta/break family
		# of functions provided for the WorldTime
		# type.
		a = lc.world_now()
		b = lc.world_at(1963, 3, 26)
		c = lc.world_delta(days=365)
		d = a - b
		y = int(d / c)

		assert a > b
		assert lc.world_break(b)[0] == 1963
		assert b.year == 1963
		assert y >= 58

		e = lc.world_delta(hours=1, minutes=12, seconds=5, milliseconds=2, microseconds=3)
		e = e * 3
		f = b + e

		g = lc.world_break(f)

		assert g[0] == 1963 and g[1] == 3 and g[2] == 26
		assert g[3] == 3 and g[4] == 36
		assert g[5] == 15
		assert g[6] == 6009	 # 2 * 3 .. 3 * 3, sorta.

	def test_clock_trip(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		t = time.time()
		t = int(t)
		d = float(t)
		s = lc.clock_to_text(d)
		r = lc.text_to_clock(s)
		assert r == t

	def test_clock_variants(self):
		d = lc.text_to_clock('2021-07-01T03:02:01.0')

		v = ['2021-7-01T03:02:01.0',
			'2021-07-1T03:02:01.0',
			'2021-7-1T03:02:01.0',

			'2021-07-01T3:02:01.0',
			'2021-07-01T03:2:01.0',
			'2021-07-01T03:02:1.0',
			'2021-07-01T3:02:1.0',
			'2021-07-01T3:2:01.0',
			'2021-07-01T03:2:1.0',
			'2021-07-01T03:02:01'
		]
		for s in v:
			r = lc.text_to_clock(s)
			assert r == d

	def test_clock_encoding(self):
		d = -1.0
		try:
			s = lc.clock_to_text(d)
			assert False
		except lc.ConversionEncodeError as e:
			t = str(e)
			assert t.find('cannot represent') != -1

	def test_clock_decoding(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		s = 'no-such-clock'
		try:
			d = lc.text_to_world(s)
			assert False
		except lc.ConversionDecodeError as e:
			t = str(e)
			assert t.find('cannot recover') != -1

	def test_span_trip(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		d = lc.clock_span(3, 2, 1, 10)
		s = lc.span_to_text(d)
		r = lc.text_to_span(s)
		assert r == d

	def test_span_various(self):
		v = [
			['7d', lc.clock_span(days=7)],
			['5h', lc.clock_span(hours=5)],
			['3m', lc.clock_span(minutes=3)],
			['1s', lc.clock_span(seconds=1)],
			['0.1s', lc.clock_span(seconds=0, milliseconds=100)],
			['7d6m', lc.clock_span(minutes=6, days=7)],
			['7d1s', lc.clock_span(seconds=1, days=7)],
			['7d0.1s', lc.clock_span(seconds=0, milliseconds=100, days=7)],
			['5h3m', lc.clock_span(hours=5, minutes=3)],
			['5h1s', lc.clock_span(hours=5, seconds=1)],
			['5h0.1s', lc.clock_span(hours=5, seconds=0, milliseconds=100)],
			['1s', lc.clock_span(seconds=1)],
			['0.1s', lc.clock_span(seconds=0, milliseconds=100)],
		]
		for s, d in v:
			r = lc.text_to_span(s)
			assert r == d

	def test_span_small(self):
		v = [
			['0.0s', lc.clock_span()],
			['0.1s', lc.clock_span(seconds=0, milliseconds=100)],
			['0.001s', lc.clock_span(milliseconds=1)],
			['0.01s', lc.clock_span(milliseconds=10)],
			['0.1s', lc.clock_span(milliseconds=100)],
			['0.000001s', lc.clock_span(microseconds=1)],
			['0.00001s', lc.clock_span(microseconds=10)],
			['0.0001s', lc.clock_span(microseconds=100)],
			['0.001s', lc.clock_span(microseconds=1000)],
			['0.01s', lc.clock_span(microseconds=10000)],
			['0.1s', lc.clock_span(microseconds=100000)],
			['0.000010s', lc.clock_span(microseconds=10)],
			['0.000100s', lc.clock_span(microseconds=100)],
			['0.001000s', lc.clock_span(microseconds=1000)],
			['0.010000s', lc.clock_span(microseconds=10000)],
			['0.100000s', lc.clock_span(microseconds=100000)],
		]
		for s, d in v:
			r = lc.text_to_span(s)
			assert r == d

	def test_span_negative(self):
		v = [
			['-7d', -lc.clock_span(days=7)],
			['-5h', -lc.clock_span(hours=5)],
			['-3m', -lc.clock_span(minutes=3)],
			['-1s', -lc.clock_span(seconds=1)],
			['-0.1s', -lc.clock_span(seconds=0, milliseconds=100)],
			['-7d6m', -lc.clock_span(minutes=6, days=7)],
			['-7d1s', -lc.clock_span(seconds=1, days=7)],
			['-7d0.1s', -lc.clock_span(seconds=0, milliseconds=100, days=7)],
			['-5h3m', -lc.clock_span(hours=5, minutes=3)],
			['-5h1s', -lc.clock_span(hours=5, seconds=1)],
			['-5h0.1s', -lc.clock_span(hours=5, seconds=0, milliseconds=100)],
			['-1s', -lc.clock_span(seconds=1)],
			['-0.1s', -lc.clock_span(seconds=0, milliseconds=100)],
		]
		for s, d in v:
			r = lc.text_to_span(s)
			assert r == d

	def test_span_decoding(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		d = 'no-such-span'
		try:
			s = lc.text_to_span(d)
			assert False
		except lc.ConversionDecodeError as e:
			t = str(e)
			assert t.find('cannot recover') != -1

	def test_span_empty(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		s = ''
		try:
			r = lc.text_to_span(s)
			assert False
		except lc.ConversionDecodeError as e:
			t = str(e)
			assert t.find('cannot recover') != -1

	def test_world_trip(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		d = datetime.datetime.now(lc.UTC)
		s = lc.world_to_text(d)
		r = lc.text_to_world(s)
		assert r == d

	# '^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})T([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})(\.[0-9]+)?Z?$'
	# 2021-07-01T13:14:15.123
	def test_world_variants(self):
		d = lc.text_to_world('2021-07-01T03:02:01.0')

		v = ['2021-7-01T03:02:01.0',
			'2021-07-1T03:02:01.0',
			'2021-7-1T03:02:01.0',

			'2021-07-01T3:02:01.0',
			'2021-07-01T03:2:01.0',
			'2021-07-01T03:02:1.0',
			'2021-07-01T3:02:1.0',
			'2021-07-01T3:2:01.0',
			'2021-07-01T03:2:1.0',
			'2021-07-01T03:02:01'
		]
		for s in v:
			r = lc.text_to_world(s)
			assert r == d

	# Tried to create an invalid dt so that an exception
	# could be generated by encoder but ctor for datetime
	# seems to do complete validation.
	def test_world_encoding(self):
		pob = pytz.timezone('Pacific/Auckland')
		try:
			dob = datetime.datetime(year=1963, month=3, day=26,
				hour=10, minute=0, second=0,
				microsecond=1000000,
				tzinfo=pob)
		except ValueError as e:
			d = str(e)
			assert d.find('microsecond must') != -1

	def test_world_decoding(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		s = 'no-such-moment'
		try:
			s = lc.text_to_world(s)
			assert False
		except lc.ConversionDecodeError as e:
			d = str(e)
			assert d.find('cannot recover') != -1

	def test_delta_trip(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		d = datetime.timedelta(days=1, hours=2, minutes=3, seconds=4)
		s = lc.delta_to_text(d)
		r = lc.text_to_delta(s)
		assert r == d

	def test_delta_various(self):
		v = [
			['7:00:00:00', datetime.timedelta(days=7)],
			['5:00:00', datetime.timedelta(hours=5)],
			['0:03:00', datetime.timedelta(minutes=3)],
			['0:00:01', datetime.timedelta(seconds=1)],
			['0:00:0.1', datetime.timedelta(microseconds=100000)],
			['7:00:06:00', datetime.timedelta(days=7, minutes=6)],
			['7:00:00:01', datetime.timedelta(days=7, seconds=1)],
			['7:00:00:0.1', datetime.timedelta(days=7, microseconds=100000)],
			['5:00:03', datetime.timedelta(hours=5, seconds=3)],
			['5:00:01', datetime.timedelta(hours=5, seconds=1)],
			['5:00:0.1', datetime.timedelta(hours=5, microseconds=100000)],
			['0:00:01', datetime.timedelta(seconds=1)],
			['0:00:0.1', datetime.timedelta(microseconds=100000)],
		]
		for s, d in v:
			r = lc.text_to_delta(s)
			assert r == d

	def test_delta_negative(self):
		v = [
			['-7:00:00:00', datetime.timedelta(days=-7)],
			['-5:00:00', datetime.timedelta(hours=-5)],
			['-0:03:00', datetime.timedelta(minutes=-3)],
			['-0:00:01', datetime.timedelta(seconds=-1)],
			['-0:00:0.1', datetime.timedelta(microseconds=-100000)],
			['-7:00:06:00', datetime.timedelta(days=-7, minutes=-6)],
			['-7:00:00:01', datetime.timedelta(days=-7, seconds=-1)],
			['-7:00:00:0.1', datetime.timedelta(days=-7, microseconds=-100000)],
			['-5:00:03', datetime.timedelta(hours=-5, seconds=-3)],
			['-5:00:01', datetime.timedelta(hours=-5, seconds=-1)],
			['-5:00:0.1', datetime.timedelta(hours=-5, microseconds=-100000)],
			['-0:00:01', datetime.timedelta(seconds=-1)],
			['-0:00:0.1', datetime.timedelta(microseconds=-100000)],
		]
		for s, d in v:
			r = lc.text_to_delta(s)
			assert r == d

	def test_delta_decoding(self):
		# Use the current time but
		# round it cos fractional part
		# doesnt recover well.
		s = 'no-such-span'
		try:
			s = lc.text_to_delta(s)
			assert False
		except lc.ConversionDecodeError as e:
			d = str(e)
			assert d.find('cannot recover') != -1

	def test_clock_dst(self):
		# Ended 2021-04-04 at 3am.
		# Select the hour before and step up
		# through the changeover.
		a = lc.clock_at(2021, 4, 4, 1, 0, 0)
		p = lc.clock_span(hours=1)
		t = a

		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 1 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 2 and b[4] == 0 and b[5] == 0

		# Increment another hour but the rendered hour
		# stays the same - clocks wound back.
		t += p
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 2 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 3 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 4 and b[4] == 0 and b[5] == 0

		# Now do the same thing but spanning the
		# start of daylight saving.
		# 2021-09-26 at 2am.
		a = lc.clock_at(2021, 9, 26, 1, 0, 0)
		p = lc.clock_span(hours=1)
		t = a

		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 9  and b[2] == 26
		assert b[3] == 1 and b[4] == 0 and b[5] == 0

		# The hour rolls forward from 1 to 3 cos 2am
		# never happens at the start of daylight savings.
		t += p
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 9  and b[2] == 26
		assert b[3] == 3 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 9  and b[2] == 26
		assert b[3] == 4 and b[4] == 0 and b[5] == 0

	def test_world_dst(self):
		# Note
		# Cant do dst test involving world times now that the
		# concept has been defined to be "datetime.timezone"
		# values only. Left in cos it was so much work to get
		# right.
		return
		# Ended 2021-04-04 at 3am.
		# Select a wee bit past the hour and step up
		# through the changeover.
		# Forced to use direct ctor cos world_at returns
		# a UTC-based object.
		z = gettz('Pacific/Auckland')
		a = lc.world_at(2021, 4, 4, tz=z)
		p = lc.world_delta(hours=1)
		t = a

		b = lc.world_break(t, z)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 0 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.world_break(t, z)
		assert b[3] == 1 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.world_break(t, z)
		assert b[3] == 2 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.world_break(t, z)
		assert b[3] == 2 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.world_break(t, z)
		assert b[3] == 3 and b[4] == 0 and b[5] == 0

		# Now do the same thing but spanning the
		# start of daylight saving.
		# 2021-09-26 at 2am.
		a = lc.world_at(2021, 9, 26, tz=z)
		p = lc.world_delta(hours=1)
		t = a

		b = lc.world_break(t, z)
		assert b[0] == 2021 and b[1] == 9  and b[2] == 26
		assert b[3] == 0 and b[4] == 0 and b[5] == 0

		# The hour rolls forward from 1 to 3 cos 2am
		# never happens at the start of daylight savings.
		t += p
		b = lc.world_break(t, z)
		assert b[3] == 1 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.world_break(t, z)
		assert b[3] == 3 and b[4] == 0 and b[5] == 0

		t += p
		b = lc.world_break(t, z)
		assert b[3] == 4 and b[4] == 0 and b[5] == 0

	def test_clock_longer_day(self):
		# Ended 2021-04-04 at 3am.
		# Select a wee bit past the hour and step up
		# past the end-of-day.
		a = lc.clock_at(2021, 4, 4, 1, 0, 0)
		p = lc.clock_span(hours=1)
		t = a

		t += p * 10 # Ten hours forward should be 11am.
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 10 and b[4] == 0 and b[5] == 0

	def test_world_timestamp(self):
		# Ended 2021-04-04 at 3am.
		# Select a wee bit past the hour and step up
		# past the end-of-day.
		# a = datetime.datetime(2021, 4, 4, 2, 40, 0, microseconds=200000)
		a = lc.clock_at(2021, 4, 4, 2, 40, 0, 200)
		p = lc.clock_span(minutes=10)
		t = a

		t += p
		d1 = datetime.datetime.fromtimestamp(t)
		f = d1.fold
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 2 and b[4] == 50 and b[5] == 0
		assert b[6] == 6

		t += p
		d2 = datetime.datetime.fromtimestamp(t)
		f = d2.fold
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 3 and b[4] == 0 and b[5] == 0
		assert b[6] == 6

		t += p
		d3 = datetime.datetime.fromtimestamp(t)
		f = d3.fold
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 3 and b[4] == 10 and b[5] == 0
		assert b[6] == 6

		t += p
		d4 = datetime.datetime.fromtimestamp(t)
		f = d4.fold
		b = lc.clock_break(t)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 3 and b[4] == 20 and b[5] == 0
		assert b[6] == 6

	def test_world_wtf(self):
		# Note. WorldTime has moved to datetime.timezone only.
		return
		z = gettz('Pacific/Auckland')
		a = lc.world_at(2021, 4, 4, tz=z)
		b = lc.world_break(a, z)
		assert b[0] == 2021 and b[1] == 4  and b[2] == 4
		assert b[3] == 0 and b[4] == 0 and b[5] == 0

	def test_world_pytz(self):
		# Note. WorldTime has moved to datetime.timezone only.
		return
		g = pytz.timezone('UTC')
		z = pytz.timezone('Pacific/Auckland')
		a = datetime.datetime(2021, 4, 4, tzinfo=z)
		b = a.astimezone(g)
		c = b.astimezone(z)

		# After a simple round-trip the output is
		# NOT the same as the input. FAIL.
		assert c.year == 2021 and c.month == 4  and c.day == 4
		assert c.hour == 1 and c.minute == 21

	def test_world_dateutil(self):
		g = gettz('UTC')
		z = gettz('Pacific/Auckland')
		s = z._filename
		i = s.find('zoneinfo/')
		name = s[i + 9:]
		a = datetime.datetime(2021, 4, 4, tzinfo=z)
		b = a.astimezone(g)
		c = b.astimezone(z)

		# After a simple round-trip the output is
		# the SAME as the input. SUCCESS.
		assert c.year == 2021 and c.month == 4  and c.day == 4
		assert c.hour == 0 and c.hour == 0
