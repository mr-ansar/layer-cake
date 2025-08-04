.. _distribution-with-multihosting:

Distribution With Multihosting
##############################

.. note::

	To follow the materials mentioned in this section, change to the ``layer-cake-demos/multihosting`` folder.

Multithreading and multiprocessing demonstrations have focused on the implementation of concurrency within the scope of a
single process. Processes that start and manage sub-processes to their completion, are included within the definition of
a single process.

To make use of physically distributed computing resources there needs to be multihosting, where the network service is
no longer a single process. Instead it consists of a logically related collection of processes, each of which may be
running on any host within a network. For the demonstration network service, this would bring the ultimate in concurrency.
Each worker in the pool could be running on its own physical platform with its own set of computing resources.

The **layer-cake** library provides both traditional networking, through the :func:`~.listen` and :func:`~.connect`
functions, and :ref:`publish-subscribe networking<publish-subscribe-networking>` (or just pubsub). To really showcase
what **layer-cake** can do, this final section on concurrency will focus on the latter.

One of the most problematic issues relating to multihosting, is arranging for all the right connections between
all the right processes on all the right hosts. Any reasonable description of this problem space is beyond the scope
of this document. Suffice to say that pubsub is one way to avoid most of the effort and most of the pain that arises
from making mistakes in this area.

Pubsub is implemented as a small set of networking components; ``group-cake``, ``host-cake`` and ``lan-cake``. At least
one of these components must be present for pubsub to work. The use of the first is effectively automated, while the latter
two need to be installed as part of the operational environment. They play a background role similar to DHCP or dynamic
DNS. Installation requires a few trivial commands, and then all operation is discreet. The most difficult aspect of pubsub
is the placement of ``lan-cake``. Further detail appears in the following sections.

A Session With A Published Service
**********************************

Registering a worker as a service looks like;

.. code-block:: python

	# test_worker_9.py
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_9 import texture

	def worker(self):
		lc.publish(self, 'test-multihosting:worker-9')
		m = self.input()
		if not isinstance(m, lc.Published):
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

			table = texture(x=m.x, y=m.y)
			self.send(lc.cast_to(table, table_type), self.return_address)

	lc.bind(worker)

	if __name__ == '__main__':
		lc.create(worker)

The interesting line of code is;

.. code-block:: python

	lc.publish(self, 'test-multihosting:worker-9')

Rather than listening at a particular network IP and port, this :func:`worker()` is publishing its capabilities under a string
name. By convention the name is structured as a series of fields separated by a colon. The :func:`worker()` is defined with
both thread and process entry-points.

Establishing a subscriber session from the :func:`server()` looks like;

.. code-block:: python

	# test_server_9.py
	import layer_cake as lc
	from test_api import Xy, table_type

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = [Xy,]

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		lc.subscribe(self, 'test-multihosting:worker-9')
		m = self.input()
		if not isinstance(m, lc.Subscribed):
			return m

		worker_spool = self.create(lc.ObjectSpool, None)

		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Returned):
				d = self.debrief()
				if isinstance(d, lc.OnReturned):
					d(self, m)
				continue
			elif isinstance(m, lc.Available):
				self.send(lc.JoinSpool(m.publisher_address), worker_spool)
				continue
			elif isinstance(m, lc.Dropped):
				self.send(lc.LeaveSpool(m.remote_address), worker_spool)
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

			a = self.create(lc.GetResponse, m, worker_spool)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

The first line of interest is;

.. code-block:: python

	lc.subscribe(self, 'test-multihosting:worker-9')

Rather than attempting to connect to a particular network IP and port, this :func:`server()` is registering interest in a
string name. There is also the special definition of spool;

.. code-block:: python

	worker_spool = self.create(lc.ObjectSpool, None)

This spool receives the addresses of its workers from an external source, indicated by the passing of a ``None``;

.. code-block:: python

	elif isinstance(m, lc.Available):
		self.send(lc.JoinSpool(m.publisher_address), worker_spool)
		continue

At some point the server receives notification that the named service is available. The server updates the spool with the
new information. A matching procedure occurs around the loss of a service, i.e. on receiving a :class:`~.Dropped` message
the spool is directed to forget the specified worker.

To run this implementation enter the following commands;

.. code-block:: console

	$ layer-cake create  
	$ layer-cake add test_server_9.py server  
	$ layer-cake add test_worker_9.py worker

This creates a small hierarchy of sub-folders and files in the ``.layer-cake`` folder. To run all the processes described in
that folder, use this command line;

.. code-block:: console

	$ layer-cake run --debug-level=DEBUG
	<0000000e>ListenConnect - Created by <00000001>
	<0000000e>ListenConnect - Received Start from <00000001>
	<0000000e>ListenConnect - Sent SocketChannel to <00000001>
	<0000000f>ObjectDirectory[INITIAL] - Created by <00000001>
	...
	<00000012>layer_cake - Created by <00000011>
	<00000012>layer_cake - run (.../multihosting/.layer-cake)
	<00000013>head_lock - Created by <00000012>
	<00000013>head_lock - Sent Ready to <00000012>
	<00000012>layer_cake - Received "Ready" from <19>
	...
	<00000015>ProcessObject[INITIAL] - Created by <00000012>
	<00000015>ProcessObject[INITIAL] - Received Start from <00000012>
	<00000015>ProcessObject[INITIAL] - .../group-cake .../multihosting/.layer-cake
	...
	<00000013>ProcessObject[INITIAL] - Created by <00000012>
	<00000014>ProcessObject[INITIAL] - Created by <00000012>
	<00000013>ProcessObject[INITIAL] - Received Start from <00000012>
	<00000013>ProcessObject[INITIAL] - .../python3 .../test_server_9.py ...
	...
	<00000014>ProcessObject[INITIAL] - Received Start from <00000012>
	<00000014>ProcessObject[INITIAL] - .../python3 .../test_worker_9.py ...
	...
	<00000013>server - Received Available from <00000016>
	<00000013>server - Sent JoinSpool to <00000014>
	<00000014>ObjectSpool[SPOOLING] - Received JoinSpool from <00000013>

Stepping through the logs it is possible to see the ``layer-cake`` process starting the ``group-cake`` process
and then the ``group-cake`` process starting the server and worker processes. Confirm that the server has found
the worker and that the worker is being put to use by the spool;

.. code-block:: console

	$ curl -s 'http://127.0.0.1:5050/Xy?x=2&y=2'
	{
		"value": [
			"vector<vector<float8>>",
			[
				[
					0.5647838146363222,
					0.5596026171995564
				],
				[
					0.1567212327148707,
					0.7033970937636289
				]
			],
			[]
		]
	}

The :ref:`layer-cake<layer-cake-command-reference>` CLI tool is \- among other things \- a process orchestration tool. It provides
sub-commands for describing a set of processes and sub-commands for initiating those processes, the result of which might be called
a *composite process*. This concept is strengthened by the discreet inclusion of ``group-cake``, which provides the supporting
pubsub machinery to bring the :func:`server()` and :func:`worker()` together.

Both :func:`~.publish` and :func:`~.subscribe` are about entering networking information into the pubsub machinery. There is no
expectation that subscribing will produce an immediate indication of whether a connection has been created. Connections occur
when matching parties are detected.

Connecting To Multiple Instances Of A Service
*********************************************

The obvious approach to connecting multiple workers would be to create multiple processes that each registered a different
configured name. The :func:`server()` would also have to include multiple calls to :func:`~.subscribe()` to register for each
of the different names. Happily there are only a few minor changes needed. Registration of a worker needs upgrading;

.. code-block:: python

	# test_worker_10.py
	import uuid
	import layer_cake as lc
	from test_api import Xy, table_type
	from test_function_10 import texture

	def worker(self):
		tag = uuid.uuid4()
		lc.publish(self, f'test-multihosting:worker-10:{tag}')
		m = self.input()
		if not isinstance(m, lc.Published):
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

			table = texture(x=m.x, y=m.y)
			self.send(lc.cast_to(table, table_type), self.return_address)

	lc.bind(worker)

	if __name__ == '__main__':
		lc.create(worker)

The interesting line of code is;

.. code-block:: python

	lc.publish(self, f'test-multihosting:worker-10:{tag}')

The name has been augmented with a UUID as the trailing field. Every instance of this :func:`worker()` is automatically
announced to the network under a unique name. Establishing a client session from the :func:`server()` now looks like;

.. code-block:: python

	# test_server_10.py
	import layer_cake as lc
	from test_api import Xy

	DEFAULT_ADDRESS = lc.HostPort('127.0.0.1', 5050)
	SERVER_API = [Xy,]

	def server(self, server_address: lc.HostPort=None):
		server_address = server_address or DEFAULT_ADDRESS

		lc.listen(self, server_address, http_server=SERVER_API)
		m = self.input()
		if not isinstance(m, lc.Listening):
			return m

		lc.subscribe(self, r'test-multihosting:worker-10:[-a-f0-9]+')
		m = self.input()
		if not isinstance(m, lc.Subscribed):
			return m

		worker_spool = self.create(lc.ObjectSpool, None)

		while True:
			m = self.input()
			if isinstance(m, Xy):
				pass
			elif isinstance(m, lc.Returned):
				d = self.debrief()
				if isinstance(d, lc.OnReturned):
					d(self, m)
				continue
			elif isinstance(m, lc.Available):
				self.send(lc.JoinSpool(m.publisher_address), worker_spool)
				continue
			elif isinstance(m, lc.Dropped):
				self.send(lc.LeaveSpool(m.remote_address), worker_spool)
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

			a = self.create(lc.GetResponse, m, worker_spool)
			self.on_return(a, respond, return_address=self.return_address)

	lc.bind(server)

	if __name__ == '__main__':
		lc.create(server)

The first line of interest is;

.. code-block:: python

	lc.subscribe(self, r'test-multihosting:worker-10:[-a-f0-9]+')

This :func:`server()` is registering interest in any name matching a pattern. The trailing field is a regular expression that
will generally match the text version of a UUID.

To try out this new arrangement;

.. code-block:: console

	$ layer-cake destroy
	$ layer-cake create
	$ layer-cake add test_server_10.py server
	$ layer-cake add test_worker_10.py worker --role-count=8

An initial ``destroy`` command deletes the previous definition of the composite process. The ``add`` command accepts a ``--role-count``
parameter that is used to add multiple instances of the same module. Decoration of the instance name with an ordinal number is automated;

.. code-block:: console

	$ layer-cake list --long-listing
	server		/home/.../multihosting/test_server_10.py 4/7/500
	worker-0	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-1	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-2	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-3	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-4	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-5	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-6	/home/.../multihosting/test_worker_10.py 4/7/502
	worker-7	/home/.../multihosting/test_worker_10.py 4/7/502

Go ahead and run this latest service;

.. code-block:: console

	$ layer-cake run --debug-level=DEBUG
	<0000000e>ListenConnect - Created by <00000001>
	<0000000e>ListenConnect - Received Start from <00000001>
	...
	<00000012>layer_cake - run (...,home_path=.../multihosting/.layer-cake)
	<00000013>head_lock - Created by <00000012>
	<00000013>head_lock - Sent Ready to <00000012>
	<00000012>layer_cake - Received "Ready" from <19>
	...
	<0000001c>ProcessObject[INITIAL] - Created by <00000012>
	<0000001c>ProcessObject[INITIAL] - Received Start from <00000012>
	<0000001c>ProcessObject[INITIAL] - .../group-cake ... .../.layer-cake
	<0000001c>ProcessObject[INITIAL] - Started process (1559661)
	...
	<00000012>Group[INITIAL] - Created by <00000011>
	<00000012>Group[INITIAL] - Received Start from <00000011>
	...
	<0000000e>ListenConnect - Listening on "127.0.0.1:43745", ...
	...
	<00000013>ProcessObject[INITIAL] - Created by <00000012>
	<00000014>ProcessObject[INITIAL] - Created by <00000012>
	<00000015>ProcessObject[INITIAL] - Created by <00000012>
	<00000016>ProcessObject[INITIAL] - Created by <00000012>
	...
	<00000013>ProcessObject[INITIAL] - Received Start from <00000012>
	<00000013>ProcessObject[INITIAL] - .../python3 .../test_worker_10.py ...
	...
	<00000014>ProcessObject[INITIAL] - .../python3 .../test_server_10.py ...

The logs show the :func:`server()` being notified of the presence of a :func:`worker()` and the information being passed onto
the spool. This process is repeated the expected number of times.

A final implementation of multihosting has been included, i.e. ``test_server_11.py``. Load testing of the service highlighted
those areas that struggled as load increased. Generally these could be tuned away using configuration values in the network
service. Under extreme load the network stack will shutdown the listen, resulting in a :class:`~.NotListening` message arriving
at the :func:`server()`. This final implementation takes a more careful approach to termination, performing a managed
termination of the spool and the subscription. See the following section for notes on configuring a group for automatic
restarts.

Connecting To Multiple Hosts
****************************

At this point there is no more coding to be done. Courtesy of pubsub networking, the latest version of :func:`worker()` can
be deployed anywhere on a network and the :func:`server` will find it. However, proper operation will require some initial,
one-time setup.

The next level of pubsub is provided by ``host-cake``. The presence of this component enables a wider range of networking
scenarios, but still within the boundary of a single host. Assuming that the previous demonstration of ``group-cake`` is
still running, enter the following command in a separate shell;

.. code-block:: console

	$ host-cake --debug-level=DEBUG

The existing ``group-cake`` process automatically connects to the new ``host-cake`` process. All the service information it
is holding is pushed up to the new process. Open another shell and enter the following command;

.. code-block:: console

	$ python3 test_worker_10.py --debug-level=DEBUG

The new :func:`worker()` instance is immediately added to the pool of workers. This demonstrates pubsub without the presence
of ``group-cake`` in the sense that this application process connects directly to the ``host-cake`` process.

To verify that all the pieces of your software solution are properly installed into the publish-subscribe machinery, use
the ``layer-cake network`` command;

.. code-block:: console

	(.env) toby@seneca:~/../multihosting$ layer-cake network
	[HOST] host-cake (9e7db6d6)
	+   [GROUP] group-cake (02f461b3)
	+   +   [PROCESS] test_worker_10.py (873dd3e9)
	+   +   [PROCESS] test_server_10.py (565edd3c)
	+   +   [PROCESS] test_worker_10.py (edf78eec)
	+   [PROCESS] test_worker_10.py (95440db7)
	+   [PROCESS] layer-cake (ba2eb859)

This shows the composite process (``group-cake``), the standalone ``test_worker_10.py`` and the ``layer-cake`` CLI, all making
connections to the local instance of ``host-cake``. There is extensive information available through the ``network`` command, including
listing of all current subscriber-to-publisher sessions. For further information look :ref:`here<layer-cake-command-reference-network>`.

There can be any number of composite processes (i.e. ``group-cake``) and application processes connecting to the local ``host-cake``.
As demonstrated, once ``host-cake`` is in place this community of processes requires zero networking configuration. The local host
should be configured with the following commands;

.. code-block:: console

	$ cd <operational-folder>  
	$ layer-cake create  
	$ layer-cake add host-cake  
	$ layer-cake update group --retry='{"regular_steps": 30.0}'

The update command is used to configure a restart of ``host-cake`` in 30 seconds, in the event that it terminates. Other members
of the retry argument (i.e. :class:`~.RetryIntervals`) are available to randomize the delay. At boot-time the host should execute
the following command;

.. code-block:: console

	$ cd <operational-folder>  
	$ layer-cake start

The next level of pubsub support is provided by ``lan-cake``. Setup at this level is a bit more involved, especially if the
operational environment is a strictly controlled network. The new ``lan-cake`` process needs to be located on a machine by
itself. More accurately it cannot be cohabiting a machine with an application process such as ``test_server_10.py``.

The simplest deployment of the ``lan-cake`` process would be to configure the process to run at boot-time, on a dedicated
host. This might be appropriate use of an SBC, e.g. a Raspberry Pi. Otherwise, this is the least likely scenario and given
the low resource requirements of the ``lan-cake`` process, probably a squandering of computing power.

The next option is to configure the process to run at boot-time on a dedicated virtual machine, e.g. using VirtualBox. This
provides the separation that the process needs from all application processes without the cost of dedicated hardware. The
physical host should be configured to start the virtual machine at boot-time.

Lastly, the ``lan-cake`` process may be installed alongside other server-room software, on a pre-existing host within the
operational network.

If at all practicable, the chosen host should be assigned the standard **layer-cake** LAN IP address. This results in an
environment where every **layer-cake** process involved in inter-host networking can proceed with zero configuration. This
applies to all ``host-cake``, ``group-cake`` and application processes that ever run within the target network.

The standard **layer-cake** LAN IP is derived from the private address range in use, the primary IP of the local host, a
defined station number (195) and a defined port number (54195), i.e.

* 10.0.0.195  
* 172.16.0.195  
* 192.168.0.195

The starting point is the primary IP of the local host. This is matched against the possible private address ranges and
the final octet is replaced with the station number. Intervening octets are set to the base values for that range.

If the standard **layer-cake** LAN IP cannot be used then every connecting process must be started with a command like;

.. code-block:: console

	$ python3 test_worker_10.py --connect-to-directory=’{“host”: “10.0.0.133”, “port”: 29101}’

Installing and configuring ``host-cake`` appropriately on every operational host is one strategy for reducing the
potential for related problems;

.. code-block:: console

	$ layer-cake update host-cake --directory-at-lan=’{“host”: “10.0.0.133”, “port”: 29101}’

Instances of ``group-cake`` and application processes on this host will connect to this ``host-cake`` and thereby join
the directory rooted at the specified address. Once there is a designated ``lan-cake`` machine and it is configured
with the proper network address, it also needs to be configured with the following commands;

.. code-block:: console

	$ cd <operational-folder>  
	$ layer-cake create  
	$ layer-cake add lan-cake  
	$ layer-cake update group --retry='{"regular\_steps": 30.0}'

At boot-time the host should execute the following command;

.. code-block:: console

	$ cd <operational-folder>
	$ layer-cake start

A Distributed, Hierarchical Directory
*************************************

Conceptually, the **layer-cake** directory is a tree with ``group-cake``, ``host-cake`` and ``lan-cake`` at the nodes and
application processes as the terminal leaves. A ``lan-cake`` node is at the root of the tree (i.e. the top of the hierarchy).

Installation and configuration of the directory is mostly automated. The items that cannot be automated are;

* installation of ``host-cake``,  
* determining the host for ``lan-cake``,  
* determining the IP address for the ``lan-cake`` host,  
* installation of ``lan-cake``.

These are all one-time operations performed on an as-needed basis; if you are not multihosting then there is no need
for ``lan-cake``. Composite processes (i.e. using ``group-cake``) are completely self-contained and don’t require the
presence of other directory components.

The **layer-cake** directory provides service to any **layer-cake** process. This means that the one-time installation and
configuration of the service will support the operation of multiple networking solutions, side-by-side. This also
applies to multiple instances of the same solution, e.g. developers can work on their own private instances of a
distributed solution by adopting an appropriate naming convention. All without concerns about duplicate assignment of
IP addresses and port numbers, or misconfiguration.

A list of the benefits of pubsub networking is long. Less obvious benefits derive from the fact that all the network
address information pertaining to the solution is updated the moment that anything changes.

Pubsub enables the initial installation and startup of the different components in a solution. This can happen in any
order and over an extended period (e.g. phased rollout).

Components of the solution, such as the ``test_worker_10.py``, can be added and deleted as required. Investing in a
cluster of machines and adding those computing resources (e.g. instances of workers) to a live system is fully automated.

Components are free to move around. A replacement service can be created on a new host. When ready, the old service is
shut down and the replacement is started. All reconnections to the new address are automated and immediate.

Lastly, solutions can be rearranged across any collection of hosts including a lone host. For development purposes the
ability to run an entire solution as a single composite process might be advantageous and is always an option. It is
also possible to generate portable images of composite processes that just need a Python environment to run. Copy it
to a laptop for demonstrations, sales or training.

Both the :func:`~.publish()` and :func:`~.subscribe()` functions accept a scope parameter;

.. code-block:: python

	lc.publish(self, 'super-system:log-store', scope=lc.ScopeOfDirectory.GROUP)

Service information is not propagated beyond its declared scope. Even with connectivity through ``host-group`` or ``lan-group``
processes, subscribers outside the group cannot see the ``super-system:log-store`` and cannot establish a session.

Where no scope is specified, the default is HOST. For full, automated matching of all subscribers to their intended
services, this value might have been set at LAN. However, that could easily lead to unintended polling in the search
for a ``lan-cake`` that will never be installed and inadvertent services leaks, i.e. access to a service that was never
intended to be widely available.

Services with the same name can be registered within the directory. The name ``super-system:log-store`` can be registered
with GROUP scope in multiple groups within a LAN, but there can only be one instance of a name at a given scope. There
can only be a single instance of ``home-automation:power-supply`` at the LAN scope.

Pubsub behaves in a manner similar to the symbol lookups in programming languages. The instance of ``super-system:log-store``
at GROUP scope has precedence over the instance registered at LAN scope; the GROUP instance is considered to be “nearer”.

Over time the different instances of services will come and go, as a consequence of events such as network outages and
software updates. This creates decision points for a subscriber;

* the nearest instance of ``super-system:log-store`` crashes but there is another instance at LAN scope,  
* the connected instance is at LAN scope but the instance at GROUP has restarted.

Layer cake implements two specific responses to these different scenarios. Firstly, there is fallback operation, where an
existing connection to the nearest instance is lost and another instance is registered in the wider directory. A new
session is immediately established with the alternate instance. The subscriber receives a sequence of :class:`~.Dropped`
and :class:`~.Available` messages.

The second response is to upgrade an existing session. This is the reverse of the events described in the previous
paragraph. This is when the “nearest” instance subsequently recovers. The subscriber receives another sequence
of :class:`~.Dropped` and :class:`~.Available` messages and finds itself messaging with the new instance at the original scope.

Recovery of instances at a wider scope than an established session does not affect the established session.
