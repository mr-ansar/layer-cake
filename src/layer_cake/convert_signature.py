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

"""Use ply library to translate between Portables and a text representation.

Part of the upgrade to allow passing of any type rather than exclusively
instances of registered messages.
"""

import sys
from .virtual_memory import *
from enum import Enum

__all__ = [
	'signature_to_portable',
	'portable_to_signature',
]

NAME_CLASS = {
	'boolean': Boolean,
	'integer2': Integer2,
	'integer4': Integer4,
	'integer8': Integer8,
	'unsigned2': Unsigned2,
	'unsigned4': Unsigned4,
	'unsigned8': Unsigned8,
	'float4': Float4,
	'float8': Float8,
	'byte': Byte,
	'block': Block,
	'character': Character,
	'string': String,
	'rune': Rune,
	'unicode': Unicode,
	'clock': ClockTime,
	'span': TimeSpan,
	'world': WorldTime,
	'delta': TimeDelta,
	'uuid': UUID,
	'any': Any,
	'target': TargetAddress,
	'address': Address,
	'type': Type,
	'word': Word,
	'array': ArrayOf,
	'vector': VectorOf,
	'deque': DequeOf,
	'set': SetOf,
	'map': MapOf,
	'pointer': PointerTo,
}

tokens = (
	'NUMBER',
	'NAME',
	'LEFT', 'SEPARATOR', 'RIGHT',
)

# Tokens
t_LEFT = r'<'
t_SEPARATOR = r','
t_RIGHT = r'>'

def t_NUMBER(t):
	r'\d+'
	try:
		value = int(t.value)
	except ValueError:
		value = 0
	t.value = value
	return t

class NotFound(object): pass

def sys_module_class(s):
	"""Convert the dotted string *s* to a class, or None."""
	try:
		i = s.rindex('.')
	except ValueError:
		return None
	module = s[:i]
	name = s[i + 1:]
	try:
		m = sys.modules[module]
	except KeyError:
		return None

	try:
		c = m.__dict__[name]
	except KeyError:
		return None
	return c

def t_NAME(t):
	r'[_a-zA-Z][_a-zA-Z0-9]*(\.[_a-zA-Z0-9]+)*'
	#
	c = NAME_CLASS.get(t.value, NotFound)
	if c is NotFound:
		c = sys_module_class(t.value)
		if c is None:
			raise ValueError(f'unknown class {t.value}')
	t.value = c
	return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")

def t_error(t):
	token = t.value[0]
	e = f'Illegal character "{token}"'
	t.lexer.skip(1)

# Build the lexer
import ply.lex as lex
lexer = lex.lex()

# Parsing rules

precedence = ()

def p_statement_type(t):
	'''statement : type'''
	t[0] = t[1]

def p_type_name(t):
	'''type : NAME'''
	c = t[1]
	if is_portable_class(c):
		if is_container_class(c):
			raise ValueError('container class and no parameters')
		t[0] = c()
	elif issubclass(c, Enum):
		t[0] = Enumeration(c)
	else:
		t[0] = UserDefined(c)

def p_type_name_list(t):
	'''type : NAME LEFT list RIGHT'''
	c = t[1]
	a = t[3]
	if not is_container_class(c):
		raise ValueError('non-container class with parameters')
	if c in (MapOf, ArrayOf):
		t[0] = c(a[0], a[1])
	else:
		t[0] = c(a[0])

def p_list_arg(t):
	'list : arg'
	t[0] = [t[1]]

def p_list_list_arg(t):
	'list : list SEPARATOR arg'
	tl = t[1]
	ta = t[3]
	tl.append(ta)
	t[0] = tl

def p_arg_NUMBER(t):
	'arg : NUMBER'
	number = int(t[1])
	t[0] = number

def p_arg_type(t):
	'arg : type'
	t[0] = t[1]

def p_error(t):
	# self_service.fault('syntax error at "{error}"'.format(error=t.value))
	pass

import ply.yacc as yacc
parser = yacc.yacc(debug=False)

#
#
def signature_to_portable(text):
	'''Given a unique string representation, generate the associated type. Return a Portable.'''
	t = parser.parse(text)
	return t

#
#
CLASS_NAME = {
	Boolean: 'boolean',
	Integer2: 'integer2',
	Integer4: 'integer4',
	Integer8: 'integer8',
	Unsigned2: 'unsigned2',
	Unsigned4: 'unsigned4',
	Unsigned8: 'unsigned8',
	Float4: 'float4',
	Float8: 'float8',
	Byte: 'byte',
	Block: 'block',
	Character: 'character',
	String: 'string',
	Rune: 'rune',
	Unicode: 'unicode',
	ClockTime: 'clock',
	TimeSpan: 'span',
	WorldTime: 'world',
	TimeDelta: 'delta',
	UUID: 'uuid',
	Enumeration: 'not used',
	Any: 'any',
	TargetAddress: 'target',
	Address: 'address',
	Type: 'type',
	Word: 'word',
	ArrayOf: 'array',
	VectorOf: 'vector',
	DequeOf: 'deque',
	SetOf: 'set',
	MapOf: 'map',
	UserDefined: 'not used',
	PointerTo: 'pointer',
}

#
#
def portable_to_signature(a):
	'''Given a Portable, generate a unique signature. Return a string.'''
	c = a.__class__
	t = CLASS_NAME.get(c, NotFound)
	if t is NotFound:
		return ''

	if c == UserDefined:
		return a.element.__art__.path
	if c == Enumeration:
		m = a.element.__module__
		s = a.element.__name__
		return f'{m}.{s}'
	if c in (VectorOf, DequeOf, SetOf, PointerTo):
		e = portable_to_signature(a.element)
		return f'{t}<{e}>'
	if c == MapOf:
		k = portable_to_signature(a.key)
		v = portable_to_signature(a.value)
		return f'{t}<{k},{v}>'
	if c == ArrayOf:
		e = portable_to_signature(a.element)
		return f'{t}<{e},{a.size}>'

	return t
