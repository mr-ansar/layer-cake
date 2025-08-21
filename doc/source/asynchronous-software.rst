
.. _lc-asynchronous-software:

Asynchronous Software
*********************

The model of execution was adopted from `SDL <https://en.wikipedia.org/wiki/Specification_and_Description_Language>`_.
This model is based around signal processing where signals are analogous to messages. Asynchronous objects are
created, they send and receive messages, create new objects, and terminate. There are many similarities with initiatives such
as `UML <https://www.omg.org/spec/UML/2.5.1/PDF>`_ and *active objects*.

.. _lc-object-type:

Creation of an object requires an *object type*. This can either be a defined function or a class; the latter
is known as a *machine*. In both cases the type must be registered. Creation produces an *object instance* of
the given type and an *object address*. All interaction with the object is through the sending of messages
to that address. There is no direct access to the underlying object (e.g. the instance of a machine class).

.. _lc-address:

Addresses are the unique, runtime identities of **layer-cake** objects. In typical use they can be
thought of as serial ids. Sending a message involves a message and an address. The address is used
to lookup the associated destination object in a single, thread-safe table; the message is added to
a queue and is eventually delivered to the expected object.

.. _lc-message:

Messages are instances of registered classes, or an instance of a *constructed type* such as a table of integers
or a list of strings. This union of class-or-constructed is captured by the *any* concept (:class:`~.Any`). The
completion of an object sends a notification message to the parent containing the returned value as an instance
of *any*.

.. _lc-receiving:

Receiving messages is a managed process. There are input primitives available to function objects, and machine
objects have dedicated message dispatching machinery. In both cases the result is application-ready data and
a *receive context* populated with associated information. This includes the *return address* so that the
receiver knows who to reply to. The context also includes the *received type* for those scenarios where the
application needs to disambiguate the application data, e.g. ``list[int]`` vs ``list[list[float]]``. Machine
dispatching has that sophistication built in.

Primary uses of the *any* concept include the return values of objects and the sending of messages. When
dealing with instances of *any* there is always the potential need to *cast back* (:func:`~.cast_back`) the
value to its application-ready state. As described above, this is automated in the receive machinery. When
sending there is always the potential need to prepare application-ready data with a *cast to* (:func:`~.cast_to`)
the *any* form.

Messaging that involves only instances of class-based messages gets a free pass. Class instances are one of
the accepted forms of *any*. Return values and received messages can be accessed without additional processing
and the same is true when sending those instances on to other parties. The only case that really requires
attention is when an object is operating as an intermediary between objects that may or may not be using
constructed types, i.e. receive from one object and forward it to another. In these cases it is safest to
apply :func:`~.cast_to`, to everything that is sent. Where the data happens to be a class instance this is
a no-op.

.. note::

	Another way to articulate the underlying issue is to consider the expression ``isinstance(message, list[float])``.
	If Python accepted this use of hints, there would be no need for *any*, *cast to* and *cast back*.

.. _lc-arranging-for-a-callback:

Arranging For A Callback
========================

Callbacks are an extension of the receive machinery, triggered by termination notifications. They involve
an address, a function and a set of named parameters. The result is a saved *callback context*;

.. code-block:: python

	def respond(self, response, args):
		self.send(lc.cast_to(response, self.returned_type), args.return_address)

	a = self.create(texture, x=m.x, y=m.y)
	self.on_return(a, respond, return_address=self.return_address)

When a parent receives a termination message from a child object, it looks for the saved context using
the :meth:`~.Point.debrief` method and checks for the context type;

.. code-block:: python

	while True:
		m = self.input()
		if isinstance(m, Xy):
			pass
		elif isinstance(m, lc.Returned):
			d = self.debrief()
			if isinstance(d, lc.OnReturned):
				d(self, m)
			continue

The callback context is defined as a callable object. Calling that object is effectively a call to the
saved function.

The saved function receives the application-ready data and any arguments saved in the callback context.
Full type information is available in the receive context as "returned type", so as not to collide with
"received type". The return address must be managed deliberately, as the address at the time of callback
creation has been clobbered by the arrival of intervening messages (e.g. the termination). Saving that
original return address as an argument in the callback context is common.

.. _simulation-of-synchronous-calling:

Simulation Of Synchronous Calling
=================================

The simplest use of callbacks is to simulate a synchronous call within the asynchronous environment. This
is defined to be a request-response exchange with an asynchronous object at a known address. A special
facility exists for exactly this purpose (i.e. :class:`~.GetResponse`).

.. code-block:: python

	def respond(self, response, args):
		self.send(lc.cast_to(response, self.returned_type), args.server_address)

	a = self.create(lc.GetResponse, request, server_address)
	self.on_return(a, respond, server_address=self.server_address)

The combination of :class:`~.GetResponse` and :meth:`~.Point.on_return` arranges for execution to resume
at the :func:`~.respond` function. The application-ready data is available in the ``response`` argument.
This small fragment of code supports multiple, concurrent calls to ``server_address``, and the return of
the correct response to the correct calling party. The :func:`~.cast_to` is needed to cover those cases
where the server returns a *constructed type*.

Where there are multiple calls to be made and there are no dependencies between the individual calls
(i.e. where request information for one call comes from the response of another), the calls can be
performed :class:`~.Concurrently`;

.. code-block:: python

	def respond(self, collated, args):
		response = collated[0]
		selection = collated[1]
		identity = collated[2]
		..
		self.send(response, args.return_address)

	a = self.create(lc.Concurrently,
		(request, worker_address),
		(query, db_address),
		(credentials, authentication_address)
	)
	self.on_return(a, respond, return_address=self.return_address)

The thread of execution splits into three involving ``worker_address``, ``db_address`` and
``authentication_address``. On completion of the slowest, execution resumes at the :func:`respond`
function and the individual responses are available in ``collated``, at a corresponding ordinal
position.

.. note::

	The type hint for ``collated`` is ``list[Any]`` - individual elements may need a :func:`~.cast_back`.
	This example also omits all error handling; ``isinstance(collated, lc.Faulted)`` may be true
	(e.g. :class:`~.TimedOut`).

As before with the use of :class:`~.GetResponse`, this code supports multiple, concurrent
instances of the three-way split.

It is possible to chain the use of :class:`~.GetResponse` and :class:`~.Concurrently`. The chain is
started with :meth:`~.Point.on_return` and then :meth:`~.Point.continuation` passes the same ``args``
on to the next callback function. Empty slots may be reserved in ``args`` at the beginning of the
chain, to be filled in at some later point.

Calling A Process
=================

Multithreading is supported by function objects and multiprocessing is supported by a special machine;
:class:`~.ProcessObject`. In both cases there is the ability to create instances of the thread or process
and to expect a termination notification at some point in the future. The process machine accepts a
parameter identifying the executable to be loaded. Remaining arguments are forwarded to the process as
argument strings. On exit of the process, a return value is decoded from ``stdout`` and inserted into the
termination notification.

.. _lc-sending-messages-across-networks:

Sending Messages Across Networks
================================

Networking is integrated seamlessly into asynchronous operation. Special "listen" and "connect" functions
accept network address information and arrange for the establishment of a network transport. Notifications
are sent to the connecting and listening objects from special new objects, created at each end. These objects
represent the new transport for the life of the connection. Replying to these notifications (i.e. sending to
the new object) results in the transfer of the reply message across the transport to the remote object. A
client that replies to a "connected" notification with a "hello" message is sending a greeting across the
network, to the server that just received an "accepted" notification.

**Layer-cake** addresses are capable of referring to objects that are located at the remote end of a network
connection. There is no special handling required of local vs remote addresses. They can all be compared,
copied, assigned and used as ``dict`` keys, in a homogeneous fashion. They can also be included in messages
and sent over network transports. The receiver is free to use such addresses, and messages sent to these
addresses will be routed to the proper party.

Addresses are *portable*. This behaviour applies across complex connection graphs.

Processes As Loadable Libraries
===============================

Multiprocessing and networking are combined to implement a process-based "loadable library". Registering
an object type with a special argument marks that object as loadable. If the process object encounters
an object type defined in that way it automatically opens a network transport between the parent and child
processes. Messages sent to the process object in the parent, are received by the main object in the
child process, using standard receive primitives. Responses find their way back to the original sender
in the parent.

.. _lc-networking-without-network-addresses:

Networking Without Network Addresses
====================================

A form of networking known variously as publish-subscribe or `zeroconf <http://www.zeroconf.org/>`_ is
available through a pair of special "publish" and "subscribe" functions. This can be used to construct
groups of processes that communicate with each other to some collective purpose. A distinguishing feature
of publish-subscribe networking is the complete lack of network administration, i.e. all assignment of
IPs and port numbers, and the associated configuration of clients and servers, is fully automated. Groups
connected in this way within a single host, are known as *composite processes*. Publish-subscribe
networking can also be extended over multiple hosts.

.. _lc-types-and-registration:

Types And Registration
======================

There are two distinct type systems to consider when using the **layer-cake** library. There is the
Python type system known through a set of keywords such as ``int``, ``bool`` and ``dict``, and as type
hints such as ``list[float]`` and ``dict[string,list[int]]``. There is also the **layer-cake** type
system that introduces names such as ``Boolean``, ``Float8`` and ``VectorOf(UserDefined(Customer))``.

To deliver on design goals there are types that exist in **layer-cake** that have no real equivalent in
Python, e.g. arrays, pointers and addresses. The presence of arrays allows automated dimension checking
that would otherwise have to exist in application code. **Layer-cake** is also capable of sending complex
graph data (e.g. trees and linked lists that include pointers) across network transports. Addresses - and
the ability to send address values across networks - are discussed in the previous section.

The bulk of type information required for **layer-cake** operation can be acquired through Python
type hints on function and class definitions. The library detects these hints, converts them to
**layer-cake** equivalents and registers them.

Registration not only extracts the type information from associated hints but also enters all
discovered types into an internal table of known types. For two distinct reasons, all type processing
must be completed before the first asynchronous object is created, i.e. the main application object.
The first reason is that the type system can experience heavy use (comparisons during dispatching) and
allowing for runtime registration of types would require thread-safety measures around access to the
table. The second reason is that type comparisons are carried out using string representations that
are compiled during registration. It is much quicker to compare strings such as ``"list<list<float>>"``
and ``"map<uuid,db.Customer>"`` rather than walking tree representations of the same details, e.g. Python
type hints or instances of :class:`~.Portable`.

.. _lc-input-processing:

Input Processing
================

Processing of messages happens in two contexts. Function objects read from the message queue using input
primitives such as :meth:`~.Buffering.input` and :meth:`~.Buffering.select`. Definition of machine objects
includes :ref:`message dispatching<stateless-machines>`;

.. code-block:: python

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m
	..

A standard comparison technique is used to check if the :func:`~.listen` operation was successful or
not. The :meth:`~.Buffering.input` method populates the receive context (i.e. ``self``) with additional
details such as the ``received_type`` and returns an item of application-ready data. This works fine for
all class-based messaging. However, it is not a complete approach in the presence of *constructed types*.
There is no simple use of ``isinstance`` that can distinguish between a *list of integers* or a
*list of Customers*. As items of application data, instances of both these types present as ``list``.

The proper approach is to use :meth:`~.Buffering.select`;

.. code-block:: python

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		lc.listen(self, server_address, http_server=SERVER_API)
		m, i = self.select(lc.Listening, lc.NotListening, list[int], list[Customer])
		if i == 0:
			pass
		elif i == 1:
			return m
		..

Along with the application data, the ordinal number of the matched type is returned to the
caller, i.e. a value of 2 indicates that the application data is a list of integers. For the
best performance there is the ability to pre-compile the selection machinery, using

:func:`~.select_list`;

.. code-block:: python

	listening_select = lc.select_list(lc.Listening, lc.NotListening, list[int], list[list[int]])

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		lc.listen(self, server_address, http_server=SERVER_API)
		m, i = self.select(listening_select)
		if i == 0:
			pass
		elif i == 1:
		..

.. _functions-and-machines:

Functions And Machines
======================

This section presents the proper definition of the available :ref:`object types<lc-object-type>`, i.e. functions,
stateless machines and stateful machines (FSMs).

Function-Based Objects
++++++++++++++++++++++

An example of a **layer-cake** function object is presented below;

.. code-block:: python
	:linenos:
	:emphasize-lines: 7,15,17

	# test_function_2.py
	import random
	import layer_cake as lc

	random.seed()

	def texture(self, x: int=8, y: int=8) -> list[list[float]]:
		table = []
		for r in range(y):
			row = [None] * x
			table.append(row)
			for c in range(x):
				row[c] = random.random()

		return table

	lc.bind(texture)

Definition of a function object has the following elements;

.. list-table::
   :widths: 25 25 75
   :header-rows: 1

   * - Element
     - Example
     - Notes
   * - **Name** (7)
     - ``texture``
     - *name of the function*
   * - **Arguments** (7)
     - ``x: int=8``
     - *named argument with type hint*
   * - **Return type** (7)
     - ``list[list[float]]``
     - *default return type hint*
   * - **Return** (15)
     - ``return table``
     - *auto-conversion to declared type*
   * - **Registration** (17)
     - ``lc.bind(texture)``
     - *registration of the function*

Arguments with no declared type information are invisible to **layer-cake**. The declared return
type is used to automate a call to :func:`~.cast_to`, ensuring the contents of the :class:`~.Returned`
message carry the appropriate type information. Where the return value is an object such as an instance
of :class:`~.Faulted` the automated call is a *no-op* - the object receives pass-through behaviour.
The default return type is :class:`~.Any`.

The :func:`~.bind` function provides additional features, including declaration of **layer-cake** type
information (e.g. :class:`~.ArrayOf`).

.. _stateless-machines:

Stateless Machines
++++++++++++++++++

An example of a **layer-cake** stateless machine is presented below;

.. code-block:: python
	:linenos:
	:emphasize-lines: 3,4,9,12,15,16,18,24

	import layer_cake as lc

	class Delay(lc.Point, lc.Stateless):
		def __init__(self, seconds: float=3.0):
			lc.Point.__init__(self)
			lc.Stateless.__init__(self)
			self.seconds = seconds

	def Delay_Start(self, message):
		self.start(lc.T1, self.seconds)

	def Delay_T1(self, message):
		self.complete(lc.TimedOut(message))

	def Delay_Stop(self, message):
		self.complete(lc.Aborted())

	DELAY_DISPATCH = [
		lc.Start,
		lc.T1,
		lc.Stop,
	]

	lc.bind(Delay, DELAY_DISPATCH, thread='delay')

Definition of a stateless machine has the following elements;

.. list-table::
   :widths: 25 25 75
   :header-rows: 1

   * - Element
     - Example
     - Notes
   * - **Name** (3)
     - ``Delay``
     - *name of the machine class*
   * - **Dedicated thread** (3)
     - ``lc.Point``
     - *selection of threading model*
   * - **Machine type** (3)
     - ``lc.Stateless``
     - *selection of stateless or stateful*
   * - **Arguments** (4)
     - ``seconds: float=3.0``
     - *named arguments with type hint*
   * - **Transition functions** (9,12,15)
     - ``Delay_Start``
     - *function to call on receive of Start*
   * - **Termination** (16)
     - ``self.complete(lc.Aborted())``
     - *destroy this machine, send Returned*
   * - **Dispatching specification** (18)
     - ``DELAY_DISPATCH = [...]``
     - *description of message processing*
   * - **Registration** (24)
     - ``lc.bind(Delay, ...)``
     - *registration of the machine*

Machines may derive from :class:`~.Point` or :class:`~.Threaded`. Use of the
latter causes the allocation of a thread for each instance of the machine. Machines
will also derive from either :class:`~.Stateless` or :class:`~.StateMachine`.

Transition function names follow the *class*\_ *message* convention, i.e when
the ``Delay`` class receives the ``Start`` message the ``Delay_Start`` function
is called. Calling the :meth:`~.Point.complete` method is the only means of
terminating a machine.

Unexpected messages are dropped on the floor. To catch these messages the :class:`~.Unknown`
class can be included in the dispatching. Appropriate processing of the ``message``
argument in that transition function is the responsibility of the machine.

If the machine receives a message that is not registered within the local process, i.e.
over a network transport, this is folded into the :class:`~.Incognito` message. This
type can also appear in the dispatching information.

Return statements terminate the transition function as expected, but any returned
value is ignored. The return type for a machine is declared at registration time
(see the ``return_type`` argument on the :func:`~.bind` function).

Unless specified otherwise, machines based on  :class:`~.Point` are all assigned
to a single, standard library thread. Larger and performance-focused applications
will pay more attention to the named threads feature offered at registration
time (24).

Stateful Machines (FSMs)
++++++++++++++++++++++++

An example of a **layer-cake** FSM is presented below;

.. code-block:: python
	:linenos:
	:emphasize-lines: 3,7,10,12,15,17,19,20,22,25,28,31,43

	import layer_cake as lc

	class INITIAL: pass
	class IDLE: pass
	class COOKING: pass

	class Toaster(lc.Threaded, lc.StateMachine):
		def __init__(self):
			lc.Threaded.__init__(self)
			lc.StateMachine.__init__(self, INITIAL)

	def Toaster_INITIAL_Start(self, message):
		return IDLE

	def Toaster_IDLE_TurnOn(self, message):
		self.start(lc.T1, message.how_long)
		return COOKING

	def Toaster_IDLE_Stop(self, message):
		self.complete(lc.Aborted())

	def Toaster_COOKING_T1(self, message):
		return IDLE

	def Toaster_COOKING_TurnOff(self, message):
		return IDLE

	def Toaster_COOKING_Stop(self, message):
		self.complete(lc.Aborted())

	TOASTER_DISPATCH = {
		INITIAL: (
			(lc.Start,), ()
		),
		IDLE: (
			(TurnOn, lc.Stop), ()
		),
		COOKING: (
			(lc.T1, TurnOff, lc.Stop), ()
		),
	}

	lc.bind(Toaster, TOASTER_DISPATCH)

Definition of a FSM has the following elements;

.. list-table::
   :widths: 25 25 75
   :header-rows: 1

   * - Element
     - Example
     - Notes
   * - **States** (3)
     - ``INITIAL``
     - *declaration of machine states*
   * - **Name** (7)
     - ``Toaster``
     - *name of the machine class*
   * - **Dedicated thread** (7)
     - ``lc.Threaded``
     - *selection of threading model*
   * - **Machine type** (7)
     - ``lc.StateMachine``
     - *selection of stateless or stateful*
   * - **Initialize state** (10)
     - ``__init__(self, INITIAL)``
     - *the starting state for this machine*
   * - **Transition functions** (12,15,...)
     - ``Toaster_INITIAL_Start``
     - *function to call on receive of Start*
   * - **Change state** (17)
     - ``return COOKING``
     - *move to the next state*
   * - **Termination** (20)
     - ``self.complete(lc.Aborted())``
     - *destroy this machine, send Returned*
   * - **Dispatching specification** (31)
     - ``TOASTER_DISPATCH = [...]``
     - *description of message processing*
   * - **Registration** (43)
     - ``lc.bind(Toaster, ...)``
     - *registration of the machine*

All the potential states of the machine are declared as classes. This allows
symbolic state information to be included in logging associated with the machine.
One of the declared states must be used to intiialize the machine.

Transition function names follow the *class*\_ *state*\_ *message* convention, i.e when
the ``Toaster`` class receives the ``Start`` message in the ``INITIAL`` state,
the ``Toaster_INITIAL_Start`` function is called. Calling the :meth:`~.Point.complete`
method is the only means of terminating a machine.

Return statements are used to change the state of the machine, i.e. ``return COOKING``
moves the machine to the ``COOKING`` state. Processing of the next message will involve
one of the matching transition functions, e.g. ``Toaster_COOKING_T1``. Every transition
function must return a valid state class. Any other return value will produce a fault.
The return type for a machine is declared at registration time (see the ``return_type``
argument on the :func:`~.bind` function).

Description of message dispatching involves a map. Each entry has a state class as
the key and a list of messages expected in that state. FSM dispatching supports 2 lists
in each state. The first lists the expected messages and the second lists the messages
to be saved for deferred processing.

Creation Of Asynchronous Objects
++++++++++++++++++++++++++++++++

Once defined and registered, instances of object types are started using :meth:`~.Point.create`;

.. code-block:: python
	:linenos:
	:emphasize-lines: 5

	# Callback for on_return.
	def respond(self, response, args):
		self.send(lc.cast_to(response, self.returned_type), args.return_address)

	a = self.create(texture, x=m.x, y=m.y)
	self.on_return(a, respond, return_address=self.return_address)

Additional arguments, e.g. ``x=m.x``, are forwarded to the associated function or class.
Thread allocation is controlled by the object type, or the use of :class:`~.Point` or
:class:`~.Threaded` base classes or the declaration of a thread name, e.g. ``thread='name'``.

Any registered object type can also be passed to :func:`~.create`, as the main process
object;

.. code-block:: python
	:linenos:
	:emphasize-lines: 2

	if __name__ == '__main__':
		lc.create(texture)


.. _lc-generating-logs:

Generating Logs
===============

Logging is wired into the **layer-cake** runtime. Logs are generated from the moment the
asynchronous runtime is active, at moments such as;

* creation and termination of objects
* sending and receiving messages
* start and termination of processes
* detection of unexpected conditions
* detection of compromising conditions

Description of the information logged can be found :ref:`here<layer-cake-command-logging-information>`.
When a process runs from the command line, the runtime needs to be advised where logging
output should be directed to;

.. code-block:: console

	$ python3 test_server_10.py --debug-level=DEBUG

This not only enables streaming of logging output to ``stderr``, it also selects which levels of logging
will be included in that output. The levels are;

+---------+----------------------------------------------+
| Name    | Notes                                        |
+=========+==============================================+
| FAULT   | Operation has been compromised.              |
+---------+----------------------------------------------+
| WARNING | Proper operation is under threat.            |
+---------+----------------------------------------------+
| CONSOLE | A logical, application-level milestone.      |
+---------+----------------------------------------------+
| OBJECT  | Object-related event - creation, sending.... |
+---------+----------------------------------------------+
| TRACE   | Curated, technical support.                  |
+---------+----------------------------------------------+
| DEBUG   | Uncurated, development stream.               |
+---------+----------------------------------------------+

Selecting ``DEBUG`` ensures that all logging is included in the output stream, i.e. everything from the
selected level and up. To limit logs to those entries relating to service availability, select ``WARNING``.

When a process runs as part of a composite process, i.e. :ref:`run<command-reference-run>`,
the handling is similar except that output includes a column for a process ID. When a composite
process is placed in the background, i.e. :ref:`start<command-reference-start>`, logs are
streamed into a per-process disk storage area. These can be extracted at any time using the
:ref:`log<command-reference-log>` command.

The following methods are available to all machines, to generate custom logging output;

+-------------------------+----------------------------------------------+
| Method                  | Notes                                        |
+=========================+==============================================+
| :meth:`~.Point.fault`   | Operation has been compromised.              |
+-------------------------+----------------------------------------------+
| :meth:`~.Point.warning` | Operation is under threat.                   |
+-------------------------+----------------------------------------------+
| :meth:`~.Point.console` | Logical application.                         |
+-------------------------+----------------------------------------------+
| :meth:`~.Point.trace`   | Curated, technical support.                  |
+-------------------------+----------------------------------------------+
| :meth:`~.Point.debug`   | Free format, uncurated developer text.       |
+-------------------------+----------------------------------------------+
| :meth:`~.Point.sample`  | Stream of key-values.                        |
+-------------------------+----------------------------------------------+

Five of the methods provide the same interface, i.e. ``fault``, ``warning``, ``console``,
``trace`` and ``debug``, tuned for convenient recording of software activity. The positional
arguments are combined into a single string and the key-value arguments are listed
as "name=<value>"" where *value* is the string representation of the Python variable
(i.e. the result of ``str(value)``). The call;

.. code-block:: console

	number = 10
	ratio = 0.25
	self.console( 'Upper', 'left', number=number, ratio=ratio)

will produce;

.. code-block:: console

	^ <00000010>SensorDevice[IDLE] - Upper left (number=10, ratio=0.25)

Refer to the individual methods for further information.

.. _lc-async-timers:

Asynchronous Timers
===================

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

Timers are not intended to be realtime. Accuracy is around 0.25s. Timer values at a finer
resolution have no effect, i.e. with a value of 2.1s the timer message will arrive some time
after 2.0s has passed.

To cancel an outstanding timer use :meth:`cancel()`. There is always the chance
that timer messages can pass each other by in message queues - its possible to receive
a timer after it has been cancelled. In critical areas of software this is solved with the
use of full state-based machines.

.. _folders-and-files:

Folders And Files
=================

This section takes just a few minutes to cover the application persistence available through the :class:`~.Folder`
and :class:`~.file_object.File` types, in the **layer-cake** library.

Registering Application Types
+++++++++++++++++++++++++++++

The first step is to register an application type. Two examples appear in the ``test_api.py`` file, used
throughout the :ref:`multithreading<concurrency-with-multithreading>`, :ref:`multiprocessing<switching-to-multiprocessing>`
and :ref:`multihosting<distribution-with-multihosting>` demonstrations:

.. code-block:: python

	# test_api.py
	import layer_cake as lc

	class Xy(object):
		def __init__(self, x: int=1, y: int=1):
			self.x = x
			self.y = y

	lc.bind(Xy)

	table_type = lc.def_type(list[list[float]])

This module registers the :class:`Xy` class and the ``list[list[float]]`` Python hint. These types
immediately become usable within persistence operations. Classes can include much more than a
few ``int`` members. The library supports types such as ``datetime``, ``set[int]`` and ``dict[str,Xy]``.
A full description of the type system can be found :ref:`here<type-reference>`.

.. note::

	Once registered with **layer-cake**, a type is available at all those points encodings are
	used. This includes file I/O, networking messaging and process integration. The latter refers to
	the arguments passed on a command-line and the encoding placed on ``stdout``.

Write An Object To A File
+++++++++++++++++++++++++

Writing an object into file storage is most conveniently carried out using the :class:`~.File` class:

.. code-block:: python

	f = lc.File('dimension', Xy)
	d = Xy(1, 2)
	f.store(d)

	f = lc.File('table', table_type)
	d = [[3.0], [4.0]]
	f.store(d)

The calls to :meth:`~.File.store` create or overwrite the ``dimension.json`` and ``table.json``
files in the current folder. The contents of the files look like this;

.. code-block:: console

	$ cat dimension.json 
	{
		"value": {
			"x": 1,
			"y": 2
		}
	}
	
	$ cat table.json 
	{
		"value": [
			[
				3.0
			],
			[
				4.0
			]
		]
	}

The files contain an instance of a JSON encoding and the Python objects appear as
the ``value`` member within that encoding. Other members may appear alongside the ``value``
member as the situation demands.

Reading An Object From A File
+++++++++++++++++++++++++++++

Reading an object from file storage is also carried out using the :class:`~.file_object.File` class.
In fact, we can re-use the same instance from the previous sample:

.. code-block:: python

   d = f.recover()

This results in assignment of a fully formed instance of the ``list[list[float]]`` type, to the ``d``
variable. Details like the filename and expected object type were retained in the ``f`` variable and
re-applied here.

A Few File Details
++++++++++++++++++

The operational behaviour of the :class:`~.file_object.File` class can be modified by passing additional
named parameters. These are:

    - ``encoding``
    - ``create_default``
    - ``pretty_format``
    - ``decorate_names``

There are two encodings supported - JSON and XML. Passing an ``encoding`` value overrides the JSON default.
The ``create_default`` parameter affects the behaviour of the :meth:`~.file_object.File.recover` method,
where a named file does not exist. If set to ``True`` the method will return a default instance
of the expected type, rather than raising an exception. By default, file contents are *pretty printed*
for readability and to assist direct editing. Efficiency can be improved by setting this parameter
to ``False``. Lastly, setting the ``decorate_names`` parameter to ``False`` disables the auto-append
of an encoding-dependent file extension, e.g. ``.xml``.

A Folder In The Filesystem
++++++++++++++++++++++++++

A :class:`~.Folder` represents an absolute location in the filesystem. Once created it always refers to
the same location, independent of where the host application may move to::

    >>> import layer_cake as lc
    >>>
    >>> f = lc.Folder('working-area')
    >>> f.path
    '/home/.../working-area'

Internally the :class:`~.Folder` object converts the relative name ``working-area`` to the full pathname.
All subsequent operations on the object will operate on that absolute location. Full pathnames passed to
the :class:`~.Folder` are adopted without change and no name at all is a synonym for the current folder.

Creation of :class:`~.Folder` objects also causes the creation of the associated filesystem folder, where
that folder doesn't already exist. This means that the ``mighty-thor`` folder is assured to exist on disk
once the ``f`` variable has been assigned. Any errors result in an exception.

A Folder Of Folders And Files
+++++++++++++++++++++++++++++

The following code has a good chance of producing a folder hierarchy in your own home folder:

.. code-block:: python

    import os
    import ansar.encode as ar

    home = ar.Folder(os.environ['HOME'])
    work = home.folder('working-area')
    a1 = work.folder('a-1')
    a2 = work.folder('a-2')
    a3 = work.folder('a-3')

Note the use of the :meth:`~.Folder.folder` method to create *sub-folders* from the parent. The
new :class:`~.Folder` refers to the *absolute location* below the parent.

Remembering the :class:`Xy` class;

.. code-block:: python

   f = a1.file('location', Xy)
   d = Xy(x=4, y=4)
   f.store(j)

The :meth:`~.Folder.file` method is used to create a :class:`~.File` object at the absolute location
provided by the parent folder object. The :meth:`~.File.store` method is used to set the contents of
the ``/.../working-area/a-1/location`` file.

.. note::

    The parameters passed on creation of a :class:`~.Folder` are all saved in the object and are
	inherited by the child objects created by the :meth:`~.Folder.folder` and :meth:`~.Folder.file`
	methods, where appropriate.

Listing The Files In A Folder
+++++++++++++++++++++++++++++

A folder is a container of files. These can be *fixed decorations* on a known hierarchy of folders,
or they can be a dynamic collection, where the set of files available at any one time is unknown.
This is the case for a spooling area where jobs are persisted until completed or abandoned. The next
few paragraphs are relevant to folders that behave like spooling areas.

Assuming that ``spool`` is a :class:`~.Folder` of inbound job objects, checking for new work looks
like this;

.. code-block:: python

   received = [m for m in spool.matching()]

The :meth:`~.Folder.matching` generator method returns a sequence
of the filenames detected in the folder. Given the following folder listing:

.. code-block:: console

    $ ls /.../spool
    2888-43c4-998f-3b5671f69459.json  4409-4182-a1fc-dde4004ccbe9.json
    549d-4ba9-9a08-f77b50540c92.json  2856-4e96-bc0b-3840ae3b2c6a.json
    3128-4f85-9729-691661b55682.json  2eaf-4efb-b07a-aa1ad6e67d04.json
    631b-4f18-9207-0e39940a668b.json  1fae-4dc2-b274-149f7520bed0.json
    4995-40a3-8ccd-116bcf78fd83.json  5f26-4d12-8276-b615244edc4e.json
    3dec-4518-be5b-953065216afc.json  b11b-4d55-8168-cdeab30ae771.json

The :meth:`~.Folder.matching` method will return the sequence "2888-43c4-998f-3b5671f69459",
"4409-4182-a1fc-dde4004ccbe9", "549d-4ba9-9a08-f77b50540c92", etc. The method automatically
truncates the file extension resulting in a name suitable for any file operations that might
follow. As always, this automated handling of file extension can be disabled by
passing ``decorate_names=False`` on creation of the ``spool`` :class:`~.Folder` object.

The folder object can be configured to filter out unwanted names from folder listings. Pass
an `re` (i.e. regular expression) parameter at creation time;

.. code-block:: python

	import layer_cake as lc

	..
    spool = lc.Folder('spool', tip=Job, re='^[-0-9a-fA-F]{27}$')

.. note::

    The ``tip`` parameter is optional for the :class:`~.Folder` class, unlike for
	the :class:`~.File` class. For this reason it must be named.

This brute-force expression will cause the ``spool`` folder object to limit its attention to
those filenames composed of 27 hex characters and dashes. Internally the expression match is
performed on the truncated version of the filename - with no file extension. The folder can
then contain fixed decorations and the :class:`~.Folder` methods involved in processing dynamic
job content will not "see" them.

It is also valid to create several :class:`~.Folder` objects that refer to the same absolute
location but are created with different `re` expressions. As long as the expressions describe
mutually exclusive names the different dynamic collections can exist alongside each other.

Of course, the simplest arrangement is for any dynamic content to be assigned its own dedicated
folder. Considering the ease with which folders can be created "on disk" there is less justification
for maintaining folders with mixed content.

Working With A Folder Of Files
++++++++++++++++++++++++++++++

The :meth:`~.Folder.each` method is similar to :meth:`~.Folder.matching` except that it returns
a sequence of ready-made :class:`~.File` objects. This means that the object inside the file is
one method call away;

.. code-block:: python

    for f in spool.each():
        j = f.recover()
		if worked(j):
        	f.store(j)

The :meth:`~.File.recover` method, introduced in a previous section, is being used to load the
file contents into a ``j``. The caller is free to process the job and perhaps save the results
back into the file.

Yet another method exists to further automate the processing of folders. The :meth:`~.Folder.recover`
method goes all the way and returns a sequence of the decoded job objects. Actually, it returns a
2-tuple of 1) a unique key, and 2) the recovered object. An extra parameter is required at :class:`~.Folder`
construction time;

.. code-block:: python

    kn = (lambda j: j.unique_id, lambda j: str(j.unique_id))

    spool = lc.Folder('spool', tip=Job, re='^[-0-9a-fA-F]{27}$', keys_names=kn)

The `keys_names` parameter delivers a pair of functions to the :class:`~.Folder` object.
These two functions are used internally during the execution of several :class:`~.Folder`
methods, to calculate a key value and a filename.

When the :meth:`~.Folder.recover` method opens a file and loads the contents, this results in an instance
of the ``tip``. The method then calls the first function passing the freshly loaded object. The function
can make use of any of the values within the object to formulate the key. The constraints are that the
result must be acceptable as a unique Python ``dict`` key and that the value is "stable", i.e. the key
formulated for an object will be the same each time the object is loaded.

Whatever that function produces becomes the first element of the ``k, j`` tuple below;

.. code-block:: python

    jobs = {k: j for k, j in spool.recover()}

This gives the application complete control over the key value used by the ``dict`` comprehension. Calling
the :meth:`~.Folder.store` method looks like this;

.. code-block:: python

    spool.store(jobs)

The method iterates the collection of ``jobs`` writing the latest values from each object into a system file.
To do this it uses the second ``keys_names`` function, passing the current object and getting a filename in
return. The function can make use of any of the values within the object to formulate the filename. The constraints
are the same as for recovery.

.. note::

    The :meth:`~.Folder.store` and :meth:`~.Folder.recover` methods are not designed to work
    in the same way. The first is a method that accepts an entire ``dict`` whereas
    the second is a *generator* method that can be used to *construct* a ``dict``,
    by visiting one file at a time.

The individual jobs can be modified;

.. code-block:: python

    for k, j in job.items():
        if update_job(j):
            spool.update(jobs, j)

Or the entire collection can be processed and then saved back to the folder as a
single operation;

.. code-block:: python

    for k, j in jobs.items():
        update_job(j)
    spool.store(jobs)

There are also methods to support adding new jobs, removing individual jobs and lastly, the removal of an
entire collection. This group of methods assumes the ``dict`` object to be the canonical reference, modifying
the related folder contents as needed.

A Few Folder Details
++++++++++++++++++++

The 3 "scanning" methods - :meth:`~.Folder.matching`, :meth:`~.Folder.each` and :meth:`~.Folder.recover`, provide
different styles of folder processing. To avoid the dangers associated with modifications to folder contents during
scanning, the latter 2 methods take filename snapshots using :meth:`~.Folder.matching` and then iterate the snapshots.

The style based on the :meth:`~.Folder.matching` method is the most powerful but also requires the most boilerplate
code. Using the :meth:`~.Folder.each` method avoids the responsibility of creating a correct :class:`~.File` object
and allows for both :meth:`~.File.recover` and :meth:`~.File.store` operations on the individual objects. Lastly,
the :meth:`~.Folder.recover` method requires the least boilerplate but is constrained in one important aspect;
there is no :class:`~.File` object available. Processing a folder with the :meth:`~.Folder.recover` method is a "read-only"
process - without a :class:`~.File` object there can be no :meth:`~.File.store`.

The :meth:`~.Folder.clear` method uses a snapshot to select files for deletion, rather than a wholesale delete of all
folder contents. This preserves the integrity of the folder where it is being shared with fixed files, and other :class:`~.Folder`
objects defined with different `re` expressions.

Snapshots are also used to delete any "dangling" files at the end of a call to :meth:`~.Folder.store`. This ensures
that the set of files in the folder is consistent with the contents of the presented ``dict``.

.. _encrypted-networking:

Encrypted Networking
====================

Encryption is built into the **layer-cake** library. To activate encryption there is a simple boolean
flag on both the :func:`~.listen` and the :func:`~.connect` functions;

.. code:: python

	import layer_cake as lc

    lc.listen(self, requested_ipp, encrypted=False)
	..
	..
    lc.connect(self, requested_ipp, encrypted=False)
	..
	..

For networking to succeed the values assigned at each end must match; either they are both
``True`` or they are both ``False``. The default is ``False``.

Encryption is based around Curve25519, high-speed, elliptic curve cryptography. There is an initial
Diffie-Hellman style exchange of public keys in cleartext, after which all data frames passing
across the network are encrypted. All key creation and runtime encryption/decryption is performed
by the `Salt <https://nacl.cr.yp.to/>`_ library.

All encryption-related communications is transparent to the application process, including the
initial handshaking.

Encrypted Publish-Subscribe Networking
++++++++++++++++++++++++++++++++++++++

Connections are initiated as a consequence of calls to the :func:`~.publish` and the :func:`~.subscribe`
functions. Encryption of these connections is controlled by the ``encrypted`` parameter that can be
passed to :func:`~.publish`;

.. code:: python

	import layer_cake as lc

    lc.publish(self, service_name, encrypted=True)
	..

There is no matching parameter on the call to :func:`~.subscribe`, as the value registered by
the publisher is propagated through to the pubsub connection machinery, i.e. it is set
automatically.

Encrypted Directory Operation
+++++++++++++++++++++++++++++

Connections are created between the components of a **layer-cake** directory, including the
application processes. Encryption of those connections is enabled for the entire collection
or it is not. Partial encryption, e.g. only those connections to ``lan-cake``, is not supported.

To enable directory encryption within the different processes, use the following process arguments;

+-----------------------+-------------------------+----------------------------------------------+
| Process               | Argument                | Notes                                        |
+=======================+=========================+==============================================+
| ``lan-cake``          | ``encrypted-directory`` | During installation of the component.        |
+-----------------------+-------------------------+----------------------------------------------+
| ``host-cake``         | ``encrypted-directory`` | During installation of the component.        |
+-----------------------+-------------------------+----------------------------------------------+
| ``group-cake``        | ``encrypted-directory`` | During installation of the component.        |
+-----------------------+-------------------------+----------------------------------------------+
| *application process* | ``encrypted-process``   | 1) Automatic within a *composite process*.   |
|                       |                         | 2) On the process command line.              |
+-----------------------+-------------------------+----------------------------------------------+

Examples are provided below;

.. code-block:: console

	$ lan-cake --directory-at-lan='{"host": "192.168.1.176", "port": 54196}' --encrypted-directory
	$ host-cake -debug-level=DEBUG --encrypted-directory

	$ layer-cake create
	$ layer-cake add lan-cake
	$ layer-cake update lan-cake --directory-at-lan='{"host": "192.168.1.176", "port": 54197}'
	$ layer-cake update lan-cake --encrypted-directory
	$ layer-cake start
	$

To enable encryption of application processes use;

.. code-block:: console

	$ python3 test_worker_10.py --encrypted-process

Lastly, to enable encryption of a *composite process*;

.. code-block:: console

	$ layer-cake create
	$ layer-cake update group --encrypted-directory
	$ layer-cake add test_server_10.py server
	$ layer-cake add test_worker_10.py worker --role-count=8
	$ layer-cake run --debug-level=DEBUG
	..
	16:42:26.031 ~ <0000000f>ListenConnect - Listening (encrypted) on "127.0.0.1:37065", ...
	..
	..
	16:42:26.087 ~ <0000000f>ListenConnect - Connected (encrypted) to "127.0.0.1:37065", ...

Security And Availability Of Directory Services
+++++++++++++++++++++++++++++++++++++++++++++++

Encryption of network connections brings security of data that is in-flight, at the cost of
additional CPU cycles and development and support difficulties. An obvious need for encryption
might be where LAN messaging is associated with sensitive business information, especially in
the presence of wireless networking. It seems less applicable to localhost messaging
(e.g. a *composite process*) or messaging over a dedicated, wired network segment. Legal
requirements such as the GDPR would have all in-flight data encrypted.

Layer-cake supports encrypted and unencrypted directory operation. It is reasonably simple to
reconfigure a directory to be one or the other, but even simpler to maintain dual directories.
At each point of component installation (i.e. ``group-cake``, ``host-cake`` and ``lan-cake``)
there are two components added. The second is configured to run on a port beside the first
and for encrypted operation;

.. code-block:: console

	$ layer-cake create
	$ layer-cake add lan-cake lan-cake
	$ layer-cake add lan-cake lan-cake-encrypted
	$ layer-cake update lan-cake --directory-at-lan='{"host": "192.168.1.195", "port": 54195}'
	$ layer-cake update lan-cake-encrypted  --directory-at-lan='{"host": "192.168.1.195", "port": 54196}'
	$ layer-cake update lan-cake-encrypted --encrypted-directory
	$ layer-cake start

Default behaviour of **layer-cake** processes will result in connection to the first, unencrypted
directory. This might be for convenience of development work. Production deployments would be
configured to run on the second directory.

For reasons such as security, reliability and performance, there may be benefit in a directory
for the exclusive use of a single solution. The resource footprint of directory components is low
(i.e. CPU cycles, memory peaks) and there is no disk usage other than logging. All **layer-cake**
logging is self-maintaining and capped at around 2Gb per role (i.e. a process within a *composite
process*). Directory components are *not* involved in messaging between application processes, in
the manner of a message broker.

.. _lc-connections-and-keep-alives:

Long Term Connections And Keep-Alives
=====================================

Long term connections are at risk of failures in the operational environment. These include
events such as dropout of network infrastructure (e.g. someone pulls the plug on a network
switch) and discarded NAT mappings. The significance of these events is that they are likely
to go unreported. There will be no related activity in the local network stack and therefore
no :class:`~.Closed` message propagated to the application.

Enabling the ``keep_alive`` flag on the call to :func:`~.connect` activates
a keep-alive capability, involving a low bandwidth handshake between the two endpoints. If
the exchange is interrupted at any point a timer will expire and the connection will be
:class:`~.Closed`, with the :class:`~.EndOfTransport` value set to ``WENT_STALE``. Keep-alive
machinery is symmetrical - the same code runs at both ends of a connection.

The handshake is ongoing for the life of the connection and operation is entirely discreet.
Activity is periodic but also randomized to avoid unfortunate synchronization. Each pause in
proceedings is adjusted by plus-minus, up to 5 percent. It is also slow, to reduce the network
overhead of just keeping the connection alive. From the time a cable is unplugged it can take
a few minutes before the associated :class:`~.Closed` message is generated.

Long term connections are good in that they improve responsiveness; messages can be sent
in response to a local event without having to wait for a successful connection. There are
also scenarios where an event needs to propagate from the listen end (i.e. the server) to
the connect end (i.e. the client) that run into trouble without enduring connections. With
no connection from the client there is no way for the server to make contact with the other
party.

Connections initiated with a defined task and an expected completion, e.g. in the style of
a file transfer, do not need a keep-alive. Failure of the transport will be exposed by the
failure of the ongoing network I/O. In these scenarios the presence of the associated machinery
would be an unnecessary complication.

By default the ``keep_alive`` flag is disabled. Note that all connections associated
with pubsub operation, that are *not* within the localhost, have ``keep_alive`` enabled.

Logging associated with keep-alive activity is deliberately limited to the recording of
a few initial handshake messages. This is to provide evidence that the feature is operational
and also to preserve the value of the logging facility, i.e. useful log entries would be
pushed out by the recording of endless keep-alive messages.
