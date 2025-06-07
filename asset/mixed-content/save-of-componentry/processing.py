# Author: Scott Woods <scott.suzuki@gmail.com>
# MIT License
#
# Copyright (c) 2017-2022 Scott Woods
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

"""Platform processes as objects.

Async objects are used to start and manage underlying platform processes. The
named process is started, runs to completion and (potentially) returns a value.
This conforms to the general model of an asynchronous object.

There are two variants. Utility provides the most expressive access possible to
third-party executables. These are processes that may accept many different styles
of arguments and behave differently with respect to the standard streams (e.g. stdout).
The class provides for convenient sending of a stream of text or bytes to the process,
and the corresponding ability to receive text or bytes as a result.

The Process class is used where the targeted executable is implemented using a
special framework provided by the library. An instance of a message (i.e. with
fully typed members) is passed over the input pipe, to serve as "arguments" or
"configuration". An instance of an Any() expression is expected on the output.
In this way the local object can satisfy all the expectations of an async object,
while the actual work is carried out in the child process.

Both classes implement the proper termination behaviour. A Stop() message is
translated into a platform signal, to interrupt the execution of the targeted
process. This is a fundamental part of the asynchronous object lifecycle and
it brings expressive and responsive multi-processing capability.

.. autoclass:: Process
.. autoclass:: Punctuation
.. autoclass:: Utility
"""
__docformat__ = 'restructuredtext'

__all__ = [
    'Process',
    'Punctuation',
    'Utility',
    'process_args',
    'CodecArgs'
]

#
#
import sys
import os
import signal
from subprocess import Popen, PIPE, DEVNULL
import shutil
import io
import uuid
from datetime import datetime, timedelta
from collections import deque
import base64
import ansar.encode as ar
from .lifecycle import Start, Completed, Faulted, Stop, Aborted
from .point import Point, bind_function
from .machine import StateMachine, bind_statemachine
from .framework import home

# A thread dedicated to the blocking task of
# waiting for termination of a process.
def wait(self, p, piping, input):
    if piping:
        out, _ = p.communicate(input=input)
        return p.returncode, out
    else:
        code = p.wait()
        return code, None

bind_function(wait)

# The Process class
# A platform process that accepts a set of fully-typed arguments
# and returns a fully-typed result.
class INITIAL: pass
class EXECUTING: pass
class CLEARING: pass

class Process(Point, StateMachine):
    def __init__(self, name, input=None, output=True, role=None, **kw):
        Point.__init__(self)
        StateMachine.__init__(self, INITIAL)
        self.name = name
        self.input = input
        self.output = output
        self.role = role
        self.kw = kw
        self.p = None

def Process_INITIAL_Start(self, message):
    executable = shutil.which(self.name, path=home().bin_path)
    if executable is None:
        cwd = os.getcwd()
        c = 'cannot resolve executable "%s" from "%s"' % (self.name, cwd)
        self.complete(Faulted(condition=c))

    # Pipe work. There is a fixed contract between the parent
    # and the child. Arguments are encoded onto stdin and results
    # are decoded from stdout - both optional. The child inherits
    # the stderr of the parent.
    stdin = None
    input = None
    io = ''
    if self.input is not None:
        stdin = PIPE
        encoding = ar.CodecJson()
        t = type(self.input)
        try:
            input = encoding.encode(self.input, ar.UserDefined(t))
            io += 'i'
        except ar.CodecFailed as e:
            s = str(e)
            c = 'args for "%s", %s' % (self.name, s)
            self.complete(Faulted(condition=c, explanation='not a standard component'))

    stdout = None
    if self.output:
        stdout = PIPE
        io += 'o'

    command = [executable]
    io = '--ansar-io=%s' % (io,)
    command.append(io)

    # Pass the info needed to maintain a process hierarchy, enough
    # to know what to do about settings and logging.
    # First - construct a role, i.e. the relative path from
    # some logical home to a unique place for this child. A
    # series of names separated by dots.

    role = self.role
    if role is None:                        # No assigned role.
        base = os.path.basename(executable) # Use the name of the executable.
        zero = os.path.splitext(base)[0]
        role = zero.replace('_', '-')

    # Does the child have a place to maintain its own files
    # and store its logs.
    h = home()
    if h.home is not None:
        t = '--ansar-home=%s' % (h.home.path,)
        command.append(t)

    #
    #
    if h.settings is not None:
        t = '--ansar-settings=%s' % (h.settings.path,)
        command.append(t)

    #
    #
    if h.bin is not None:
        t = '--ansar-bin=%s' % (h.bin.path,)
        command.append(t)

    #
    #
    if h.logs is not None:
        t = '--ansar-logs=%s' % (h.logs.path,)
        command.append(t)

    # Construct the child argument depending on whether this process
    # is the root or not.
    if h.role is None:
        t = '--ansar-role=%s' % (role,)          # Root.
    else:
        t = '--ansar-role=%s.%s' % (h.role, role)
    command.append(t)

    # Default is to break association with controlling
    # terminal.
    start_new_session = self.kw.pop('start_new_session', True)

    # Force the details of the I/O streams.
    self.p = Popen(command,
        start_new_session=start_new_session,
        stdin=stdin, stdout=stdout, stderr=sys.stderr,
        text=True, encoding='utf-8', errors='strict',
        env=t.bin_env,
        **self.kw)

    piping = stdin == PIPE or stdout == PIPE
    self.create(wait, self.p, piping, input)
    return EXECUTING

def Process_EXECUTING_Completed(self, message):
    # Wait thread has returned
    # Forward the result.
    code, out = message.value
    if code == 0:
        if out is None:
            self.complete()
        encoding = ar.CodecJson()
        try:
            output = encoding.decode(out, ar.Any())
        except ar.CodecFailed as e:
            s = str(e)
            c = 'cannot decode value, %s' % (s,)
            self.complete(Faulted(condition=c, explanation='not a standard component'))

        # Proper completion.
        self.complete(output)
    c = 'child exit code %d' % (code,)
    self.complete(Faulted(condition=c, explanation='expecting 0 (zero)'))

def Process_EXECUTING_Stop(self, message):
    self.p.terminate()
    return CLEARING

def Process_CLEARING_Completed(self, message):
    code, _ = message.value
    if code < 0:
        if -code == signal.SIGTERM:
            self.complete(Aborted())
        c = 'child signal code %d' % (-code,)
        self.complete(Faulted(condition=c, explanation='expecting SIGTERM (15)'))
    elif code == 1:
        c = 'child exit code 1'
        self.complete(Faulted(condition=c, explanation='framework failure, e.g. encoding/decoding'))
    elif code == 0:
        self.complete(Aborted())
    # Some positive exit code
    # A standard process can only return -SIGTERM, 0 and 1.
    c = 'child exit code %d' % (code,)
    self.complete(Faulted(condition=c, explanation='not expected from framework process'))

PROCESS_DISPATCH = {
    INITIAL: (
        (Start,),
        ()
    ),
    EXECUTING: (
        (Completed, Stop),
        ()
    ),
    CLEARING: (
        (Completed,),
        ()
    ),
}

bind_statemachine(Process, dispatch=PROCESS_DISPATCH)

#
#
class Punctuation(object):
    def __init__(self, dash=None, double_dash=None,
            list_ends=None, list_separator=None,
            dict_ends=None, dict_separator=None, dict_colon=None,
            message_ends=None, message_separator=None, message_colon=None,
            true_false=None, no_value=None,
            flag_value_separator=None, any_separator=None):
        self.dash = dash or '-'
        self.double_dash = double_dash or '--'
        self.list_ends = list_ends or [None, None]
        self.list_separator = list_separator or ','
        self.dict_ends = dict_ends or [None, None]
        self.dict_separator = dict_separator or ','
        self.dict_colon = dict_colon or ':'
        self.message_ends = message_ends or [None, None]
        self.message_separator = message_separator or ','
        self.message_colon = message_colon or ':'
        self.true_false = true_false or ['true', 'false']
        self.no_value = no_value or 'null'
        self.flag_value_separator = flag_value_separator or '='
        self.any_separator = any_separator or '/'

class Utility(Point, StateMachine):
    def __init__(self, name, *args,
            args_schema=None, punctuation=None,
            stdin=None, stdout=None, stderr=None,
            text=False, encoding=None, errors=None,
            cwd=None,
            **kw):
        Point.__init__(self)
        StateMachine.__init__(self, INITIAL)
        ar.fix_schema(name, args_schema)
        self.name = name
        self.args = args
        self.args_schema = args_schema
        self.punctuation = punctuation or Punctuation()
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.text = text
        self.encoding = encoding
        self.errors = errors
        self.cwd = cwd
        self.input = None
        self.piping = False
        self.kw = kw
        self.p = None

def Utility_INITIAL_Start(self, message):
    executable = shutil.which(self.name, path=home().bin_path)
    if executable is None:
        cwd = os.getcwd()
        self.warning('cannot resolve executable "%s" from "%s"' % (self.name, cwd))
        self.complete()

    try:
        args = process_args(self.args, self.args_schema, self.punctuation)
    except ValueError as e:
        s = str(e)
        self.warning(s)
        self.complete()

    # Pipe work
    # 1. ACTION - nothing in, nothing out (default)
    # 2. SINK - something in, nothing out
    # 3. SOURCE - nothing in, something out
    # 4. FILTER - something in, something out

    stdin = self.stdin
    if isinstance(stdin, str):
        self.input = stdin
        self.stdin = PIPE
        self.text = True
    elif isinstance(stdin, (bytes, bytearray)):    # Block
        self.input = stdin
        self.stdin = PIPE
        self.text = False

    stdout = self.stdout
    if stdout == str:     # Unicode
        if stdin and not self.text:
            raise ValueError('cannot support different input/output/error pipes')
        self.stdout = PIPE
        self.text = True
    elif stdout in (bytes, bytearray):    # Block
        if stdin and self.text:
            raise ValueError('cannot support different input/output/error pipes')
        self.stdout = PIPE
        self.text = False

    stderr = self.stderr
    if stderr == str:     # Unicode
        if (stdin or stdout) and not self.text:
            raise ValueError('cannot support different input/output/error pipes')
        self.stderr = PIPE
        self.text = True
    elif stderr in (bytes, bytearray):    # Block
        if (stdin or stdout) and self.text:
            raise ValueError('cannot support different input/output pipes')
        self.stderr = PIPE
        self.text = False

    self.piping = stdin or stdout or stderr

    line = [executable]
    line.extend(args)

    h = home()
    if len(self.kw) > 0:
        kw = dict(stdin=self.stdin, stdout=self.stdout, stderr=self.stderr,
            text=self.text, encoding=self.encoding, errors=self.errors,
            cwd=self.cwd, env=h.bin_path)
        kw.update(self.kw)
        self.p = Popen(line, **kw)
        self.create(wait, self.p, self.piping, self.input)
        return EXECUTING

    if self.piping:
        self.p = Popen(line,
            stdin=self.stdin, stdout=self.stdout, stderr=self.stderr,
            text=self.text, encoding=self.encoding, errors=self.errors,
            cwd=self.cwd, env=h.bin_path)
    else:
        self.p = Popen(line, cwd=self.cwd, env=h.bin_path)
    self.create(wait, self.p, self.piping, self.input)
    return EXECUTING

def Utility_EXECUTING_Completed(self, message):
    # Wait thread has returned
    # Forward the result.
    code, out = message.value
    if code == 0:
        self.complete(out)
    c = 'child exit code %d' % (code,)
    self.complete(Faulted(condition=c, explanation='expecting 0 (zero)'))

def Utility_EXECUTING_Stop(self, message):
    self.p.terminate()
    return CLEARING

def Utility_CLEARING_Completed(self, message):
    code, _ = message.value
    if code < 0:
        if -code == signal.SIGTERM:
            self.complete(Aborted())
        c = 'child signal code %d' % (-code,)
        self.complete(Faulted(condition=c, explanation='expecting SIGTERM (15)'))

    # These are non-standard processes, i.e. there will
    # be a variety of meanings to exit codes. Also, allow
    # ships passing in the night. And any positive exit
    # code.
    self.complete(Aborted())

UTILITY_DISPATCH = {
    INITIAL: (
        (Start,),
        ()
    ),
    EXECUTING: (
        (Completed, Stop),
        ()
    ),
    CLEARING: (
        (Completed,),
        ()
    ),
}

bind_statemachine(Utility, dispatch=UTILITY_DISPATCH)

#
#

NoneType = type(None)

def write_if(r, s):
    if s:
        r.write(s)

def write_if_else(r, b, ie):
    if b:
        r.write(ie[0])
    else:
        r.write(ie[1])

def dash_style(name, punctuation):
    if len(name) == 1:
        return punctuation.dash
    return punctuation.double_dash

def resolve(name, value, schema, punctuation):
    if value is None:
        return None
    encoding = CodecArgs(pretty_format=False)
    inferred = False
    try:
        if schema:
            try:
                te = schema[name]
            except KeyError:
                inferred = True
                t = type(value)
                te = ar.fix_expression(t, set())
        else:
            inferred = True
            t = type(value)
            te = ar.fix_expression(t, set())

        value = encoding.encode(value, te, punctuation)
        return value
    except ar.CodecFailed as e:
        s = str(e)
    except ar.TypeTrack as e:
        s = e.reason
    
    if inferred:
        s = 'inferring type for %r failed - %s' % (name, s)
    else:
        s = 'encoding for %r failed - %s' % (name, s)
    raise ValueError(s)

def process_args(args, schema, punctuation=None):
    punctuation = punctuation or Punctuation()
    line = []
    for i, a in enumerate(args):
        if isinstance(a, tuple):
            n = len(a)
            if not (n in [2, 3]):
                raise ValueError('tuple flag [%d] with unexpected length %d' % (i, n))
            
            name = a[0]
            if not isinstance(name, str):
                raise ValueError('tuple flag [%d] with strange name %r' % (i, name))

            separator = punctuation.flag_value_separator
            dash = dash_style(name, punctuation)
            if len(a) == 2:
                value = resolve(name, a[1], schema, punctuation)
            else:
                separator = a[1]
                value = resolve(name, a[2], schema, punctuation)

            if value is None:
                line.append('%s%s' % (dash, name))
            elif separator is None:
                line.append('%s%s' % (dash, name))
                line.append('%s' % (value,))
            else:
                line.append('%s%s%s%s' % (dash, name, separator, value))
        else:
            value = resolve(i, a, schema, punctuation)
            line.append('%s' % (value,))
    return line

# Dedicated code for transforming python data into
# reasonable command-line text.

def p2a_placeholder(c, p, t):
    r = c.representation
    r.write('<?>')

def p2a_address(c, p, t):
    p2a_vector(c, p, ar.VectorOf(ar.Integer8()))

def p2a_none(c, p, t):
    r = c.representation
    r.write('<>')

def p2a_bool(c, p, t):
    r = c.representation
    tf = c.punctuation.true_false
    write_if_else(r, p, tf)

def p2a_byte(c, p, t):
    r = c.representation
    value = '%d' % (p,)
    r.write(value)

def p2a_int(c, p, t):
    r = c.representation
    value = '%d' % (p,)
    r.write(value)

def p2a_float(c, p, t):
    r = c.representation
    value = '%f' % (p,)
    value = value.rstrip('0')
    r.write(value)

def p2a_string(c, p, t):
    r = c.representation
    w = ''
    for b in p:
        w += chr(b)
    r.write(w)

def p2a_block(c, p, t):
    r = c.representation
    w = base64.b64encode(p)
    w = w.decode(encoding='utf-8', errors='strict')
    r.write(w)

def p2a_unicode(c, p, t):
    r = c.representation
    r.write(p)

def p2a_clock(c, p, t):
    r = c.representation
    w = ar.clock_to_text(p)
    r.write(w)

def p2a_span(c, p, t):
    r = c.representation
    w = ar.span_to_text(p)
    r.write(w)

def p2a_world(c, p, t):
    r = c.representation
    w = ar.world_to_text(p)
    r.write(w)

def p2a_delta(c, p, t):
    r = c.representation
    w = ar.delta_to_text(p)
    r.write(w)

def p2a_uuid(c, p, t):
    r = c.representation
    w = ar.uuid_to_text(p)
    r.write(w)

def p2a_enumeration(c, p, t):
    r = c.representation
    try:
        w = t.to_name(p)
    except KeyError:
        m = '/'.join(t.kv.keys())
        raise ar.EnumerationFailed('no name for %d in "%s"' % (p, m))
    r.write(w)

def p2a_message(c, p, t):
    message = t.element
    rt = message.__art__
    schema = rt.value
    # Get the set of names appropriate to
    # this message type. Or none.
    r = c.representation
    me = c.punctuation.message_ends
    ms = c.punctuation.message_separator
    mc = c.punctuation.message_colon
    n = len(schema)

    write_if(r, me[0])
    for k, v in schema.items():
        c.walking_stack.append(k)
        def get_put():
            m = getattr(p, k, None)
            r.write(k)
            write_if(r, mc)
            python_to_args(c, m, v)
            if (n - 1) > 0:
                write_if(r, ms)
        get_put()
        n -= 1
        c.walking_stack.pop()
    write_if(r, me[1])

def p2a_array(c, p, t):
    e = t.element
    n = len(p)
    s = t.size
    if n != s:
        raise ValueError('array size vs specification - %d/%d' % (n, s))
    r = c.representation
    le = c.punctuation.list_ends
    ls = c.punctuation.list_separator
    write_if(r, le[0])
    for i, y in enumerate(p):
        c.walking_stack.append(i)
        python_to_args(c, p[i], e)
        if (i + 1) < n:
            write_if(r, ls)
        c.walking_stack.pop()
    write_if(r, le[1])

def p2a_vector(c, p, t):
    e = t.element
    r = c.representation
    le = c.punctuation.list_ends
    ls = c.punctuation.list_separator
    n = len(p)
    write_if(r, le[0])
    for i, y in enumerate(p):
        c.walking_stack.append(i)
        python_to_args(c, p[i], e)
        if (i + 1) < n:
            write_if(r, ls)
        c.walking_stack.pop()
    write_if(r, le[1])

def p2a_set(c, p, t):
    e = t.element
    r = c.representation
    le = c.punctuation.list_ends
    ls = c.punctuation.list_separator
    n = len(p)
    write_if(r, le[0])
    for i, y in enumerate(p):
        c.walking_stack.append(i)
        python_to_args(c, y, e)
        if (i + 1) < n:
            write_if(r, ls)
        c.walking_stack.pop()
    write_if(r, le[1])

def p2a_map(c, p, t):
    k_t = t.key
    v_t = t.value
    r = c.representation
    de = c.punctuation.dict_ends
    ds = c.punctuation.dict_separator
    dc = c.punctuation.dict_colon
    n = len(p)
    write_if(r, de[0])
    for k, v in p.items():
        python_to_args(c, k, k_t)
        write_if(r, dc)
        python_to_args(c, v, v_t)
        if (n - 1) > 0:
            write_if(r, ds)
        n -= 1
    write_if(r, de[1])

def p2a_type(c, p, t):
    r = c.representation
    b = p.__art__
    w = b.path
    r.write(w)

def p2a_any(c, p, t):
    r = c.representation
    le = c.punctuation.list_ends
    ls = c.punctuation.any_separator
    a = p.__class__

    write_if(r, le[0])
    python_to_args(c, a, ar.Type())
    write_if(r, ls)
    python_to_args(c, p, ar.UserDefined(a))
    write_if(r, le[1])

# Map the python+portable pair to a dedicated
# transform function.
p2a = {
    # Direct mappings.
    (bool, ar.Boolean): p2a_bool,
    (int, ar.Byte): p2a_byte,
    (bytes, ar.Character): p2a_string,
    (str, ar.Rune): p2a_unicode,
    (int, ar.Integer2): p2a_int,
    (int, ar.Integer4): p2a_int,
    (int, ar.Integer8): p2a_int,
    (int, ar.Unsigned2): p2a_int,
    (int, ar.Unsigned4): p2a_int,
    (int, ar.Unsigned8): p2a_int,
    (float, ar.Float4): p2a_float,
    (float, ar.Float8): p2a_float,
    (int, ar.Enumeration): p2a_enumeration,
    (bytearray, ar.Block): p2a_block,
    (bytes, ar.String): p2a_string,
    (str, ar.Unicode): p2a_unicode,
    (float, ar.ClockTime): p2a_clock,
    (float, ar.TimeSpan): p2a_span,
    (datetime, ar.WorldTime): p2a_world,
    (timedelta, ar.TimeDelta): p2a_delta,
    (uuid.UUID, ar.UUID): p2a_uuid,
    (list, ar.ArrayOf): p2a_array,
    (list, ar.VectorOf): p2a_vector,
    (set, ar.SetOf): p2a_set,
    (dict, ar.MapOf): p2a_map,
    (deque, ar.DequeOf): p2a_set,
    (ar.TypeType, ar.Type): p2a_type,
    (list, ar.TargetAddress): p2a_address,
    (list, ar.Address): p2a_address,

    # PointerTo - can be any of the above.
    # (bool, PointerTo): p2a_pointer,
    # (int, PointerTo): p2a_pointer,
    # (float, PointerTo): p2a_pointer,
    # (bytearray, PointerTo): p2a_pointer,
    # (bytes, PointerTo): p2a_pointer,
    # (str, PointerTo): p2a_pointer,
    # ClockTime and TimeDelta. Float/ptr already in table.
    # (float, PointerTo): p2a_pointer,
    # (float, PointerTo): p2a_pointer,
    # (datetime, PointerTo): p2a_pointer,
    # (timedelta, PointerTo): p2a_pointer,
    # (uuid.UUID, PointerTo): p2a_pointer,
    # (list, PointerTo): p2a_pointer,
    # (set, PointerTo): p2a_pointer,
    # (dict, PointerTo): p2a_pointer,
    # (deque, PointerTo): p2a_pointer,
    # (TypeType, PointerTo): p2a_pointer,
    # (tuple, PointerTo): p2a_pointer,
    # (Message, PointerTo): p2a_pointer,

    # Two mechanisms for including messages
    (ar.Message, ar.UserDefined): p2a_message,
    (ar.Message, ar.Any): p2a_any,

    # Support for Word, i.e. passthru anything
    # that could have been produced by the functions
    # above. No iterating nested layers.

    (bool, ar.Word): p2a_bool,
    (int, ar.Word): p2a_int,
    (float, ar.Word): p2a_float,
    # (bytearray, Word): pass_thru,
    # (bytes, Word): pass_thru,
    (str, ar.Word): p2a_unicode,
    (list, ar.Word): p2a_vector,
    (dict, ar.Word): p2a_map,
    # set, tuple - do not appear in generic

    # Provide for null values being
    # presented for different universal
    # types.

    (NoneType, ar.Boolean): p2a_none,
    (NoneType, ar.Byte): p2a_none,
    (NoneType, ar.Character): p2a_none,
    (NoneType, ar.Rune): p2a_none,
    (NoneType, ar.Integer2): p2a_none,
    (NoneType, ar.Integer4): p2a_none,
    (NoneType, ar.Integer8): p2a_none,
    (NoneType, ar.Unsigned2): p2a_none,
    (NoneType, ar.Unsigned4): p2a_none,
    (NoneType, ar.Unsigned8): p2a_none,
    (NoneType, ar.Float4): p2a_none,
    (NoneType, ar.Float8): p2a_none,
    (NoneType, ar.Block): p2a_none,
    (NoneType, ar.String): p2a_none,
    (NoneType, ar.Unicode): p2a_none,
    (NoneType, ar.ClockTime): p2a_none,
    (NoneType, ar.TimeSpan): p2a_none,
    (NoneType, ar.WorldTime): p2a_none,
    (NoneType, ar.TimeDelta): p2a_none,
    (NoneType, ar.UUID): p2a_none,
    (NoneType, ar.Enumeration): p2a_none,
    # DO NOT ALLOW
    # (NoneType, UserDefined): p2a_none,
    # (NoneType, ArrayOf): p2a_none,
    # (NoneType, VectorOf): p2a_none,
    # (NoneType, SetOf): p2a_none,
    # (NoneType, MapOf): p2a_none,
    # (NoneType, DequeOf): p2a_none,
    (NoneType, ar.PointerTo): p2a_none,
    (NoneType, ar.Type): p2a_none,
    (NoneType, ar.TargetAddress): p2a_none,
    (NoneType, ar.Address): p2a_none,
    (NoneType, ar.Word): p2a_none,
    (NoneType, ar.Any): p2a_none,
}

def python_to_args(c, p, t):
    """Generate word equivalent for the supplied application data.

    :param c: the active codec
    :type c: an Ansar Codec
    :param p: the data item
    :type p: application data
    :param t: the portable description of `p`.
    :type t: a portable expression
    :return: a generic word, ready for serialization.
    """
    try:
        if ar.is_message(p):
            a = ar.Message
        else:
            a = getattr(p, '__class__')
    except AttributeError:
        a = None

    try:
        b = t.__class__         # One of the universal types.
    except AttributeError:
        b = None

    if a is None:
        if b is None:
            raise TypeError('data and specification are unusable')
        raise TypeError('data with specification "%s" is unusable' % (b.__name__,))
    elif b is None:
        raise TypeError('data "%s" has unusable specification' % (a.__name__,))

    try:
        f = p2a[a, b]
    except KeyError:
        raise TypeError('no transformation for data/specification %s/%s' % (a.__name__, b.__name__))

    # Apply the transform function
    return f(c, p, t)


# Define the wrapper around the JSON encoding
# primitives.
class CodecArgs(ar.Codec):
    """Encoding and decoding of command-line representations."""

    EXTENSION = 'arg'
    SINGLE_TAB = '  '

    def __init__(self, return_proxy=None, local_termination=None, pretty_format=False, decorate_names=True):
        """Construct an args codec."""
        ar.Codec.__init__(self,
            CodecArgs.EXTENSION,
            None,
            None,
            return_proxy, local_termination, pretty_format, decorate_names)
        self.representation = None
        self.tabstops = {}

    def find_tab(self, tabs):
        """Generate the tab-space indicated by the tabs count. Return a string of spaces."""
        try:
            tab = self.tabstops[tabs]
        except KeyError:
            tab = CodecArgs.SINGLE_TAB * tabs
            self.tabstops[tabs] = tab
        return tab

    def encode(self, value, expression, punctuation, version=None):
        """Blah."""
        self.punctuation = punctuation

        self.walking_stack = []         # Breadcrumbs for m.a[0].f.c[1] tracking.
        self.aliased_pointer = {}       # Pointers encountered in value.
        self.portable_pointer = {}      # Pointers accumulated from Incognitos.
        self.any_stack = [set()]
        self.pointer_alias = 2022

        u4 = uuid.uuid4()
        self.alias_space = str(u4)

        self.versioning(expression, version)    # Establish versioning context.
        self.representation = io.StringIO()

        try:
            # Convert the value to a generic intermediate
            # representation.

            python_to_args(self, value, expression)
        except (AttributeError, TypeError, ValueError, IndexError, KeyError,
                ar.EnumerationFailed, ar.ConversionEncodeFailed) as e:
            text = self.nesting()
            if len(text) == 0:
                raise ar.CodecFailed('transformation (%s)', str(e))
            raise ar.CodecFailed('transformation, near "%s" (%s)', text, str(e))
        s = self.representation.getvalue()
        return s

