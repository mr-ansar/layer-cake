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

"""Low level conversions, e.g. string to time.

Transformation of application data to a formal text representation according
to an associated :py:mod:`~ansar.encode.portable` type, and back again. These text
fragments become the *on-the-wire* representation for data such as times, that
might otherwise end up as unreadable integer or floating point numbers. These
transformations guarantee correctness of the encode-decode process, i.e. the
original application value will be recovered in the decoding process. System
limitations, such as floating point representation, mean that the guarantee
cannot be extended to related encode-decode processes.
"""

# .. autofunction:: world_to_text
# .. autofunction:: clock_to_text

__docformat__ = 'restructuredtext'

import time
import datetime
from enum import Enum
import re
import uuid

from .virtual_memory import *
from .convert_signature import *
from .convert_type import *

__all__ = [
	'ConversionError',
	'ConversionEncodeError',
	'ConversionDecodeError',

	'clock_to_text',
	'text_to_clock',
	'span_break',
	'span_to_text',
	'text_to_span',
	'UTC',
	'world_to_text',
	'text_to_world',
	'delta_to_text',
	'text_to_delta',
	'uuid_to_text',
	'text_to_uuid',
	'type_to_text',
	'text_to_type',
	'clock_now',
	'clock_at',
	'clock_break',
	'clock_span',
	'world_now',
	'world_at',
	'world_break',
	'world_delta',
]

# Exceptions
#
class ConversionError(Exception):
	"""Base exception for all conversion exceptions."""

class ConversionDecodeError(ConversionError):
	"""Exception raised on failure of one of the :py:mod:`~ansar.encode.convert` decoding functions."""

	def __init__(self, need, text):
		"""Construct the exception.

		:param need: type to be decoded
		:type need: str
		:param need: description of failure
		:type need: str
		"""
		self.need = need
		self.text = text

	def __str__(self):
		"""Auto-convert to str."""
		return 'cannot recover %s from "%s"' % (
			self.need, self.text)

class ConversionEncodeError(ConversionError):
	"""Exception raised on failure of one of the :py:mod:`~ansar.encode.convert` encoding functions."""

	def __init__(self, need, text):
		"""Construct the exception.

		:param need: type to be encoded
		:type need: str
		:param need: description of failure
		:type need: str
		"""
		self.need = need
		self.text = text

	def __str__(self):
		"""Auto-convert to str."""
		return 'cannot represent %s as a %s' % (
			self.text, self.need)

# SHOULD NOT EXIST. ALSO DEFINED IN message.py.
#
# def type_to_text(t):
# """Convert host time value to standard clock-on-the-wall time representation. Return string."""
# a = '%f' % (t,)
# d = a.find('.')

# Specification of time formats.
ISO_CLOCK_RE = r'^([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})[tT]([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})(\.([0-9]+))?$'
iso_clock = re.compile(ISO_CLOCK_RE)

ISO_8601_RE = r'^([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})(T([0-9]{1,2})(:([0-9]{1,2})(:([0-9]{1,2})(\.([0-9]{1,6}))?)?)?([-+]([0-9]{1,2}):?([0-9]{1,2})(\.([0-9]{1,6}))?)?)?$'
iso_8601 = re.compile(ISO_8601_RE)

def clock_to_text(t):
	"""Convert host time value to standard clock-on-the-wall time representation. Return string."""
	a = '%f' % (t,)
	d = a.find('.')
	if d == -1:
		raise ConversionEncodeError('ClockTime', a)
	h = a[:d]
	t = a[d + 1:]
	if not h.isdigit() or not t.isdigit():
		# NOTE: catches times before epoch (negatives)
		raise ConversionEncodeError('ClockTime', a)
	i = int(h)
	f = int(t)
	t9 = time.localtime(i)
	iso = time.strftime(ISO_8601_NO_SECONDS, t9)
	s = t9[5]
	if f == 0:
		return '%s:%02d' % (iso, s)
	z = t.rstrip('0')
	return '%s:%02d.%s' % (iso, s, z)

def group_or_zero(s):
	if s is None:
		return 0
	return int(s)

def text_to_clock(s):
	"""Convert a standard clock-on-the-wall time string to a host time value. Return float."""
	m = iso_clock.match(s)
	if not m or s[-1] == 'Z':
		raise ConversionDecodeError('ClockTime', s)
	t9 = (group_or_zero(m.group(1)),
		group_or_zero(m.group(2)),
		group_or_zero(m.group(3)),
		group_or_zero(m.group(4)),
		group_or_zero(m.group(5)),
		group_or_zero(m.group(6)),
		0,
		0,
		-1)
	# Local time, no zone offset and with any
	# fractional part added in.
	c = time.mktime(t9)
	f = m.group(7)
	if f is not None:
		f = float(f)
		if c < 0.0:
			return c - f
		return c + f
	return c

# Helpers for time span values.
#
SPAN_TEXT = r'^[-]?(([0-9]+)d)?(([0-9]+)h)?(([0-9]{1,2})m)?(([0-9]{1,2}(\.[0-9]+)?)s)?$'
spanner = re.compile(SPAN_TEXT)

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR

def span_break(s):
	"""Break down a timespan value into standard quanta. Return tuple."""
	n = s < 0.0
	if n:
		s = -s
	i = int(s)	  # Whole part.
	f = s % 1	   # Fractional part.

	D = int(i / SECONDS_PER_DAY)	 # Grab largest sub-value
	i %= SECONDS_PER_DAY		# Then discard same.

	H = int(i / SECONDS_PER_HOUR)
	i %= SECONDS_PER_HOUR

	M = int(i / SECONDS_PER_MINUTE)
	S = i % SECONDS_PER_MINUTE

	return n, D, H, M, S, f

def span_to_text(s):
	"""Convert a host timespan value to a standard text representation. Return string."""
	n, D, H, M, S, f = span_break(s)

	r = ''
	if n: r += '-'
	if D: r += '%dd' % (D,)
	if H: r += '%dh' % (H,)
	if M: r += '%dm' % (M,)
	if S:
		if f == 0.0:
			r += '%ds' % (S,)
		else:
			t = '%f' % (S + f,)
			r += t.rstrip('0')
			r += 's'
	else:
		if f != 0.0:
			t = '%f' % (S + f,)
			r += t.rstrip('0')
			r += 's'

	if len(r):
		return r
	return '0s'

def text_to_span(t):
	"""Convert a standard text representation of a timespan to a host value. Return float."""
	if len(t) == 0:
		raise ConversionDecodeError('TimeSpan', t)
	# Regular expression and subsequent processing allows for clean redundancy
	# in text representation of timespan, e.g. "1h" is the same as "1h0m0s".
	m = spanner.match(t)
	if not m:
		raise ConversionDecodeError('TimeSpan', t)
	n = t[0] == '-'
	D = group_or_zero(m.group(2))
	H = group_or_zero(m.group(4))
	M = group_or_zero(m.group(6))
	s = D * SECONDS_PER_DAY + H * SECONDS_PER_HOUR + M * SECONDS_PER_MINUTE

	if m.group(7):
		if m.group(9):
			s += float(m.group(8))
		else:
			s += float(int(m.group(8)))
	else:
		s = float(s)
	if n:
		return -s
	return s

ISO_8601_NO_SECONDS = '%Y-%m-%dT%H:%M'

#
#
UTC = datetime.timezone.utc

# Very sensitive functions in the area of fractional
# part and time conversion functions, e.g. gmtime and
# timegm.
def world_to_text(dt):
	"""Convert datetime value to standard ISO 8601 time representation. Return string."""
	tz = dt.tzinfo
	if tz is None:
		cannot = 'cannot represent a naive datetime'
		raise ValueError(cannot)
	if not isinstance(tz, datetime.timezone):
		cannot = 'cannot represent a tzinfo that is not a datetime.timezone'
		raise ValueError(cannot)

	ymdhms = dt.strftime('%Y-%m-%dT%H:%M:%S')

	f = dt.microsecond == 0
	if f:
		fraction = ''
	else:
		fraction = dt.strftime('.%f')
		fraction = fraction.rstrip('0')

	if tz == UTC:
		zone = ''
	else:
		zone = dt.strftime('%z')

	s = '%s%s%s' % (ymdhms, fraction, zone)
	return s

DIGITS_IN_MICRO = 6

def text_to_world(s):
	"""Convert a standard ISO 8601 string to an application value. Return datetime."""
	m = iso_8601.match(s)
	if not m:
		raise ConversionDecodeError('WorldTime', s)

	# Date parts. Required.
	dY = group_or_zero(m.group(1))
	dM = group_or_zero(m.group(2))
	dD = group_or_zero(m.group(3))

	# Time parts.
	tH = tM = tS = 0
	tF = 0

	# Zone parts.
	zH = zM = zS = 0
	zF = 0
	tz = UTC

	x = m.group(4)  # Is there a time and optional zone?
	if x:
		tH = group_or_zero(m.group(5))
		x = m.group(6)  # Is there a minutes, seconds and optional fraction?
		if x:
			tM = group_or_zero(m.group(7))
			x = m.group(8)  # Is there a seconds and optional fraction?
			if x:
				tS = group_or_zero(m.group(9))
				x = m.group(10) # Is there a fraction?
				if x:
					tF = m.group(11) # Fractional digits
					tN = len(tF)
					# Standard expects 6 fractional digits but regex allows from 1 to 6.
					# Unrealistic to expect editing that always conforms to 6 digits.
					# But still, technically this can never happen.
					if tN > DIGITS_IN_MICRO:
						raise ConversionDecodeError('WorldTime', s)
					tF = int(tF)
					# Adjust for the custom strip of trailing
					# zeroes.
					if tF and tN < DIGITS_IN_MICRO:
						tF = tF * 10 ** (DIGITS_IN_MICRO - tN)
		x = m.group(12)	 # Is a timezone present?
		if x:
			zH = group_or_zero(m.group(13))
			zM = group_or_zero(m.group(14))
			x = m.group(15)				 # Is there seconds and optional fraction?
			if x:
				zS = group_or_zero(m.group(16))  # Seconds
				x = m.group(17)				 # Is there a fraction?
				if x:
					zF = m.group(18)  # Fraction digits, no dot.
					zN = len(zF)
					# See same handling of fraction above.
					if zN > DIGITS_IN_MICRO:
						raise ConversionDecodeError('WorldTime', s)
					zF = int(zF)
					# Adjust for the custom strip of trailing
					# zeroes.
					if zF and zN < DIGITS_IN_MICRO:
						zF = zF * 10 ** (DIGITS_IN_MICRO - zN)

			td = datetime.timedelta(hours=zH, minutes=zM, seconds=zS, microseconds=zF)
			tz = datetime.timezone(td)

	dt = datetime.datetime(dY, dM, dD,
		hour=tH, minute=tM, second=tS,
		microsecond=tF,
		tzinfo=tz)
	return dt

# Helpers for timedelta values.
#

def delta_to_text(d):
	"""Convert a TimeDelta value to its text representation. Return string."""
	t = d.total_seconds()
	n, D, H, M, S, f = span_break(t)

	dash = ''
	if n:
		dash = '-'

	if f == 0.0:
		S = '%02d' % (S,)
	else:
		S = '%02f' % (S + f,)
		S = S.rstrip('0')

	if D == 0:
		return '%s%02d:%02d:%s' % (dash, H, M, S)
	return '%s%d:%02d:%02d:%s' % (dash, D, H, M, S)

# Helpers for time delta values.
#
DELTA_TEXT = r'^-?(([0-9]+):)?([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})(\.([0-9]+))?$'
delta = re.compile(DELTA_TEXT)

def text_to_delta(t):
	"""Convert a standard text representation of a time delta to a host value. Return timedelta."""
	m = delta.match(t)
	if not m:
		raise ConversionDecodeError('TimeDelta', t)
	n = t[0] == '-'
	D = group_or_zero(m.group(2))
	H = int(m.group(3))
	M = int(m.group(4))
	S = int(m.group(5))

	F = m.group(7)
	if F is None:
		F = 0
	else:
		x = len(F)
		if x > DIGITS_IN_MICRO:
			raise ConversionDecodeError('TimeDelta', t)
		F = int(F)
		# Adjust for the custom strip of trailing
		# zeroes.
		if F and x < DIGITS_IN_MICRO:
			F = F * 10 ** (DIGITS_IN_MICRO - x)

	if n:
		D = -D
		H = -H
		M = -M
		S = -S
		F = -F

	dt = datetime.timedelta(days=D,
		hours=H,
		minutes=M,
		seconds=S,
		microseconds=F)
	return dt

#
#
def uuid_to_text(u):
	"""Convert a host UUID value to a standard text representation. Return string."""
	t = str(u)
	return t

def text_to_uuid(t):
	"""Convert a standard text representation to a host UUID value. Return UUID."""
	u = uuid.UUID(t)
	return u

#
#
def text_to_type(t):
	"""Convert the dotted string *s* to a class, or None."""
	s = lookup_signature(t)
	return s

def type_to_text(s):
	"""Convert the class *c* to a dotted string representation."""
	t = portable_to_signature(s)
	return t

#
#
def clock_now():
	"""Query the platform for the current ClockTime epoch. Return float."""
	t = time.time()
	return t

def clock_at(year, month, day, hour=0, minute=0, second=0, millisecond=0, microsecond=0):
	"""Convert the date and time arguments into a ClockTime epoch. Return float."""
	m = millisecond / 10 ** 3
	c = microsecond / 10 ** 6
	s = (year, month, day, hour, minute, second, 0, 0, -1)
	t = time.mktime(s)
	t = t + m + c
	return t

def clock_break(t):
	"""Break down a ClockTime value into standard quanta. Return a 10-tuple.

	A microseconds value is appended to the standard time.struct_time 9-tuple. It
	is taken from the fractional part of the value returned by time epoch.

	[0] Year
	[1] Month
	[2] Day of month
	[3] Hour
	[4] Minute
	[5] Second
	[6] Day of week
	[7] Day of year
	[8] Is daylight saving
	[9] Microseconds

	The standard time.localtime function turns a float into Gregorian calendar
	information. Unfortunately it loses the fractional part of a time epoch along
	the way, making format conversions a lossy process. This is an implementation
	that preserves the fractional part but produces a tuple that cannot be
	presented to time.mktime. This function is retained for special uses and
	as a record.
	"""
	i = int(t)
	f = t % 1
	t9 = time.localtime(i)
	if t9.tm_isdst:
		_ = 1
	Y = t9[0]
	M = t9[1]
	D = t9[2]
	H = t9[3]
	m = t9[4]
	S = t9[5]
	w = t9[6]
	y = t9[7]
	s = t9[8]
	X = int(f * 10 ** 6)
	return Y, M, D, H, m, S, w, y, s, X

def clock_span(days=0, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0):
	"""Convert standard time quanta to a host time value. Return float."""
	m = milliseconds / 10 ** 3
	c = microseconds / 10 ** 6
	s = days * SECONDS_PER_DAY + hours * SECONDS_PER_HOUR + minutes * SECONDS_PER_MINUTE + seconds
	r = float(s) + m + c
	return r

def world_now(tz=None):
	"""Query the platform for the current WorldTime. Return datetime."""
	tz = tz or UTC
	t = datetime.datetime.now(tz=tz)
	return t

def world_at(year, month, day, hour=0, minute=0, second=0, millisecond=0, microsecond=0, tz=None):
	"""Convert the date, time and timezone arguments into a WorldTime. Return datetime."""
	p = millisecond * 10 ** 3
	m = microsecond + p
	if tz is None:
		t = datetime.datetime(year, month, day, hour, minute, second, m, tzinfo=UTC)
		return t

	t = datetime.datetime(year, month, day, hour, minute, second, m, tz)
	t = t.astimezone(UTC)
	return t

# Not really needed as datetime object provides
# direct access to breakdown. Included for
# symmetry.
def world_break(w, tz=None):
	"""Break down a WorldTime value into standard quanta. Return tuple."""
	if tz is not None:
		p = w.astimezone(tz)
	else:
		p = w
	Y = p.year
	M = p.month
	D = p.day
	H = p.hour
	m = p.minute
	S = p.second
	X = p.microsecond
	return Y, M, D, H, m, S, X

def world_delta(days=0, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0):
	"""Convert the days, hours, minutes and seconds into a TimeSpan epoch difference. Return float."""
	return datetime.timedelta(days=days,
		hours=hours, minutes=minutes, seconds=seconds,
		milliseconds=milliseconds, microseconds=microseconds)
