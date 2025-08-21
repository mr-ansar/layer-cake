.. _type-reference:

Type Reference
##############

A type expression is either a Python hint or an instance of the :class:`~.Portable` type.
Python hints are constructions of class names and syntax tokens (e.g. ``[``). The list
of potential class names include;

* a basic Python type, e.g. ``float``
* a basic library type, e.g. ``TimeDelta``
* a registered class, e.g. ``Customer``

Instances of :class:`~.Portable` are constructed from one of the basic library types
plus those types listed as additional types. All library types derive from :class:`~.Portable`;

* ``Boolean()``
* ``VectorOf(Block())``
* ``MapOf(Unicode(),ArrayOf(Integer8(), 4))``

Library types are constructed from instances, e.g. ``VectorOf(Address())``. The Python
hint facility does not accept instances, leaving no room for ambiguity between the
two type systems.

.. _basic-python-types:

Basic Python Types
------------------

The Python types that are accepted as a hint class, along with their respective library
equivalents, are listed below.

+---------------+------------------------+----------------------------------------------+
| Python        | Library                | Notes                                        |
+===============+========================+==============================================+
| ``bool``      | :class:`~.Boolean`     | True or false.                               |
+---------------+------------------------+----------------------------------------------+
| ``int``       | :class:`~.Integer8`    | A large, signed integer.                     |
+---------------+------------------------+----------------------------------------------+
| ``Enum``      | :class:`~.UserDefined` | Subclass of Enum. A name for a number.       |
+---------------+------------------------+----------------------------------------------+
| ``float``     | :class:`~.Float8`      | A large, floating-point number.              |
+---------------+------------------------+----------------------------------------------+
| ``bytearray`` | :class:`~.Block`       | A sequence of *arbitrary bytes*.             |
+---------------+------------------------+----------------------------------------------+
| ``bytes``     | :class:`~.String`      | A sequence of *printable bytes*.             |
+---------------+------------------------+----------------------------------------------+
| ``str``       | :class:`~.Unicode`     | A sequence of Unicode *codepoints*.          |
+---------------+------------------------+----------------------------------------------+
| ``datetime``  | :class:`~.WorldTime`   | A datetime object.                           |
+---------------+------------------------+----------------------------------------------+
| ``timedelta`` | :class:`~.TimeDelta`   | The difference between two datetime objects. |
+---------------+------------------------+----------------------------------------------+
| ``uuid.UUID`` | :class:`~.UUID`        | A UUID from the standard Python              |
|               |                        | library.                                     |
+---------------+------------------------+----------------------------------------------+

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

The **layer-cake** types that are accepted as a hint class, along with their respective
Python equivalents, are listed below.

+-------------------------+---------------+-------------------------------------+
| Library                 | Python        | Notes                               |
+=========================+===============+=====================================+
| :class:`~.Boolean`      | ``bool``      | True or false.                      |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Byte`         | ``int``       | A single `arbitrary byte`.          |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Character`    | ``bytes``     | A single `printable byte`.          |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Rune`         | ``str``       | A single Unicode `code-point`.      |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Integer8`     | ``int``       | Signed integer numbers.             |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Float8`       | ``float``     | Signed, floating-point numbers      |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Block`        | ``bytearray`` | A sequence of `arbitrary bytes`.    |
+-------------------------+---------------+-------------------------------------+
| :class:`~.String`       | ``bytes``     | A sequence of `printable bytes`.    |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Unicode`      | ``str``       | A sequence of Unicode `codepoints`. |
+-------------------------+---------------+-------------------------------------+
| :class:`~.ClockTime`    | ``float``     | A local time, i.e. ``float``.       |
+-------------------------+---------------+-------------------------------------+
| :class:`~.TimeSpan`     | ``float``     | A local time delta, i.e. ``float``. |
+-------------------------+---------------+-------------------------------------+
| :class:`~.WorldTime`    | ``datetime``  | A date, time and timezone.          |
+-------------------------+---------------+-------------------------------------+
| :class:`~.TimeDelta`    | ``timedelta`` | A time delta, i.e. t2 - t1.         |
+-------------------------+---------------+-------------------------------------+
| :class:`~.UUID`         | ``UUID``      | A Python uuid.UUID.                 |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Any`          |               | A :ref:`message<lc-message>`        |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Type`         | ``class``     | A registered class, e.g. Person.    |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Word`         |               | A generic form.                     |
+-------------------------+---------------+-------------------------------------+
| :class:`~.Address`      |               | Runtime object identity.            |
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

This is more human-friendly than expecting the entry of ``93600.0``. The same conversions
are happening for network encodings. When debugging network messages at lower
levels, members defined with the ``TimeSpan`` library type will appear as JSON strings
like ``"2m34.1s"`` rather than ``154.1``.

.. _additional-library-types:

Additional Library Types
------------------------

The **layer-cake** types that involve additional information and therefore cannot
appear as a hint class, appear below. Types such as ``VectorOf(expression)`` are
passed a library type expression as an argument. This is a recursive definition.
Also note that ``VectorOf`` expects an instance of an expression not the class,
i.e. ``Integer8()`` rather than ``Integer8``.

Instances of these types can only appear at registration time using :func:`~.bind`,
around the use of :meth:`~.Buffering.select`, and around :ref:`machine dispatching<stateless-machines>`.

+------------------------+---------------+-------------------------------------+
| Library                | Python        | Notes                               |
+========================+===============+=====================================+
| :class:`~.ArrayOf`     | ``list``      | Fixed number of objects.            |
+------------------------+---------------+-------------------------------------+
| :class:`~.VectorOf`    | ``list``      | A sequence of zero or more objects. |
+------------------------+---------------+-------------------------------------+
| :class:`~.SetOf`       | ``set``       | A collection of unique objects.     |
+------------------------+---------------+-------------------------------------+
| :class:`~.MapOf`       | ``dict``      | A collection of key-value pairs.    |
+------------------------+---------------+-------------------------------------+
| :class:`~.DequeOf`     | ``deque``     | A double-ended queue of objects.    |
+------------------------+---------------+-------------------------------------+
| :class:`~.UserDefined` | ``class``     | An instance of a registered class.  |
+------------------------+---------------+-------------------------------------+
| :class:`~.PointerTo`   |               | An object that may appear multiple  |
|                        |               | times in the single representation. |
+------------------------+---------------+-------------------------------------+

.. _strings-of-things:

Strings Of Things
-----------------

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
----------------------

The library types associated with time values appear below;

+----------------------+----------------+----------------------------------------------+
| Library              | Python         | Notes                                        |
+======================+================+==============================================+
| :class:`~.ClockTime` | ``float``      | A local time, i.e. ``float``.                |
+----------------------+----------------+----------------------------------------------+
| :class:`~.TimeSpan`  | ``float``      | A local time delta, i.e. ``float``.          |
+----------------------+----------------+----------------------------------------------+
| :class:`~.WorldTime` | ``datetime``   | A date, time and timezone.                   |
+----------------------+----------------+----------------------------------------------+
| :class:`~.TimeDelta` | ``timedelta``  | A time delta, i.e. t2 - t1.                  |
+----------------------+----------------+----------------------------------------------+

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
---------------

The proper type expression for an object that may appear at multiple
points in a single encoding operation, looks like;

.. code-block:: python

    lc.PointerTo(UserDefined(Person))

The library uses these "pointers" to implement graphs, e.g. linked-lists, trees
and networks.
