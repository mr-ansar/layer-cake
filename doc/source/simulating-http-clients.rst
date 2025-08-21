.. _simulating-http-clients:

Simulating HTTP Clients
#######################

.. note::

	To follow the materials mentioned in this section, change to the ``layer-cake-demos/testing`` folder.

A testing tool is needed for the demonstration network service. As much as possible it needs to simulate the workload that
the network service will experience. There will be;

* multiple connected clients \- tens, hundreds or even thousands,  
* clients connecting, submitting a few requests and disconnecting,  
* validation of responses, i.e. tables must be of requested dimensions,  
* configurable delays between client requests.

The test client will use multithreading and multiprocessing to deliver multiple concurrent clients. There will be;

* a thread that connects, performs a series of request-response sequences and disconnects,  
* a process that starts and maintains a number of threads,  
* and a process that starts a number of the multithreading processes.

The number of threads and processes will be configurable to allow for tuning.

Implementation uses the machine feature within the **layer-cake** library. This style of programming is inspired by
finite state machines (i.e. FSMs or active objects). An introduction can be found :ref:`here<functions-and-machines>`.

Rather than defining a function, a machine is defined as a class. The class accepts arguments defined using type hints on
the :meth:`__init__()` method, and it returns an instance of a type, defined when registering the class with :func:`~.bind()`;

.. code-block:: python

	# connect_and_request.py
	import layer_cake as lc
	import random
	from test_api import Xy, table_type

	#
	random.seed()

	#
	DEFAULT_SERVER = lc.HostPort('127.0.0.1', 5050)

	class ConnectAndRequest(lc.Threaded, lc.Stateless):
		def __init__(self, server_address: lc.HostPort=None,
				request_count: int=1, slow_down: float=0.5, big_table: int=100):
			lc.Threaded.__init__(self)
			lc.Stateless.__init__(self)
			self.server_address = server_address or DEFAULT_SERVER
			self.request_count = request_count
			self.slow_down = slow_down
			self.big_table = big_table

			self.sent = None
			self.client_address = None
		
		def send_request(self):
			'''Connection is active. Initiate request-response sequence.'''
			x = random.randint(1, self.big_table)
			y = random.randint(1, self.big_table)
			xy = Xy(x, y)
			self.send(xy, self.client_address)
			self.sent = xy

		def post_response(self, response):
			'''Response received, validate and determine next move.'''
			y = len(response)
			x = len(response[0])

			sent = self.sent
			if not (x == sent.x and y == sent.y):
				self.complete(lc.Faulted('not the matching table'))

			# Completed sequence of requests.
			self.request_count -= 1
			if self.request_count < 1:
				self.send(lc.Close(), self.client_address)
				return

			# Take a breath.
			s = lc.spread_out(self.slow_down)
			self.start(lc.T1, s)

	def ConnectAndRequest_Start(self, message):
		lc.connect(self, self.server_address, http_client='/', layer_cake_json=True)

	def ConnectAndRequest_Connected(self, message):
		self.client_address = self.return_address
		self.send_request()

	def ConnectAndRequest_NotConnected(self, message):
		self.complete(message)

	def ConnectAndRequest_list_list_float(self, message):
		self.post_response(message)

	def ConnectAndRequest_Busy(self, message):
		self.request_count -= 1
		if self.request_count < 1:
			self.send(lc.Close(), self.client_address)
			return

		s = lc.spread_out(self.slow_down)
		self.start(lc.T1, s)

	def ConnectAndRequest_T1(self, message):
		self.send_request()

	def ConnectAndRequest_Closed(self, message):
		self.complete(lc.Ack())

	def ConnectAndRequest_Stop(self, message):
		self.complete(lc.Aborted())

	def ConnectAndRequest_Faulted(self, message):
		self.complete(message)

	#
	#
	CONNECT_AND_REQUEST_DISPATCH = (
		lc.Start,
		lc.Connected, lc.NotConnected,
		table_type, lc.Busy, lc.T1,
		lc.Closed,
		lc.Stop,
		lc.Faulted,
	)

	lc.bind(ConnectAndRequest,
		CONNECT_AND_REQUEST_DISPATCH,
		return_type=lc.Any())

	if __name__ == '__main__':
		lc.create(ConnectAndRequest)

The :class:`ConnectAndRequest` class derives from the :class:`~.Threaded` and :class:`~.Stateless` classes. The former causes
the allocation of a thread-per-object instance while the latter selects the simpler variant of machines. Switching from
the :class:`~.Threaded` class to the :class:`~.Point` class results in a machine that does not require its own thread allowing
for the creation of large numbers of machines. Switching from the :class:`~.Stateless` class to the :class:`~.StateMachine`
class results in something much closer to a FSM.

Supporting the class are a collection of transition functions, or message handlers. One function is defined for each message
type that the machine expects to receive. Lastly there is the definition of a dispatch table that lists those expected
messages. Passing the table on the call to :func:`~.bind()` results in the compilation of an internal lookup table, during startup
of the process. As messages are received for the machine there is an efficient lookup using the table, and then a call to
the appropriate function.

Machines do not make calls to input routines such as :meth:`~.Buffering.input()`; they are purely reactive. To get things going the
library generates a :class:`~.Start` message immediately after construction of the class has completed. Execution usually continues
as a sequence of message exchanges with other machines and functions, all initiated by activity in the start function.

An execution trace for the client goes like this;

.. code-block:: console

	* lc.create(ConnectAndRequest)
	* ConnectAndRequest.__init__(…)
	* ConnectAndRequest_Start(…):
	* lc.connect(self, self.server_address, …)
	* ConnectAndRequest_Connected(…):
	* self.send(xy, self.client_address)
	* ConnectAndRequest_list_list_float(…)
	* self.start(lc.T1, …)
	* ConnectAndRequest_T1(self, …)
	* self.send(xy, self.client_address)
	* ConnectAndRequest_list_list_float(…)
	* self.start(lc.T1, …)
	* …
	* ConnectAndRequest_Closed(self, …)
	* self.complete()

The call to :func:`~.create()` causes the construction of a :class:`ConnectAndRequest` object. The object is given a unique identity
and the ``self`` object provides the same facilities as the ``self`` object passed to a function, e.g. :func:`server()`.

The machine calls :func:`~.connect()` and then expects a :class:`~.Connected`, then calls :meth:`~.Point.send()` and expects a ``list_list_float``,
then calls :meth:`~.Point.start()` and expects a timer message (:class:`~.T1`). This continues until there is a call to the :meth:`~.Point.complete()`
method. Layer cake destroys the calling object and sends an :class:`~.Returned` message to the parent. The message carries the value
passed to :meth:`~.Point.complete()`, in this case the default value ``None``.

Enter the following commands;

.. code-block:: console

	$ cd ../testing
	$ python3 connect_and_request.py --debug-level=DEBUG

Machines are the better option when dealing with complex exchanges of messages and the ever present potential for faults. Writing
robust code in these situations using a procedural approach can quickly become fragile, with large sections of dispatching mingled
with tricky control flow. Rather conveniently the :class:`ConnectAndRequest` machine includes no control flow at all, a consequence
of each action resulting in a unique reaction. It’s worth noting that the :class:`ConnectAndRequest` machine does perform a loop
around the decrement of ``self.request_count`` and that the :func:`ConnectAndRequest_Faulted()` and :func:`ConnectAndRequest_Stop()`
functions may be called at any time within the lifespan of the machine.

Further implementations of ``ConnectAndRequest`` are provided for reference;

* connect\_and\_request.py … thread allocated to each client  
* connect\_and\_request\_not\_threaded.py … all clients execute on default thread  
* connect\_and\_request\_named\_thread.py … all clients execute on a dedicated thread  
* connect\_and\_request\_state\_machine.py … FSM-based client (default thread)

These show the different threading models available to machines and the use of state-based machines. The particular implementation
to use can be selected on the command line of the test clients appearing below, e.g. ``--client-type=module.class``.

The first application of concurrency comes with a process that manages instances of :class:`ConnectAndRequest`;

.. code-block:: python

	# clients_as_threads.py
	import layer_cake as lc
	import random
	from test_api import Xy, table_type
	import connect_and_request
	import connect_and_request_not_threaded
	import connect_and_request_named_thread
	import connect_and_request_state_machine

	#
	DEFAULT_SERVER = lc.HostPort('127.0.0.1', 5050)

	#
	def clients_as_threads(self, client_type: lc.Type=None,
		thread_count: int=1, server_address: lc.HostPort=None,
		request_count: int=1, slow_down: float=1.0, big_table: int=100):

		client = connect_and_request.ConnectAndRequest
		if isinstance(client_type, lc.UserDefined):
			client = client_type.element
		self.server_address = server_address or DEFAULT_SERVER

		def restart(self, value, args):
			a = self.create(client, server_address=server_address,
				request_count=request_count, slow_down=slow_down,
				big_table=big_table)
			self.on_return(a, check_response)

		def check_response(self, value, args):
			if isinstance(value, lc.Faulted):
				return
			a = self.create(lc.Delay, seconds=slow_down)
			self.on_return(a, restart)

		# Start with full set and setup replace callback.
		for i in range(thread_count):
			a = self.create(client, server_address=server_address,
				request_count=request_count, slow_down=slow_down,
				big_table=big_table)
			self.on_return(a, check_response)

		# Two ways this can end - control-c and faults.
		# By default it will be because all the clients faulted.
		ending = lc.Faulted('number of clients declined to zero', 'see logs')

		while self.working():
			m = self.input()
			if isinstance(m, lc.Stop):
				self.abort()
				ending = lc.Aborted()
				break
			elif isinstance(m, lc.Returned):
				d = self.debrief()
				if isinstance(d, lc.OnReturned):
					d(self, m)

		# Wait for clearing of clients.
		while self.working():
			r = self.input()
			if isinstance(r, lc.Returned):
				d = self.debrief()
				# No callback processing.
				# Just debrief() to clear the OnReturned entry.

		return ending

	lc.bind(clients_as_threads)

	if __name__ == '__main__':
		lc.create(clients_as_threads)

If the caller selects a particular implementation, there is some processing required to extract the Python class from the type
information. Otherwise this defaults to the thread-per-client implementation.

A ``for`` loop creates the requested number of client instances and registers a callback to :func:`check_response()`. If a client returns
an :class:`~.Faulted` value the callback terminates, leaving one less active client. Otherwise a callback is registered to :func:`restart()`
after a short delay. This is a rather esoteric use of callbacks that might be expressed more clearly as a machine.

After the initial instantiation of clients and callbacks the :func:`clients_as_threads` process loops on :meth:`~.Point.working`. This is
a simple method that returns the number of outstanding callbacks. As long as there is pending work the process waits for the next
message, e.g. :class:`~.Stop`.

Calling :meth:`~.Point.abort()` causes the broadcast of a :class:`~.Stop` to every object with an outstanding callback. As the :class:`~.Returned`
messages are processed the number of those still outstanding falls to zero and the while loop terminates.

An alternative implementation of :func:`clients_as_threads()` would have the parent process performing the :func:`~.connect()` and passing
the resulting address to each instance of the :class:`ConnectAndRequest` class, rather than passing the IP and port.

The only real value in such an implementation is as a demonstration of the difference between the internal, **layer-cake**, asynchronous
messaging and HTTP request-response messaging. HTTP does not support multiplexing of requests, forcing **layer-cake** to queue the outgoing
requests. When a response is received it is forwarded to the original requesting party. The next pending request is then sent across
the connection, and so on. This artificially imposes the request-response model. All this discreet handling allows fully asynchronous
operation within the **layer-cake** client and **layer-cake** server, but in actual operation it is throttled by the presence of HTTP.

The ``clients_as_threads_2.py`` module is provided for reference. Enter a command like;

.. code-block:: console

	$ python3 clients_as_threads_2.py --debug-level=DEBUG --request-count=4 --thread-count=1000

Using the first implementation this would create a significant workload on the network service but instead the requests dribble
through, one at a time. There are always 999 instances of :class:`ConnectAndRequest` waiting their turn.

To fully exploit the testing potential of the local host there needs to be multiprocessing. This looks like;

.. code-block:: python

	# clients_as_processes.py
	import layer_cake as lc
	import random
	from test_api import Xy, table_type
	from clients_as_threads import clients_as_threads

	#
	DEFAULT_SERVER = lc.HostPort('127.0.0.1', 5050)

	#
	def clients_as_processes(self, process_count: int=1, thread_count: int=1,
		client_type: lc.Type=None, server_address: lc.HostPort=None,
		request_count: int=1, slow_down: float=1.0, big_table: int=100):
		server_address = server_address or DEFAULT_SERVER

		# Start the processes.
		for i in range(process_count):
			a = self.create(lc.ProcessObject, clients_as_threads,
				thread_count=thread_count,
				client_type=client_type, server_address=server_address,
				request_count=request_count, slow_down=slow_down,
				big_table=big_table)
			self.assign(a, i)

		# Two ways this can end - control-c and faults.
		ending = lc.Faulted('too many client faults', 'see logs')

		while self.working():
			m = self.input()
			if isinstance(m, lc.Stop):
				self.abort()
				ending = lc.Aborted()
			elif isinstance(m, lc.Returned):
				d = self.debrief()

		return ending

	lc.bind(clients_as_processes)

	if __name__ == '__main__':
		lc.create(clients_as_processes)

Enter a command like;

.. code-block:: console

	$ python3 clients_as_processes.py --debug-level=DEBUG --process-count=20 --thread-count=20 --request-count=4

Client activity is concurrent. Adjust the distribution of threads, i.e. is performance better when processes are
at 100 and threads are at 4, or when processes are at 4 and threads are at 100? The full set of command line
arguments are;

* ``process-count`` … number of processes to be created  
* ``thread-count`` … number of threads to be created  
* ``client-type`` … select the implementation of ConnectAndRequest  
* ``server-address`` … network location to be tested  
* ``request-count`` … number of request-response exchanges by each client  
* ``slow-down`` … a pause after each request-response  
* ``big-table`` … maximum requested size of table

The ability to select the client type was included for broader demonstration of **layer-cake** machines. It's also
extensible in the sense that further implementations of clients can be written and included in the list of
client imports. These can be client interactions customized to a particular network service;

* watch dog … a light interaction that verifies overall operational status,
* administrator maintenance … specific check of administrative functions,
* typical user … most common usage pattern by the largest section of the user base,
* expert user … special cases for those demanding users.

As a side effect of **layer-cake** multithreading and multiprocessing, there are 3 distinct testing tools;

* ``connect_and_request.py``
* ``clients_as_threads.py``
* ``clients_as_processes.py``

The first simply runs the interaction and terminates, using a single process and thread - there is no repetition.
The remaining pair maintain the specified number of clients until they themselves are terminated, using a tunable
number of threads and processes to do so.

Use composite processes to manage combinations of client activity;

.. code-block:: console

	$ layer_cake create
	$ layer_cake add clients_as_threads.py watchdog
	$ layer_cake add clients_as_processes.py typical
	$ layer_cake add clients_as_processes.py expert

Tune the composite;

.. code-block:: console

	$ layer_cake update watchdog --client-type=watch_dog.ConnectAndRequest --thread-count=1 --request-count=4 --slow-down=30.0
	$ layer_cake update typical --client-type=typical_user.ConnectAndRequest --process-count=20 --thread-count=100 --request-count=32
	$ layer_cake update expert --client-type=expert_user.ConnectAndRequest --process-count=1 --thread-count=5 --request-count=64

Start the composite;

.. code-block:: console

	$ layer_cake start

Check that everything is still running;

.. code-block:: console

	$ layer_cake status --long-listing
	watchdog                 <867502> 7h
	typical                  <867510> 7h
	expert                   <867508> 7h

Look at how advanced usage has been running for the last hour;

.. code-block:: console

	$ layer_cake log expert --back=1h
	2026-03-08T21:04:33.651 < <00000025>SocketProxy[INITIAL] - Received Start from <0000000f>
	2026-03-08T21:04:33.651 > <0000000f>ListenConnect - Forward LoopOpened to <00000020> (from <0000001f>)
	2026-03-08T21:04:33.651 + <00000027>SocketProxy[INITIAL] - Created by <0000000f>
	2026-03-08T21:04:33.651 ~ <0000000f>ListenConnect - Connected to "127.0.0.1:33831", at local address "127.0.0.1:36022"
	2026-03-08T21:04:33.651 > <0000000f>ListenConnect - Forward Connected to <0000001c> (from <00000027>)
	2026-03-08T21:04:33.652 < <00000027>SocketProxy[INITIAL] - Received Start from <0000000f>
	2026-03-08T21:04:33.652 < <0000001c>ConnectToPeer[PENDING] - Received Connected from <00000027>
	2026-03-08T21:04:33.652 + <00000028>GetResponse - Created by <0000001c>
	2026-03-08T21:04:33.652 < <00000024>GetResponse - Received Start from <0000001a>
	...

HTTP vs Internal Messaging
**************************

Messaging between test clients and the demonstration network service uses HTTP as the message format. This is to
demonstrate integration capability with standard messaging techniques, i.e. operating as the backend for a website.

HTTP is a request-response, or blocking protocol. All messaging within the service implementations uses an internal
messaging protocol. Among other features, this protocol is fundamentally asynchronous, or non-blocking. It would be
impossible to deliver the concurrency appearing in this document, using HTTP for internal messaging.

Providing HTTP integration is as simple as adding an argument on the call to :func:`~.listen()`;

.. code-block:: python

	lc.listen(self, address, http_server=SERVER_API)

The ``http_server`` argument indicates that HTTP request messages should be expected on all accepted connections. Any
Python message sent to a connected client is converted into an HTTP response message.

At the client end use;

.. code-block:: python

	lc.connect(self, server_address, http_client='/', layer_cake_json=True)

The passing of ``http_client`` enables the exchange of HTTP request and response messages. The value (e.g. ``/``) is
combined with the name of the message and included as the path component of the outgoing URI, e.g. ``/Xy``. To enable
full processing of response messages into Python messages, enable ``layer_cake_json``. The default is to treat the
remote party as a non-**layer-cake** service and pass :class:`~.HttpResponse` messages to the client. Processing of the body becomes
the client's responsibility.

Due to the blocking nature of HTTP there can only ever be one outstanding request per connected client. To actually
see concurrency occurring in the service there must be multiple clients.
