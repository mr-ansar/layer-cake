.. _design-and-implementation:

Design And Implementation
*************************

This section of the documentation captures any design or implementation detail that might be useful
to the user.

Implementation Language
=======================

**Layer-cake** is implemented in Python after years of work in C/C++. Moving to Python delivers **layer-cake**
to every instance of a modern Python environment. The decision to change language was about reach. To reach
the same number of environments with a C/C++ library would take hundreds of build chains and thousands of
developer hours.

There is no current intention to port **layer-cake** to other languages.

.. _supported-platforms:

Supported Platforms
===================

**Layer-cake** has been tested on the following platforms, using Python 3.10+;

* Ubuntu 20+
* Debian 12+
* Raspberry Pi OS 12+ (debian-based)
* macOS 14 Sonoma
* Windows 11+ (see below)

Other Linux Platforms
+++++++++++++++++++++

Any combination of a modern Python interpreter (3.10+) and a Linux-based operating system may support
**layer-cake** operation. Only those included in **layer-cake** testing are listed in the previous section.

Windows Support
+++++++++++++++

Testing on the Windows platform has been recently disabled, while completing a major refactoring
of the codebase.

The most recent round of testing indicated that a modern Python interpreter on a Windows platform should have basic
support (i.e. command-line execution of scripts) and may have full support (i.e. full use of the **layer-cake**
CLI and its process orchestration features).

Testing and full support for Windows is unlikely until Q1 2026.

.. _lc-limitations-and-constraints:

Limitations And Constraints
===========================

There is a single internal map of objects, where the key is an integer and the value is one of the
supported object types, i.e. a function with its own thread, or a machine. Every async application starts
with the creation of a single object, using :func:`~.create()`.

An async application may contain hundreds of thousands of async objects. Attempting to create large numbers
(e.g. over 10K) in a single sweep may encounter message overflow problems (refer to following paragraps).
Accumulating much larger numbers - over time - does not carry the same risk.

Objects that are implemented as functions cause the allocation of a platform thread. Machines based on
the :class:`~.Threaded` class also cause the allocation of a thread - machines based on :class:`~.Point`
do not.

A reasonable maximum number of threads for a typical host may be in the range of 500-1000, i.e. an async
application with large numbers of objects that are allocated threads, may become adversely affected by the
overhead of context switching. A similar issue exists around the number of processes running on a host.
There needs to an awareness of the total numbers of threads and processes that you might be creating
at runtime. The library does nothing to prevent the creation of assemblies that are not in your own
best interests.

Machines based on :class:`~.Point` that are not assigned to a named thread, on the call to :func:`~.bind()`,
are assigned to a default thread (created automatically by the async runtime). A thread that processes
messages on behalf of large numbers of objects may become an execution bottleneck and affect the order
of message processing.

Sending messages requires message queues. Message queues are assigned a maximum size of 16384 at creation
time. Messages sent to a full queue are discarded - a burst of 20k messages to the same destination has a
good chance of resulting in lost messages. Lost messages are likely to be a symptom of programming as if
there were infinite processing resources. Redesign the messaging to be more exchange-like rather than a
one-way flood.

Discarding overflow messages is deliberate. The alternative to discarding is blocking until items are taken
off the queue by a consumer. This would put the process at risk of deadlocks.

.. _publish-subscribe-networking:

Publish-Subscribe Networking
++++++++++++++++++++++++++++

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
+++++++++++++++++++++++++++++++

Sending messages across networks uses the same method (i.e. :meth:`send()`) used to
send to any async object and uses the same underlying message processing machinery. Bursts
of large numbers of network messages may result in overflow of a message queue, i.e. > 10K.

There are no real limits imposed on the sending end of network messaging. Any type of message
(i.e. registered class instance or constructed type) will be transferred across the network.
Each messaging socket (i.e. accepted or connected) is assigned its own outbound message queue
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
