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

"""Processing of the command line.

Scanning for flags, splitting of flags into name-value pairs and
converting the values according to a relevant schema.
"""
__docformat__ = 'restructuredtext'

__all__ = [
	'process_flags',
	'break_arguments',
	'decode_argument',
	'to_any',
	'from_any',
	'extract_arguments',
	'apply_arguments',
	'command_arguments',
	'command_sub_arguments',
	'command_variables',
]

import os
import sys
from .virtual_memory import *
from .message_memory import *
from .virtual_codec import *
from .json_codec import *
from .virtual_runtime import *
from .command_line import *
from .file_object import *


def process_flags(flags):
	'''Scan a raw list of flags. Return word and flag details.'''
	word = []
	lf = {}		# Long form.
	sf = {}		# Short.

	for f in flags:
		if f.startswith('--'):
			i = f.find('=')
			if i == -1:
				k = f[2:]
				v = None
			else:
				k = f[2:i]
				v = f[i + 1:]
			lf[k] = v
		elif f.startswith('-'):
			i = f.find('=')
			if i == -1:
				k = f[1:]
				v = None
			else:
				k = f[1:i]
				v = f[i + 1:]
			sf[k] = v
		else:
			word.append(f)

	return word, (lf, sf)

def break_arguments(arguments):
	'''Process a command line. Return executable, words and flags.'''
	executable = os.path.abspath(arguments[0])
	word, flags = process_flags(arguments[1:])
	return executable, word, flags

def verbatim(s, w, t):
	return w

DEQUOTED = {
	Character: w2p_string,
	Rune: verbatim,
	Block: w2p_block,
	String: w2p_string,
	Unicode: verbatim,
	Enumeration: w2p_enumeration,
	ClockTime: w2p_clock,
	TimeSpan: w2p_span,
	WorldTime: w2p_world,
	TimeDelta: w2p_delta,
	UUID: w2p_uuid,
	Type: w2p_type,
}

def decode_argument(c, s, t):
	'''Convert the json value into python value based on type. Return decoded value.'''
	q = DEQUOTED.get(type(t), None)
	if q is not None:
		d = q(c, s, t)
	else:
		j = f'{{"value": {s} }}'
		d = c.decode(j, t)
	return d

def first_letters(k):
	'''Generate an acronym for k. Return a string.'''
	s = k.split('_')
	v = [t[0] for t in s if t]	# Omit empty strings, e.g. "from_".
	c = ''.join(v)
	return c

def to_any(v, t):
	if isinstance(t, UserDefined):
		return v
	return (v, t)

def from_any(v):
	if isinstance(v, (list, tuple)) and len(v) == 2 and isinstance(v[1], Portable):
		return v[0]
	return v

def extract_arguments(schema, ls):
	'''Generate a dict of decoded arguments for the given schema and flags. Return a dict and remaining flags.'''
	lf, sf = ls

	# Compile a set of acronyms as aliases for the long form.
	acronym = {}
	for k in schema.keys():
		f = first_letters(k)
		a = acronym.get(f, None)
		if a is None:
			a = []
			acronym[f] = a
		a.append(k)

	# Promote short name to the matching long form.
	def short_to_long(a):
		f = acronym.get(a, None)
		if f is None:
			return None
		if len(f) > 1:
			clashes = ', '.join(f)
			name = f[0].replace('_', '-')
			e1 = f'ambiguous short settings ({clashes})'
			e2 = f'{e1}, use long form --{name}=<value>'
			raise ValueError(e2)
		return f[0]

	# Rather detailed processing of - (dash) and -- (dash-dash)
	# arguments.
	extracted = {}
	lr, sr = {}, {}
	c = CodecJson()

	# Long form --<name>=<value>
	for k, v in lf.items():
		r = k.replace('-', '_')
		t = schema.get(r, None)
		if t is not None:
			d = decode_argument(c, v, t)	# Matched.
			extracted[r] = to_any(d, t)
		else:
			lr[k] = v			# Not matched - remainder.

	# Short form -<first-letters>=<value>
	for k, v in sf.items():
		t = short_to_long(k)	# Map to long name.
		if t is None:
			sr[k] = v			# No mapping in schema.
			continue
		r = t.replace('_', '-')
		if t in extracted:
			raise ValueError(f'use of both long and short forms for "{t}" ({r}/{k})')
		x = schema.get(t, None)
		if x is not None:
			d = decode_argument(c, v, x)
			extracted[t] = to_any(d, x)
		else:
			sr[k] = v

	return extracted, (lr, sr)

def apply_arguments(target, extracted):
	'''Assign members of the target with named values.'''
	schema = type_schema(target)

	for k, v in extracted.items():
		if k in schema:
			d = from_any(v)
			setattr(target, k, d)

def command_arguments(object_type, override_arguments=None):
	process_schema = type_schema(CL)
	object_schema = type_schema(object_type)
	c = set(process_schema.keys()) & set(object_schema.keys())
	if len(c) > 0:
		j = ', '.join(c)
		raise ValueError(f'collision in settings names - {j}')
	if override_arguments is None:
		arguments = sys.argv
	else:
		arguments = override_arguments
	executable, word, flags = break_arguments(arguments)
	extracted, remainder = extract_arguments(process_schema, flags)
	apply_arguments(CL, extracted)
	extracted, remainder = extract_arguments(object_schema, remainder)
	if remainder[0] or remainder[1]:
		k = [k for k in remainder[0].keys()]
		k.extend([k for k in remainder[1].keys()])
		r = ', '.join(k)
		raise ValueError(f'unknown arguments ({r})')
	return executable, extracted, word

#
#
def break_table(object_table):
	table = {t.__name__.rstrip('_'): (t, type_schema(t)) for t in object_table}
	return table

def command_sub_arguments(object_type, object_table, override_arguments=None):
	process_schema = type_schema(CL)
	object_schema = type_schema(object_type)
	s1 = set(process_schema.keys())
	s2 = set(object_schema.keys())
	c = s1 & s2
	if len(c) > 0:
		j = ', '.join(c)
		raise ValueError(f'collision in settings names - {j}')
	if override_arguments is None:
		arguments = sys.argv
	else:
		arguments = override_arguments
	executable, word, flags = break_arguments(arguments)
	extracted, remainder = extract_arguments(process_schema, flags)
	apply_arguments(CL, extracted)
	objected, remainder = extract_arguments(object_schema, remainder)

	# Optional appearance of a sub-command in the arguments.
	if len(word) > 0:
		name = word[0]
		word = word[1:]

		table = break_table(object_table)
		t = table.get(sub, None)
		if t is None:
			raise ValueError(f'unknown sub-command "{sub}"')
		sub_schema = t[1]
		s3 = set(sub_schema.keys())
		s4 = s1 | s2
		c = s3 & s4
		if len(c) > 0:
			j = ', '.join(c)
			raise ValueError(f'collision in settings names - {j}')
		extracted, remainder = extract_arguments(sub_schema, remainder)
		jump = t[0]
		sub = (name, jump, extracted)
	else:
		sub = None		# Non sub command.

	if remainder[0] or remainder[1]:
		k = [k for k in remainder[0].keys()]
		k.extend([k for k in remainder[1].keys()])
		r = ', '.join(k)
		raise ValueError(f'unknown arguments ({r})')
	return executable, objected, word, sub

def command_variables(factory_variables):
	if factory_variables is None:
		return

	environment = {k[5:].replace('-', '_'): v for k, v in os.environ.items()
		if k.startswith('LC_V_')}

	schema = type_schema(factory_variables)
	c = CodecJson()
	for k, t in schema.items():
		K = k.upper()
		e = environment.get(K, None)
		if e is None:
			continue
		v = decode_argument(c, e, t)
		setattr(factory_variables, k, v)
