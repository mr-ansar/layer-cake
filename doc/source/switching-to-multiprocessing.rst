.. _switching-to-multiprocessing:

Switching To Multiprocessing
############################

.. note::

	To follow the materials mentioned in this section, change to the ``layer-cake-demos/multiprocessing`` folder.

Multithreading in the Python environment is affected by the presence of the GIL. The only true concurrency
available to the Python language is through multiprocessing but that brings the difficulties of process
management and network communication. Together these factors can dampen the enthusiasm for multiprocessing.

Basic Use Of Multiprocessing
****************************

Under the **layer-cake** library there are only minor differences between thread-based and process-based concurrency.
The following sections step through the same recent series of thread-based server implementations, but switching
multithreading for multiprocessing.

The most basic use of multiprocessing looks like;

.. code-block:: python

	# test_server_5.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_5 import texture

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = [Xy,]

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

			client_address = self.return_address
			self.create(lc.ProcessObject, texture, x=m.x, y=m.y)
			m = self.input()
			response = m.message

			self.send(response, client_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

Rather than calling :func:`texture`, or creating a thread that calls the function, there is now the creation of
a :class:`~.ProcessObject`, passing ``texture`` as the first argument;

.. code-block:: python

	self.create(lc.ProcessObject, texture, x=m.x, y=m.y)

This is a library facility that initiates a platform process, passes arguments and waits for completion. A return value is
decoded from ``stdout`` and passed back to the :func:`server` inside the :class:`~.Returned` message. The benefit of this approach is
that process behaviour follows the same model as thread behaviour.

Passing ``texture`` as the first argument provides the :class:`~.ProcessObject` with everything it needs to perform its role.
The module the function was loaded from is recorded in the function object and the type information needed to encode the
arguments and decode the output is available in the information registered using :func:`~.bind`.

The following lines have been added to the ``test_function_5.py`` module;

.. code-block:: python

	lc.bind(texture)

	if __name__ == '__main__':
		lc.create(texture)

The ``self`` parameter has also been added to the function definition. The call to :func:`~.create` ensures that the module is
loadable and there is the expected processing of arguments.

The sequence of;

.. code-block:: python

	self.create(lc.ProcessObject, texture, x=m.x, y=m.y)
	m = self.input()
	response = m.message

is a process-based equivalent to the thread-based version;

.. code-block:: python

	self.create(texture, ...)
	m = self.input()
	response = m.message

There is no networking involved in this implementation. Logs from the processing of a request include details such as;

.. code-block:: console

	<00000012>server - Received Xy
	<00000014>ProcessObject[...] - Created by <00000012>
	<00000014>ProcessObject[...] - Received Start from <00000012>
	<00000014>ProcessObject[...] - .../python3 .../test_function_5.py --x=2 --y=2 ...
	...
	<00000012>texture - Created by <00000011>
	<00000012>texture - Destroyed
	<00000011>start_vector - Received "Returned" ...
	...
	<00000012>server - Received Returned ...
	<00000013>SocketProxy[NORMAL] - Received list_list_float ...

There is a full record of the arguments passed on creation of the process. Eventually a :class:`~.Returned` message is
received at the :func:`server()` and it can extract the response.

This example is intended to illustrate how processes are integrated into the **layer-cake** library. It is in no way a
recommended implementation of a network service. It suffers from the same fundamental problem as the very first server
that called :func:`texture()` directly. A problem only made worse by the overhead of loading a process.

Command-Line Access To The Function
***********************************

The previous section uses the creation of a process entry-point to enable the “calling” of the :func:`texture()` function,
as if it were a process.

.. code-block:: python

	if __name__ == '__main__':
		lc.create(texture)

It does this by using the call to :func:`~.create()` to interrogate the :func:`texture()` function for type hints, for both
the arguments that it expects and the value that it returns. It then uses the argument hints to decode the ``sys.argv``
information and pass that decoded information on a call to the actual function. After the function completes the return
type hint is used to encode the results onto ``stdout``.

A side effect of providing this behaviour for the benefit of complex multiprocessing is that the same behaviour becomes
useful at the command line;

.. code-block:: console

	$ python3 test_function_5.py --x=2 --y=2
	[
		[
			0.5810276144909766,
			0.5707206342428258
		],
		[
			0.01199731571794349,
			0.29231401993019657
		]
	]

Arguments passed on the command-line mimic the passing of named arguments to a Python function, and the JSON output exactly
reflects the ``list[list[float]]`` type hint, allowing for natural use of the ``jq`` utility;

.. code-block:: console

	$ python3 test_function_5.py --x=2 --y=2 | jq '.[1][1]'  
	0.8117815849029929

More complete output can be requested;

.. code-block:: console

	$ python3 test_function_5.py --x=2 --y=2 --full-output
	{
		"value": [
			"vector<vector<float8>>",
			[
				[
					0.37766725552751146,
					0.7368838301641667
				],
				[
					0.34781758273139174,
					0.6930133207480063
				]
			],
			[]
		]
	}

This is the output seen from previous use of the ``curl`` client and it is also the output seen by the :class:`~.ProcessObject`
facility, i.e. the ``--full-output`` flag is always added within the multiprocessing machinery. Full output includes a type
signature that must be present for a successful decoding process.

It is the absence of the ``--full-output`` flag at the command-line that results in the more human-friendly output.

All the server implementations use the same technique for a process entry-point and therefore enjoy the same means of passing
arguments;

.. code-block:: console

	$ python3 test_server_5.py --server-address=’{“host”: “127.0.0.1”, “port”: 5051}’

The servers can also be started as a sub-process using;

.. code-block:: python

	from test_server_1 import server  
	..

	a = self.create(lc.ProcessObject, server, server_address=requested_address)

The process entry-point imposes conventions around the execution of a process. Each process becomes a reusable component to be
incorporated into other developments. It’s also nice that they can be operated from the command-line.

Concurrency Using Multiprocessing
*********************************

A slight improvement can be achieved with the use of callbacks;

.. code-block:: python

	# test_server_6.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_6 import texture

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = [Xy,]

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

			a = self.create(lc.ProcessObject, texture, x=m.x, y=m.y)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

A process is created for every request received by the server. Once a process has been initiated the server thread is
immediately available for processing the next message. Technically the server supports an infinite number of concurrent
executions of the :func:`texture()` function. These are truly concurrent by virtue of their location inside dedicated
host processes. As with the multithreading approach, platforms do not support an infinite number of processes and the
cost of starting and stopping processes is exorbitant. Aside from some specific circumstances, this is an approach to
be avoided.

As with the previous implementation, there is no network communication between the server and texture processes. There
are arguments passed on process creation and a response read from ``stdout``. Asynchronous termination of a process is
achieved using platform signals. A :class:`~.Stop` can be sent to a :class:`~.ProcessObject` at any time and results in a
signal, which is in turn translated back into a :class:`~.Stop` in the receiving process.

Delegating Requests To A Process
********************************

A process is needed that accepts multiple :class:`Xy` requests over a network connection;

.. code-block:: python

	# test_worker_7.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_7 import texture

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

	lc.bind(worker, api=[Xy,])

	if __name__ == '__main__':
		lc.create(worker)

This is similar to the previous implementations of :func:`worker()`, except ``api=[Xy,]`` has been added to the
registration. To take advantage of this new worker there needs to be a matching server;

.. code-block:: python

	# test_server_7.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_worker_7 import worker

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = [Xy,]

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		# Open a network port for HTTP clients, e.g. curl.
		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		# Start a request processor in a separate thread.
		worker_address = self.create(lc.ProcessObject, worker)

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

			a = self.create(lc.GetResponse, m, worker_address)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

This appears similar to the previous use of a :func:`worker()`, except that now we have the address of a :class:`~.ProcessObject`
rather than the :func:`worker()` instance, and somehow messages sent to that new object are being received at the :func:`worker()`
instance located in that new process.

The instance of :class:`~.ProcessObject` created by;

.. code-block:: python

	worker_address = self.create(lc.ProcessObject, worker)

checks the registered details for ``worker``;

.. code-block:: python

	lc.bind(worker, api=[Xy,])

It detects the declaration of an API and passes a special argument at process creation time. This directs the asynchronous
framework within the new ``worker`` to make a special connection back to the parent process. Further background routing occurs
such that any message sent to the :class:`~.ProcessObject` in the server (i.e. ``worker_address``) travels across the connection
and is delivered to the :func:`worker()` instance through the :meth:`~.Buffering.input()` function. Responses sent to the ``self.return_address``
by the :func:`worker()` function find their way back to the original sender, i.e. the :func:`server()` instance in the server process.

Processes created in this way effectively operate as private loadable libraries. Load as many libraries as required and send
whatever requests are appropriate to the different :class:`~.ProcessObject` addresses. This is true multiprocessing, i.e. process
management and network messaging, with zero coding effort.

By removing the overhead of starting and stopping a process for every request, the response time is manifestly improved. However,
there is no real concurrency as requests are queued internally and fed to the single :func:`worker()` process one at a time.

Distributing Load Across Multiple Processes
*******************************************

A spool of worker processes is needed. The changes to convert the multithreading version to multiprocessing are again, trivial;

.. code-block:: python

	# test_server_8.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_worker_8 import worker

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = [Xy,]

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		# Open a network port for HTTP clients, e.g. curl.
		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		worker_spool = self.create(lc.ObjectSpool, lc.ProcessObject, worker)

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

Rather than creating a :class:`~.ProcessObject`, there is now the creation of a :class:`~.ObjectSpool`. As described previously,
this library facility uses its arguments to create a pool of objects;

.. code-block:: python

	worker_spool = self.create(lc.ObjectSpool, lc.ProcessObject, worker)

Rather than creating a pool of worker threads, there is now a pool of worker processes. This brings those same benefits enjoyed
by a spool of worker threads, plus there is true concurrency in the activities of the separate worker processes.

These benefits come at the cost of a slightly slower startup and the relatively slow exchange of request and response messages,
when compared with the multithreading implementation. Network messaging in this scenario (i.e. across the loopback interface)
is quick; in the order of a few thousand request-response pairs a second, with current hardware.

Process Orchestration And Housekeeping
**************************************

The final implementation of multiprocessing is a reasonably difficult example of process orchestration. There may be hundreds
of processes in the worker spool that must be managed at all times. Worker processes may terminate and require restarts, or
a full teardown of the server process and all its workers may suddenly be required at any moment. A significant challenge if
assigned the task of developing such a process from scratch.

The final act of process orchestration is to terminate cleanly. This involves the managed teardown of all platform resources
such as processes and network ports. When any **layer-cake** process is terminated (e.g. a control-c) there is a phase of
housekeeping. Open connections are closed, listen ports are closed and lastly, child processes are terminated. 

This housekeeping occurs by default and obviates the need for any housekeeping by the developer of a **layer-cake** process. Where
there is a specific need, there is always the ability to release those platform resources manually. To close a connection \- send
the :class:`~.Close` message to the transport, to close a listen port \- use :func:`~.stop_listening`, and to terminate a
process \- send the :class:`~.Stop` message to the address of the :class:`~.ProcessObject`.
