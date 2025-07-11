.. _concurrency-with-multithreading:

Concurrency With Multithreading
###############################

The :func:`texture` function accepts size parameters and returns a 2D table of the specified dimensions, filled with random
floating-point values. Execution of the code consumes computing resources such as memory and CPU cycles.

.. code-block:: python

	# test_function_1.py
	import random

	random.seed()

	def texture(x: int=8, y: int=8) -> list[list[float]]:
		table = []
		for r in range(y):
			row = [None] * x
			table.append(row)
			for c in range(x):
				row[c] = random.random()

		return table

Standard Python hints describe the nature of the values passed to the function (``int``) and the nature of what the function
produces (``list[list[float]]``). As the software evolves these hints become a requirement.

.. code-block:: console

	$ python3
	...
	>>> from test_function import texture
	>>> texture(x=2, y=2)
	[[0.7612548315750599, 0.23818407873566672], [0.3034216434184227, 0.06614148124376695]]
	>>>

Calling the function produces a list of lists matching the specified dimensions.

Providing Network Access To The Function
****************************************

The demonstration function needs to be combined with some network plumbing and management of request and response messages. An
implementation is presented below. It introduces an asynchronous approach to software operation, also known as event-driven or
message-driven software. The more interesting aspects of this approach are covered in detail in following sections;

.. code-block:: python

	# test_server_1.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_1 import texture

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = (Xy,)

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()
			else:
				continue

			response = texture(x=m.x, y=m.y)
			self.send(lc.cast_to(response, table_type), self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

Execution of the server will produce output similar to that shown below;

.. code-block:: console

	$ python3 test_server_1.py --debug-level=DEBUG
	00:04:11.423 + <0000000e>ListenConnect - Created by <00000001>
	00:04:11.424 < <0000000e>ListenConnect - Received Start from <00000001>
	00:04:11.424 > <0000000e>ListenConnect - Sent SocketChannel to <00000001>
	00:04:11.424 + <0000000f>ObjectDirectory[INITIAL] - Created by <00000001>
	00:04:11.424 < <0000000f>ObjectDirectory[INITIAL] - Received Start ...
	00:04:11.424 + <00000010>ObjectCollector[INITIAL] - Created by <00000001>
	00:04:11.424 < <00000010>ObjectCollector[INITIAL] - Received Start ...
	00:04:11.424 + <00000011>start_vector - Created by <00000001>
	00:04:11.424 + <00000012>server - Created by <00000011>
	00:04:11.424 ~ <0000000e>ListenConnect - Listening on "127.0.0.1:5050"
	00:04:11.424 > <0000000e>ListenConnect - Sent Listening to <00000012>
	00:04:11.424 < <00000012>server - Received Listening from <0000000e>

Use ``curl`` (or some other HTTP client) to make a call to the network service;

.. code-block:: console

	$ curl -s 'http://127.0.0.1:5050/Xy?x=2&y=2'
	{
		"value": [
			"vector<vector<float8>>",
			[
				[
					0.7121297344671714,
					0.2617093660768349
				],
				[
					0.44326145558200136,
					0.1843574524335293
				]
			],
			[]
		]
	}

The service returns the table as one part of a larger response. Logs associated with the processing of
the request will look like;

.. code-block:: console

	00:08:39.230 + <00000013>SocketProxy[INITIAL] - Created by <0000000e>
	00:08:39.230 ~ <0000000e>ListenConnect - Accepted "127.0.0.1:56586" ...
	00:08:39.230 > <0000000e>ListenConnect - Forward Accepted to <00000012> ...
	00:08:39.231 > <0000000e>ListenConnect - Forward Xy to <00000012> ...
	00:08:39.231 < <00000013>SocketProxy[INITIAL] - Received Start ...
	00:08:39.231 < <00000012>server - Received Accepted from <00000013>
	00:08:39.231 < <00000012>server - Received Xy from <00000013>
	00:08:39.231 < <00000013>SocketProxy[NORMAL] - Received list_list_float ...
	00:08:39.233 > <0000000e>ListenConnect - Sent Stop to <00000013>
	00:08:39.233 > <0000000e>ListenConnect - Forward Closed to <00000012> ...
	00:08:39.234 < <00000013>SocketProxy[NORMAL] - Received Stop ...
	00:08:39.234 < <00000012>server - Received Closed from <00000013>
	00:08:39.234 X <00000013>SocketProxy[NORMAL] - Destroyed

The connection from ``curl`` is accepted, and is immediately followed by the inbound request. The :func:`server` responds
with a table and the connection is terminated.

Declaring An API
****************

Details about the API are defined separately in the ``test_api.py`` file. This file remains the same for all the implementations;

.. code-block:: python

	# test_api.py
	import layer_cake as lc

	class Xy(object):
		def __init__(self, x: int=1, y: int=1):
			self.x = x
			self.y = y

	lc.bind(Xy)

	table_type = lc.def_type(list[list[float]])

To send a message (i.e. a named collection of typed members) in layer cake it needs to be defined as a class. Type hints must be
used to describe the arguments passed to the :meth:`__init__` method. Lastly, the class is registered with the layer cake library
using :func:`~.bind`.

Registration prepares information needed during logging. It’s also needed for the conversion of the HTTP representation \- ``/Xy?x=2&y=3`` \- into
an instance of the :class:`Xy` class during network messaging.

To send anything other than a registered class, the type must be registered using the :func:`~.def_type` function. This produces a
portable object that is used to mark the relevant Python data when required, e.g. :func:`~.cast_to`. As far as the Python type system
is concerned the response variable is a list of anything. This is not enough information by itself for effective processing at the receiver.

In the world of network messaging, the ability to send something like a list of :class:`Xy` objects or a 3D table of floats is uncommon (is this the
first?). Normally this issue is resolved with a message containing the single member. However, in some areas of code it can become tedious to
maintain large numbers of message classes that contain a single member. This can happen in a network API over a database, where many responses
are the result of querying different database tables, i.e. lists of different message types.

Layer cake software that restricts itself to only sending registered messages can completely avoid the details involved in sending data such
as ``list[list[float]]``. However, it is crucial to the complete integration of multithreading and multiprocessing into layer cake processes
and does allow for some nice behaviour around the command line (refer to later sections).

A Brief Outline
***************

An execution trace for the server goes like this;

.. code-block:: console

	* lc.create(server)
	* server(self, server_address)
	* lc.listen(self, server_address, http_server)
	* m = self.input()
	* isinstance(m, Listening)
	* while True
	* m = self.input()
	* isinstance(m, Xy)
	* response = texture(m.x, m.y)
	* c = lc.cast_to(response, self.returned_type)
	* self.send(c, self.return_address)
	* m = self.input()
	* ..

The call to :func:`~.create` causes the initiation of a platform thread and the new thread is directed to call the :func:`server` function.
Alongside the thread, a special object is created by the library and passed as the first argument. This provides access to asynchronous operations
such as :meth:`~.Point.send`. It also contains the unique identity of the :func:`server` *instance*. Technically, there can be many running instances
of a function such as :func:`server`, each with its own dedicated thread and ``self`` object.

A call to :func:`~.listen` arranges for the setup of a TCP listen, at the given address. The library directs all events associated with the
network port to the given identity (i.e. ``self``), such as;

* :class:`~.Listening` \- the listen operation was successful,  
* :class:`~.NotListening` \- the listen operation failed,  
* :class:`~.Accepted` \- a client has successfully connected,  
* :class:`~.Closed` \- an established connection has shut down,  
* :class:`Xy` \- a request was sent by a connected client.

The server checks for a successful :func:`~.listen` and then enters an endless loop that waits for messages and responds according to the type
of the message received.

In the case of the :class:`Xy` message this involves a call to :func:`texture` and sending the result back to the identity that sent the request,
i.e. ``self.return_address``.

Sending and receiving of messages across a network is fully automated \- activities such as serialization, marshaling and block I/O all occur
discreetly. The ``curl`` client forms the proper HTTP representation of an :class:`Xy` message and the :func:`server` function receives a fully
resolved instance of the :class:`Xy` class, using the :meth:`~.Buffering.input` method. When the :func:`server` responds there is a reversal of the
process, eventually resulting in a JSON encoding of the table within the body of an HTTP response message.

Sending a :class:`~.Stop` message is the standard mechanism for termination of asynchronous activity. In this context the message is generated
by the asynchronous runtime in response to a control-c. The standard response is to terminate with the :class:`~.Aborted` message.

A :class:`~.Faulted` message indicates a runtime problem. :class:`~.NotListening` is an example of a fault message, i.e. the :class:`~.NotListening`
class derives from the :class:`~.Faulted` class. Testing with the ``isinstance(m, lc.Faulted)`` call catches all derived messages. Terminating a
process with a fault produces specific handling in the asynchronous runtime \- it is the means by which child processes deliver bad news to the
parent process. In the context of command-line operation, a diagnostic message is printed on ``stderr``. Starting multiple copies of ``test_server_1.py``
will elicit this behaviour;

.. code-block:: console

	$ python3 test_server_1.py
	test_server_1.py: cannot listen at "127.0.0.1:5050" ([Errno 98] Address already in use)

Messages are sent to a specified address. These addresses are layer cake addresses, i.e. not network addresses or machine pointers. They are more
akin to a unique identity, such as the special parameter passed to :func:`server`. At that point where a message is received, the address of
the sending party is always available as ``self.return_address``. This is how the response table is routed back to the proper HTTP client.

Message-driven software inevitably includes message dispatching code;

.. code-block:: python

	if isinstance(m, Xy):
		pass
	elif isinstance(m, lc.Faulted):
		return m
	elif isinstance(m, lc.Stop):
		return lc.Aborted()
	else:
		continue

The lack of a switch statement in Python is a little unfortunate. Layer cake includes the concept of machines, which tackles the issue of
dispatching head on. A short introduction of machines appears in a later section.

Perhaps the most important aspect to this initial implementation is the fundamentally asynchronous approach to the processing of an HTTP
request message. HTTP clients are restricted to a synchronous, request-response interaction with HTTP servers. There is no such constraint
on the internal workings of the :func:`server` and it is in this area that effective concurrency can be delivered. Layer cake can’t help
individual clients with the blocking nature of their HTTP requests but it can deliver true concurrency across multiple connected clients.

Concurrency Using Multithreading
********************************

The first iteration of the server supports a single execution of the :func:`texture` function at any one time. There can be multiple
connected clients but the associated requests are queued internally by the asynchronous framework and delivered to :func:`server` one
at a time, through the :meth:`~.Buffering.input` function. Until the load is heavy enough to overflow the internal queues, this is not a problem.
However, the average response time \- that time between submitting an :class:`Xy` request and receiving the response table \- is probably
sub-optimal. A few minor changes arrange for full concurrency;

.. code-block:: python

	# test_server_2.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_2 import texture

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = (Xy,)

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		# Open a network port for HTTP clients, e.g. curl.
		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		# Run a live network service.
		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Returned):
				d = self.debrief()
				if isinstance(d, lc.OnReturned):
					d(self, m)
				continue
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()
			else:
				continue

			# Callback for on_return.
			def respond(self, response, args):
				self.send(lc.cast_to(response, self.returned_type), args.return_address)

			a = self.create(texture, x=m.x, y=m.y)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

The direct call to :func:`texture` has been replaced with :meth:`~.Point.create`. The asynchronous framework initiates a platform thread
and causes the new thread to call :func:`texture`. This is similar to what occurs during startup of the server, i.e. :func:`~.create`.

An address for the new instance is returned in the “a“ variable and that is used to register a callback to the :func:`respond`
function. When the :func:`texture` call completes the framework generates a :class:`~.Returned` message and routes it back to the
server. Processing of the :class:`~.Returned` message ultimately results in the deferred call to :func:`respond`, passing the response
and the collection of saved arguments passed to :meth:`~.Point.on_return`, e.g. ``return_address=self.return_address``. This is critical to
ensuring that each response goes back to the proper client.

The result of these changes is that every execution of :func:`texture` is discreetly provided with its own dedicated thread. There
can now be multiple instances of :func:`texture` running inside the server at any one time. It is also entirely possible for instances
of :func:`texture` to terminate “out of sequence”, e.g. where the request for a large table of random floats is followed by a request
for a small table and the latter returns before the former.

After creating a callback using :meth:`~.Point.on_return` the :func:`server` thread is immediately available for processing of the next
message, preserving overall responsiveness.

A minor change was also required in ``test_function_2.py``;

.. code-block:: python

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

The :func:`texture` function is now being registered and a ``self`` argument has been added. This ensures that the function call signature
matches the expectations of a :meth:`~.Point.create`, even though the argument is unused in this case. Registration of a function effectively creates
a “thread entry-point” for that function.

Delegating Requests To A Worker
*******************************

The second iteration of the server looks like a real improvement. However, to an experienced eye there are still problems. It is a convenient
assumption that there is an endless supply of thread resources and that adding the next thread to the workload of the CPU, is as beneficial
as it was to add the first. Of course, neither of these things is true.

It’s also a consideration that the platform operation to initiate a thread consumes CPU time and avoiding the cost of constantly creating and
destroying platform threads is probably a good idea.

A thread is needed that accepts multiple :class:`Xy` requests over its lifetime;

.. code-block:: python

	# test_worker_3.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_3 import texture

	def worker(self):
		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()
			else:
				continue

			table = texture(x=m.x, y=m.y)
			self.send(lc.cast_to(table, table_type), self.return_address)

	lc.bind(worker)

To benefit from this approach the server needs to look like;

.. code-block:: python

	# test_server_3.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_worker_3 import worker

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = (Xy,)

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		# Open a network port for HTTP clients, e.g. curl.
		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		# Start a request processor in a separate thread.
		worker_address = self.create(worker)

		# Run a live network service.
		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Returned):
				d = self.debrief()
				if isinstance(d, lc.OnReturned):
					d(self, m)
				continue
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()
			else:
				continue

			# Callback for on_return.
			def respond(self, response, args):
				self.send(lc.cast_to(response, self.returned_type),
					args.return_address)

			a = self.create(lc.GetResponse, m, worker_address)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

There are two points of interest;

* ``worker_address = self.create(worker)``
* ``a = self.create(lc.GetResponse, m, worker_address)``

An instance of :func:`worker` is created during startup and its address saved as ``worker_address``. Rather than sending the
requests directly to that address there is now a :meth:`~.Point.create`. This special library facility forwards the given message to
the specified address and waits for a response. This somewhat convoluted approach allows for continued use of the callback
mechanism. Without the presence of :class:`~.GetResponse` the worker would send the response directly to the server and there would
be no :class:`~.Returned` message to drive the callback machinery.

.. note::

	Developers familar with event-driven software will recognise the role that :class:`~.GetResponse` plays
	in this scenario. It is the equivalent of an entry in a `pending request table`. Within the layer cake
	framework there is no need to allocate ids, match responses with requests and update the table. This happens
	as a natural by-product of delegating to an independent, asynchronous object.

On receiving a message the :class:`~.GetResponse` facility terminates, passing the message back to the server inside a :class:`~.Returned`
message. The standard processing of callbacks occurs resulting in the call to :func:`respond` and a :meth:`~.Point.send` of the table back
to the proper client.

The per-request creation of platform threads (i.e. instances of :func:`texture`) has been replaced with one-off creation of
a :func:`worker`.

Distributing Load Across Multiple Workers
*****************************************

Adoption of :func:`worker` has reduced interactions with the platform but has also resulted in the return of a familiar problem. All
requests must pass through the single thread that has been assigned to the instance of :func:`worker`. Concurrency has been lost.

A pool of workers is needed along with the code to distribute the requests across the pool. Adding this capability to the previous
implementation is trivial;

.. code-block:: python

	# test_server_4.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_worker_4 import worker

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = (Xy,)

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		# Open a network port for HTTP clients, e.g. curl.
		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		# Start a collection of workers.
		worker_spool = self.create(lc.ObjectSpool, worker)

		# Run a live network service.
		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Returned):
				d = self.debrief()
				if isinstance(d, lc.OnReturned):
					d(self, m)
				continue
			elif isinstance(m, lc.Faulted):
				return m
			elif isinstance(m, lc.Stop):
				return lc.Aborted()
			else:
				continue

			# Callback for on_return.
			def respond(self, response, args):
				self.send(lc.cast_to(response, self.returned_type), args.return_address)

			a = self.create(lc.GetResponse, m, worker_spool)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

Rather than creating an instance of a :func:`worker` there is now the creation of an :class:`~.ObjectSpool`. This library facility uses
the remaining arguments to create a collection of :func:`worker` instances. The number of workers can be specified as a parameter,
e.g. ``object_count=16``. The default is 8\.

.. code-block:: python

	worker_spool = self.create(lc.ObjectSpool, worker)

The ``worker_spool`` variable is used in exactly the same manner as the ``worker_address`` was used. Internally the requests are distributed
across the workers. Running the latest server looks like;

.. code-block:: console

	$ python3 test_server_4.py -dl=DEBUG
	00:39:57.196 + <0000000e>ListenConnect - Created by <00000001>
	00:39:57.196 < <0000000e>ListenConnect - Received Start from <00000001>
	00:39:57.196 > <0000000e>ListenConnect - Sent SocketChannel to <00000001>
	00:39:57.196 + <0000000f>ObjectDirectory[INITIAL] - Created by <00000001>
	...
	00:39:57.197 < <00000012>server - Received Listening from <0000000e>
	00:39:57.197 + <00000013>ObjectSpool[INITIAL] - Created by <00000012>
	00:39:57.197 < <00000013>ObjectSpool[INITIAL] - Received Start ...
	00:39:57.197 + <00000014>worker - Created by <00000013>
	00:39:57.197 + <00000015>worker - Created by <00000013>
	00:39:57.197 + <00000016>worker - Created by <00000013>
	00:39:57.197 + <00000017>worker - Created by <00000013>
	00:39:57.198 + <00000018>worker - Created by <00000013>
	00:39:57.198 + <00000019>worker - Created by <00000013>
	00:39:57.198 + <0000001a>worker - Created by <00000013>
	00:39:57.198 + <0000001b>worker - Created by <00000013>

Logs show the spool being populated with multiple instances of the :func:`worker`. After multiple requests using the ``curl`` client, the associated
logs look like;

.. code-block:: console

	00:40:03.529 < <00000012>server - Received Xy from <0000001c>
	...
	00:40:03.529 > <0000001d>GetResponse - Sent Xy to <00000013>
	00:40:03.529 < <00000013>ObjectSpool[SPOOLING] - Received Xy ...
	...
	00:40:03.529 > <0000001e>GetResponse - Sent Xy to <00000014>
	00:40:03.529 < <00000014>worker - Received Xy from <0000001e>
	...
	00:42:12.500 < <00000012>server - Received Xy from <0000001c>
	...
	00:42:12.500 > <0000001d>GetResponse - Sent Xy to <00000013>
	00:42:12.500 < <00000013>ObjectSpool[SPOOLING] - Received Xy ...
	...
	00:42:12.501 > <00000022>GetResponse - Sent Xy to <00000014>
	00:42:12.501 < <00000015>worker - Received Xy from <00000022>

The line containing;

.. code-block:: console

	<00000014>worker - Received Xy

is followed by the same line but with a different id;

.. code-block:: console

	<00000015>worker - Received Xy

This illustrates the distribution of requests among the workers.

There is now concurrency courtesy of the multiple workers. There is also a fixed number of platform threads assigned to the
server and the one-time cost of creating those threads is incurred at startup time. It is possible to tune the number of
workers to suit the deployment environment.

Operation Of A Spool
********************

An operational spool consists of a collection of workers, a request queue and a few configuration parameters. On receiving a
request the spool locates an available worker and forwards the request. A callback is registered (i.e. :meth:`~.Point.on_return`)
for the processing of the response. Load distribution is round-robin, as availability allows. If a worker is not available
the request is appended to the queue.

During execution of a callback the queue is checked. A non-empty queue results in the forwarding of the oldest, deferred
request. Availability of a worker is guaranteed as the worker that triggered the callback, has just become available.

There are five operational parameters that can be set at creation time;

* ``object_count``
* ``size_of_queue``
* ``responsiveness``
* ``busy_pass_rate``
* ``stand_down``

There is explicit control over the number of workers, the maximum number of queued requests and the expected performance of
the workers, expressed as a maximum time between presentation of a request and receiving the response.

An average response time is calculated across a number of the most recent requests. When this average exceeds the given
response time, the spool is considered busy. In this state it uses the ``busy_pass_rate`` to reject a percentage of the inbound
requests, e.g. ``busy_pass_rate=10`` says that one tenth of received requests will be processed and the remainder rejected.
The few requests that do pass through to a :func:`worker` are needed to recover normal operation, i.e. they cause updates
to the average performance metric and therefore the busy status of the spool.

Both ``size_of_queue`` and ``responsiveness`` can be set to ``None``, disabling the associated behaviour. If the former
is ``None`` the queue is never considered full and if the latter is ``None`` the workers are never judged to be busy.
A ``stand_down`` of ``None`` disables the recovery of workers and the failure of a single worker will cause the termination
of the entire spool. Improbable parameters are rejected at startup time.

When a new request encounters a full condition the spool responds immediately with an :class:`~.Overloaded` message. All clients
of a spool should be checking for what they receive as a response. The :class:`~Overloaded` and :class:`~.Busy` messages derive
from the :class:`~.Faulted` message.

In the event that a worker terminates and depending on the value of ``stand_down``, the spool replaces it with a fresh instance.
It inserts a randomized delay into this processing to avoid thrashing. The delay applied is ``stand_down`` seconds plus or minus
up to 25%.
