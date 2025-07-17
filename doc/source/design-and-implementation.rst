.. _design-and-implementation:

Design And Implementation
*************************

The **layer-cake** library has significant goals but also includes tradeoffs and compromises. It would
be nice if **layer-cake** was available for every development language and for every platform. Instead
there is one development language and a significant number of supported platforms.

This section of the documentation captures any design or implementation detail that might be useful
to the user.

Implementation Language
=======================

**Layer-cake** is implemented in Python after years of work in C/C++. Moving to Python delivers **layer-cake** to every
instance of a modern Python environment. The decision to move was not after determining that Python was a better
language, it was about reach. A distributed computing technology that is only available to a small section
of the development community can barely refer to itself in such grand terms. To reach the same number
of environments with a C/C++ library would take hundreds of build chains and thousands of developer hours.

There is no intention to port **layer-cake** to other languages.

.. _supported-platforms:

Supported Platforms
===================

**layer-cake** has been tested on the following platforms, using Python 3.10+;

* Ubuntu 20+
* Debian 12+
* Raspberry Pi OS 12+ (debian-based)
* macOS 14 Sonoma
* Windows 11+ (no ``layer-cake`` CLI, i.e. process orchestration)

Other Linux Platforms
+++++++++++++++++++++

Any combination of a modern Python interpreter (3.10+) and a Linux-based operating system may support
**layer-cake** operation. Only those included in **layer-cake** testing are listed in the previous section.

Windows Support
+++++++++++++++

Execution of individual **layer-cake**-based scripts on Windows is supported. Process orchestration using
the ``layer-cake`` CLI is not. **layer-cake** uses the ``signal`` library to implement asynchronous control over
running processes. Limited support for this library on Windows, along with the differences
between \*nix-style filesystems and Windows filesystems (file extensions and path separator) have
delayed the implementation of the ``layer-cake`` CLI for Windows.

.. _lc-address:

Asynchronous Objects, Addresses And Execution
=============================================

The model of execution was adopted from `SDL <https://en.wikipedia.org/wiki/Specification_and_Description_Language>`_.
This model is based around signal processing where signals are analogous to messages. Objects are created,
send and receive messages, create new objects, and terminate.

There is a single internal map of objects, where the key is an integer and the value is one of the
supported object types, i.e. a function with its own thread, or a machine. The integer key is often
referred to as a **layer-cake** address. Every async application starts with the creation of a single object,
using :func:`~.create()`.

An async application may accumulate tens of thousands of objects. Attempting to create large
numbers in a burst may encounter message overflow problems (refer to following paragraps).

Objects that are implemented as functions cause the allocation of a platform thread. Objects
implemented as machines that use the :class:`~.Threaded` base class also cause the allocation of a thread.
A reasonable maximum number of threads for any process may be around 500, i.e. an async application
with large numbers of objects that are allocated threads, may become adversely affected by the
overhead of thread switching.

Machines that are not assigned to a named thread on the call to :func:`~.bind()` are
assigned to the default thread, created automatically by the async runtime. A thread that
processes messages on behalf of large numbers of objects may become an execution bottleneck
and affect the order of message processing.

Sending messages requires message queues. Message queues are assigned a maximum size of 8192
at creation time. Messages sent to a full queue are discarded - a burst of 10k messages to the
same destination has a good chance of resulting in lost messages. Lost messages are likely to
be a symptom of programming as if there were infinite resources. Redesign the messaging to be
more exchange-like rather than a one-way flood.

Discarding overflow messages is deliberate. The alternative to discarding is blocking until
items are taken off the queue by a consumer. This is considered to be the risky option
(i.e. deadlocks).

.. _lc-message:

Asynchronous Messages
=====================

A message is the unit of data that can be passed around by an asynchronous process. It can move
around inside a process, between threads and machines. It can also move between two processes
over a network connection, or between a process and a disk file.

Messages are either an instance of a registered class (i.e. refer to :func:`~.bind()`) or an
instance of an inline, or anonymous type, such as a table of floats, cube of integers or map
of integers to strings. The latter requires specific handling with :func:`~.def_type`
and :func:`~.cast_to`.

.. _lc-type:

Message Types
=============

A type is special unit of data that describes instances of data, i.e. it is meta data. A
type can be included in a message alongside integers and strings and it is portable. A type
can describe a registered function or class and it can describe inline or anonymous data.
The **layer-cake** type system is more extensive than Python's and is applied more strictly.
It includes types such as;

* boolean, integer, floating point
* ASCII strings, unicode, byte blocks
* enumerations,
* user-defined function or class
* vector, array, deque,
* set, map,
* type,
* address,
* any,
* pointer

Python type hints are converted to internal **layer-cake** types as necessary.

.. _lc-object-type:

Object Types
============

An object type is a function or class registered using :func:`~.bind()`, and then passed to
the global :func:`~.create` function or the :meth:`~.Point.create` method to form an instance
of an asynchronous object. An object type is not a portable value though there is the ability
to convert from one to the other, i.e. if :func:`backup()` is a registered Python
function, :class:`Schedule` is a registered Python class and ``callback`` is a member of
that class;

.. code-block:: python

	import layer_cake as lc

	class Schedule(object):
		def __init__(self, when: datetime=None, callback: lc.Type=None):
			self.when = when
			self.callback = callback

	..
	s = Schedule(when=when, callback=lc.UserDefined(backup))

Instances of :class:`Schedule` can be sent over the network or saved to a disk file. Successful
decoding is dependent on the presence of the matching registrations in the decoding process.

Async Timers
++++++++++++

Timers are implemented as messages that are processed by the same mechanisms as any other
message. An object requests a timer using :meth:`start()` and an instance of the
specified timer will arrive after the specified time period. This arrangement means that
timers can be applied to anything - there is no need for each individual operation to provide
a timing option. A timer can also be applied to an expected sequence of operations, e.g. a
:class:`T1` message can be used to indicate that the sequence of operations *A*, *B* and *C*
took too long.

Timers will arrive after a period *at least as long* as the specified time. Timers can be
delayed in heavy traffic. Internally, monotonic time values are used. Starting a timer that
is still pending is effectively a restart. The countdown continues with the new period.

Timers are not intended to be realtime. They run a bit faster than human speed rather than
machine speed. Accuracy is around 0.25s. Timer values at a finer resolution have no
effect, i.e. with a value of 2.1s the timer message will arrive some time after 2.0s
has passed.

To cancel an outstanding timer use :meth:`cancel()`. There is always the chance
that timer messages can pass each other by in message queues - its possible to receive
a timer after it has been cancelled. The standard approach to message processing should
ensure these are ignored.

.. _publish-subscribe-networking:

Publish-Subscribe Networking
============================

Delivering multihosting solutions is obviously more complex than delivering a single process. Installation and maintenance
of software materials that are spread across multiple machines is probably the first difficulty that comes to mind. Two
further aspects are tackled head-on by the **layer-cake** library. These are;

* network addresses  
* session management

Network addresses must be assigned and configured into the solution at the correct points, and there must be a quality
retry strategy around every attempt to establish a connection. These activities are critical. Without them you have a
solution that is broken or poised to break. The next software update will expose that client that did not take connection
retries seriously enough.

The **layer-cake** library provides the :func:`~.publish()` and :func:`~.subscribe()` functions. These are almost drop-in
replacements for the :func:`~.listen()` and :func:`~.connect()` functions, respectively. Together they deliver publish-subscribe
networking, or just pubsub. Switching to pubsub means no more network address administration. It also means no more connection
retry code.

A service registers itself under an agreed text name, and a client registers interest in that same name. The service
receives :class:`~.Delivered` and :class:`~.Dropped` messages delimiting each successful session and the client
receives :class:`~.Available` and :class:`~.Dropped` messages. These are analogous to the :class:`~.Accepted`, :class:`~.Connected`
and :class:`~.Closed` messages that are generated by the use of :func:`~.listen()` and :func:`~.connect()`.

Internally, sessions between subscriber and publisher are established using :func:`~.connect()`. The reason for different
notification messages is that the underlying transport may be shared, i.e. if there are two subscriptions in the one process
to the same service name, only one transport will be created. Sharing or multiplexing of sessions over a single transport is
an innate capability of **layer-cake** messaging. Both subscribers will receive the :class:`~.Available` message, but
the :class:`~.Closed` message cannot be used to terminate the session as the underlying transport may still be in use.
Subscribers and publishers should use :func:`~.clear_subscribed()` and :func:`~.clear_published()` respectively, in those
contexts where use of a directory name is ending but the process is not. Termination of a **layer-cake** process automatically
achieves the same thing.

If the number of pubsub sessions on a transport falls to zero, there is an automated shutdown of the transport. The
shutdown procedure honours a short grace period of no further activity, before the transport is actually closed.

Network I/O And Safety Measures
===============================

Sending messages across networks uses the same method (i.e. :meth:`send()`) used to
send to any async object and uses the same underlying message processing machinery. Bursts
of large numbers of network messages may result in overflow of a message queue.

There are no real limits imposed on the sending end of network messaging. Any message type
registered using :func:`bind()` will be transferred across the network. Each
messaging socket (i.e. accepted or connected) is assigned its own outbound message queue
and streaming buffers. Large messages may result in processing bottlenecks and memory
fragmentation. A reasonable maximum message size may be around 100k. This refers to the
quantity of memory consumed by the Python application message.

All socket I/O is based around blocks of 4096 bytes.

Several limits are imposed at the receiving end of network messaging. The encoded representation
of a message (the JSON byte representation) cannot exceed 1Mb and there are further checks
applied to frame dimensions. Any message that fails to meet requirements results in an immediate
shutdown of the associated socket and a session control message is sent to the relevant party
(i.e. :class:`Closed`. These are measures to defend against messages that somehow arrive corrupted
and the possibility of bad actors.

Long Term Connections And Keep-Alives
=====================================

Long term connections are at risk of failures in the operational environment. These include
events such as dropout of network infrastructure (e.g. someone pulls the plug on a network
switch) and discarded NAT mappings. The significance of these events is that they are likely
to go unreported. There will be no related activity in the local network stack and therefore
no :class:`~.Closed` message propagated to the application.

Enabling the ``self_checking`` flag on the call to :func:`~.connect` activates
a keep-alive capability. After a period of inactivity - no messages sent or received - the
library will perform a low-level enquiry-ack exchange to verify the operational status of
the network transport and the remote application. This may result in either an error in
the network stack or a timeout, further resulting in a :class:`~.Closed` message.

Inactivity is defined to be a period of two minutes with no message activity. The enquiry-ack
exchange is expected to complete within five seconds.

Long term connections are good in that they improve responsiveness. Messages can be sent
in response to a local event without having to wait for a successful connection. On the
other hand, regular housekeeping messages are noisey and may create their own problems
at scale.

Connections initiated with a defined task and an expected completion, in the style of a
file transfer, do not need a keep-alive capability. The presence of the associated machinery
may be an unnecessary complication.

By default the ``self_checking`` flag is disabled. Note also that all connections
established as a result of :func:`~.subscribe` calls have ``self_checking`` *enabled*.

Logging associated with keep-alive activity is deliberately limited to the recording of
a few initial enquiry-ack exchanges. This is to provide evidence that the feature is
operational and also to preserve the value of the logging facility, i.e. useful log
entries would be pushed out by the recording of endless enquiry-ack exchanges.

Data Types And Portability
==========================

A type system is imposed on all messages and applies to both file and network operations.

Network messaging under **layer-cake** is *fully-typed*, i.e. applications send and receive instances
of application types. This is part of the initiative to remove networking details from the application
code and requires that the library knows the internal details of each message. The type information forms
the basis for marshaling and encoding activities.

The type system is static in nature rather than dynamic. This is a design decision and motivated by goals
of portability and robustness. Data based on a static type system has an increased chance of moving between
languages, e.g. Python and C++. Robustness is improved in the sense that checks that would probably be
needed in the application instead occur automatically in the messaging machinery, e.g. if a list of
3 GPS coordinates is expected.

Implementation of data transfer between **layer-cake** (i.e. Python) and some other language, at the *file* level
would be a realistic initiative. This kind of export/import code would need to resolve any mismatches
in the respective type systems, e.g. the Python ``int`` vs the C/C++ ``int``. The chances of a quality
mapping is improved by the presence of the **layer-cake** type system.
