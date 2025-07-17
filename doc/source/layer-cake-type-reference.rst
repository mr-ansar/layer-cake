.. _layer-cake-type-reference:

Layer Cake Type Reference
#########################

Type Expressions
================

Type expressions (*tips*) are descriptions of memory, e.g. what argument is being passed
to a process or what an encoding is expected to contain. The **layer-cake** library integrates
with Python type hints while internally running its own type system. Not all Python types
are supported (e.g. ``tuples``) and not all library types are implemented in Python (e.g. arrays).

Type expressions must be *compiled* during loading - before the first asynchronous object
is created. Mostly this happens automatically as a part of function and class definitions;

.. code-block:: python

	def texture(self, x: int=2, y: int=2) -> list[list[float]]:
		table = [[1.0, 2.0], [3.0, 4.0]]
		return table

This compiles and registers entries for ``int``, ``float``, ``list[float]``
and ``list[list[float]]``. Where a type is required outside the domain of a function
or class, the :func:`~.def_type` function is available;

.. code-block:: python

	table_type = lc.def_type(dict[str,Person])

Type expressions can be used in runtime contexts but it is more efficient to use the compiled
value, e.g. ``table_type``. Using ``dict[str,Person]`` results in a lookup for the
associated compiled value.

This does create an unfortunate wrinkle where it is good coding practise to use Python type
hints but a particular hint is also needed somewhere else. The inevitable symptom is duplication
of type information. These situations can be resolved by adding type information to the
function or class registration;

.. code-block:: python

	table_type = lc.def_type(list[list[float]])
	..
	def texture(self, x=1, y: int=1):
		..
		return table

	lc.bind(texture, return_type=table_type, x=int)

Type information passed to :func:`~.bind` overrides whatever information is defined on the
function, using Python hints. The ``return_type`` replaces the ``-> list[list[float]]`` hint
and the ``x=int`` provides the type information for the ``x`` parameter of ``texture``. The
``table_type`` can now be used anywhere its needed and there are no duplicate type expressions.

A type expression is an instance of one of the following:

* a basic Python type, e.g. ``float``
* a constructed type or Python type hint, e.g. ``list[float]``
* a registered class, e.g. ``Person``
* one of the basic library types, e.g. ``TimeSpan``
* an instance of an additional library type, e.g. ``ArrayOf(Unicode(),8)``

.. _basic-python-types:

Basic Python Types
------------------

The Python types that are accepted as *tips*, along with their respective library
equivalents, are listed below. Internally all Python types are converted to their
library equivalents before use.

+---------------+-----------------+----------------------------------------------+
| Python        | Library         | Notes                                        |
+===============+=================+==============================================+
| ``bool``      | ``Boolean``     | True or false.                               |
+---------------+-----------------+----------------------------------------------+
| ``int``       | ``Integer8``    | A large, signed integer.                     |
+---------------+-----------------+----------------------------------------------+
| ``Enum``      | ``UserDefined`` | Subclass of Enum. A name for a number.       |
+---------------+-----------------+----------------------------------------------+
| ``float``     | ``Float8``      | A large, floating-point number.              |
+---------------+-----------------+----------------------------------------------+
| ``bytearray`` | ``Block``       | A sequence of *arbitrary bytes*.             |
+---------------+-----------------+----------------------------------------------+
| ``bytes``     | ``String``      | A sequence of *printable bytes*.             |
+---------------+-----------------+----------------------------------------------+
| ``str``       | ``Unicode``     | A sequence of Unicode *codepoints*.          |
+---------------+-----------------+----------------------------------------------+
| ``datetime``  | ``WorldTime``   | A datetime object.                           |
+---------------+-----------------+----------------------------------------------+
| ``timedelta`` | ``TimeDelta``   | The difference between two datetime objects. |
+---------------+-----------------+----------------------------------------------+
| ``uuid.UUID`` | ``UUID``        | A UUID from the standard Python              |
|               |                 | library.                                     |
+---------------+-----------------+----------------------------------------------+

Enumerations are defined as sub-classes of ``Enum``;

.. code-block:: python

	from enum import Enum

	class ScopeOfDirectory(Enum):
		LAN=1
		HOST=2
		GROUP=3

.. _basic-library-types:

Basic Library Types
-------------------

The **layer-cake** types that are accepted as *tips*, along with their respective
Python equivalents, are listed below.

+-------------------------+---------------+-------------------------------------+
| Library                 | Python        | Notes                               |
+=========================+===============+=====================================+
| Boolean                 | ``bool``      | True or false.                      |
+-------------------------+---------------+-------------------------------------+
| Byte                    | ``int``       | A single `arbitrary byte`.          |
+-------------------------+---------------+-------------------------------------+
| Character               | ``bytes``     | A single `printable byte`.          |
+-------------------------+---------------+-------------------------------------+
| Rune                    | ``str``       | A single Unicode `code-point`.      |
+-------------------------+---------------+-------------------------------------+
| Integer8                | ``int``       | Signed integer numbers.             |
+-------------------------+---------------+-------------------------------------+
| Float8                  | ``float``     | Signed, floating-point numbers      |
+-------------------------+---------------+-------------------------------------+
| Block                   | ``bytearray`` | A sequence of `arbitrary bytes`.    |
+-------------------------+---------------+-------------------------------------+
| String                  | ``bytes``     | A sequence of `printable bytes`.    |
+-------------------------+---------------+-------------------------------------+
| Unicode                 | ``str``       | A sequence of Unicode `codepoints`. |
+-------------------------+---------------+-------------------------------------+
| ClockTime               | ``float``     | A local time, i.e. ``float``.       |
+-------------------------+---------------+-------------------------------------+
| TimeSpan                | ``float``     | A local time delta, i.e. ``float``. |
+-------------------------+---------------+-------------------------------------+
| WorldTime               | ``datetime``  | A date, time and timezone.          |
+-------------------------+---------------+-------------------------------------+
| TimeDelta               | ``timedelta`` | A time delta, i.e. t2 - t1.         |
+-------------------------+---------------+-------------------------------------+
| UUID                    | ``UUID``      | A Python uuid.UUID.                 |
+-------------------------+---------------+-------------------------------------+
| Any                     |               | An instance of any registered       |
|                         |               | type.                               |
+-------------------------+---------------+-------------------------------------+
| Type                    | ``class``     | A registered class, e.g. Person.    |
+-------------------------+---------------+-------------------------------------+
| Word                    |               | A generic form.                     |
+-------------------------+---------------+-------------------------------------+
| Address                 |               | Runtime object identity.            |
+-------------------------+---------------+-------------------------------------+

There are multiple library types that are implemented using common Python types.
A ``float`` is used to hold ``Float8``, ``ClockTime`` and ``TimeSpan`` values.
The difference is about representation within an encoding.

If a :func:`schedule_changes` function is defined with a parameter ``adjustment: TimeSpan=0.0``
then the value is expected to be a floating-point value such as ``0.0``. If the
function is called from the command-line as a process entry-point, values must
be expressed in the ``TimeSpan`` representation;

.. code-block:: console

	$ python3 schedule-changes.py --adjustment=1d2h

This can be less fragile than expecting the entry of ``93600.0``. The same conversions
are happening for network encodings. When debugging network messages at lower
levels, members defined with the ``TimeSpan`` library type will appear as JSON strings
like ``"2m34.1s"`` rather than ``154.1``.

.. _additional-library-types:

Additional Library Types
------------------------

The **layer-cake** types that involve additional information and therefore cannot
appear simply as a class reference, appear below. Types such as ``VectorOf(type)``
are passed a type expression as an argument. This is a recursive definition,
though *type* is limited to examples of library types, i.e. use ``VectorOf(Integer8())``
not ``VectorOf(int)``. Also note that ``VectorOf`` expects an instance of a type not
the class, i.e. ``Integer8()`` rather than ``Integer8``.

+-------------------------+---------------+-------------------------------------+
| Library                 | Python        | Notes                               |
+=========================+===============+=====================================+
| ArrayOf(*type*, *size*) | ``list``      | Fixed number of objects.            |
+-------------------------+---------------+-------------------------------------+
| VectorOf(*type*)        | ``list``      | A sequence of zero or more objects. |
+-------------------------+---------------+-------------------------------------+
| SetOf(*type*)           | ``set``       | A collection of unique objects.     |
+-------------------------+---------------+-------------------------------------+
| MapOf(*key*, *type*)    | ``dict``      | A collection of key-value pairs.    |
+-------------------------+---------------+-------------------------------------+
| DequeOf(*type*)         | ``deque``     | A double-ended queue of objects.    |
+-------------------------+---------------+-------------------------------------+
| UserDefined(*type*)     | ``class``     | An instance of a registered class.  |
+-------------------------+---------------+-------------------------------------+
| PointerTo(*type*)       |               | An object that may appear multiple  |
|                         |               | times in the single representation. |
+-------------------------+---------------+-------------------------------------+

.. _strings-of-things:

Strings Of Things
+++++++++++++++++

The ``Byte``, ``Character`` and ``Rune`` types facilitate the
proper handling of an `arbitrary byte`, a `printable byte` and a Unicode
code-point, respectively. There are no exact Python equivalents for these types
as Python stores these values as "strings of length 1". They can be used
in type expressions for finer control over the representation of those short
strings.

The ``Block``, ``String`` and ``Unicode`` types describe sequences of ``Byte``,
``Character`` and ``Rune``, respectively.

The ``String`` and ``Block`` types result in different representations of the same
application data, i.e. a sequence of bytes. The former assumes that there is a
benefit to passing on the printable bytes (0x20 through to 0x7E) without alteration,
i.e. for readability. The non-printing bytes will be "escaped" using the mechanism
appropriate to the current encoding.

The ``Block`` type is intended for the handling of binary data, such as the
block-by-block transfer of image files. Sending a ``Block`` across a network
connection is the optimal use of bandwidth. It receives pass-through behaviour,
i.e. it is streamed directly onto outgoing buffers. A ``Block`` within a
message is represented as a base64-encoded JSON string, with all the attendant
encoding and decoding behaviour.

Dates, Times And Zones
++++++++++++++++++++++

The library types associated with time values appear below;

+---------------+----------------+----------------------------------------------+
| Library       | Python         | Notes                                        |
+===============+================+==============================================+
| ClockTime     | ``float``      | A local time, i.e. ``float``.                |
+---------------+----------------+----------------------------------------------+
| TimeSpan      | ``float``      | A local time delta, i.e. ``float``.          |
+---------------+----------------+----------------------------------------------+
| WorldTime     | ``datetime``   | A date, time and timezone.                   |
+---------------+----------------+----------------------------------------------+
| TimeDelta     | ``timedelta``  | A time delta, i.e. t2 - t1.                  |
+---------------+----------------+----------------------------------------------+

The library supports the two styles of time values; float-based values that record
the number of seconds since an epoch (e.g. January 1, 1970) and ``datetime`` objects
that hold explicit year, month (etc) values. In general applications will use ``datetime``
and ``timedelta`` values, but the float-based types are retained for those scenarios
where the full sophistication of daylight saving, war-time adjustments and
leap seconds, are not needed.

To provide timezone capability, the library allows instances of ``datetime.timezone``
for the ``tzinfo`` attribute. Assigning a value from any other timezone library,
such as ``dateutil.tz.tzfile`` or ``zoneinfo.ZoneInfo``, will result in the raising
of an exception during encoding. By default all ``WorldTime`` values are assigned
the ``datetime.timezone.utc`` timezone value.

Applications required to manage ``datetime`` objects with a variety of timezones, say
selected by a user from the set of IANA names, must implement their own conversions
between their datetime objects and library ``datetime`` objects, i.e. ``WorldTime``.

Object Pointers
+++++++++++++++

The proper type expression for an object that may appear at multiple
points in a single store operation, looks like;

.. code-block:: python

    lc.PointerTo(Person)

The library uses these "pointers" to implement graphs, e.g. linked-lists, trees
and networks.
