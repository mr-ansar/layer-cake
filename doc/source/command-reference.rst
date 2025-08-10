.. _command-reference:

Command Reference
#################

Definitions, Acronyms And Abbreviations
***************************************

.. list-table::
   :widths: 25 90
   :header-rows: 1

   * - Name
     - Notes
   * - *executable*
     - Normally a Python module ending in ``.py`` but also any executable file, e.g. ``host-cake``.
   * - *process*
     - A loaded image, a running instance of an *executable*.
   * - *role*
     - A name unique within a *home*, a context for a *process*.
   * - *home*
     - A folder, the name of that folder, a collection of *roles* and their associated *processes*.
   * - *encoding*
     - A full **layer-cake** representation of complex data, using JSON.
   * - *settings*
     - A set of encodings configured for each role, loaded and passed to the associated process on startup.
   * - *command*
     - Text typed into a command shell, an *executable* followed by zero or more *words*, *arguments* and *flags*.
   * - *argument*
     - An element of a *command*, text structured as \-\-<*name*>=<*value*> (double-dash).
   * - *flag*
     - An element of a *command*, short form of an *argument*, \-<*initial-letters-of-words*>=<*value*> (single-dash).
   * - *value*
     - A JSON fragment, stripped back alternative to full *encoding*.
   * - *word*
     - An element of a *command*, text not starting with a dash.

Summary Of Commands
*******************

Composing Collections Of Processes
==================================

* layer-cake :ref:`create<command-reference-create>` <*home*> *settings*…
* layer-cake :ref:`add<command-reference-add>` <*executable*> <*role*> <*home*> *settings*…
* layer-cake :ref:`update<command-reference-update>` <*search*>… *settings*…
* layer-cake :ref:`edit<command-reference-edit>` <*role*>
* layer-cake :ref:`delete<command-reference-delete>` <*search*>…
* layer-cake :ref:`list<command-reference-list>` <*search*>…
* layer-cake :ref:`destroy<command-reference-destroy>` <*home*>

Managing Operational Processes
==============================

* layer-cake :ref:`run<command-reference-create>` <*search*>…
* layer-cake :ref:`start<command-reference-start>` <*search*>…
* layer-cake :ref:`stop<command-reference-stop>`
* layer-cake :ref:`status<command-reference-status>` <*search*>…
* layer-cake :ref:`history<command-reference-history>` <*role*>
* layer-cake :ref:`returned<command-reference-returned>` <*role*>
* layer-cake :ref:`log<command-reference-log>` <*role*>

Network Support
===============

* layer-cake :ref:`network<command-reference-network>` <*arguments*>…
* layer-cake :ref:`ping<command-reference-ping>` <*unique-id*>

Development Automation
======================

* layer-cake :ref:`resource<command-reference-resource>` <*executable*> <*folder*>…
* layer-cake :ref:`model<command-reference-model>` <*role*> <*folder*>…
* layer-cake :ref:`script<command-reference-script>` <*arguments*>…

General Information
*******************

The **layer-cake** tool creates, modifies, executes and deletes a *home*. It implements a set of sub-commands, identifiable as
the first *word* on the command line. Each of these sub-commands accepts further information often including an *executable*
and *role*, as further *words* on the command line. Most sub-commands also support the entry of these entities as
explicit *arguments*. Ordering of *arguments* has no significance and skipping an argument does not influence assumptions
about the next.

Where no *home* is specified, the default is ``.layer-cake``.

Modification Of Live Files
**************************

Commands modifying the contents of a *home* such as ``update`` and ``script``, must consider running processes. These commands
determine the roles to be affected by their activities and then check for the presence of associated processes. Detection
of even a single associated process terminates the command.

.. _command-reference-create:

CREATE
******

    $ layer-cake create [<*home-path*>] [<*settings*> …]

Create the disk area for a new, empty composite process. Additional *settings* are stored in the *home*,
for subsequent passing to the ``group-cake`` process. The command accepts the following;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *location of the composition*
   * - **directory-at-host**
     - string
     - *connect to the custom address*
   * - **directory-at-lan**
     - string
     - *connect to the custom address*
   * - **encrypted-directory**
     - boolean
     - *enable directory encryption*
   * - **retry**
     - :class:`~.RetryIntervals`
     - *enable restarts and set the delay*
   * - **main-role**
     - string
     - *return the result of the specified role*

An attempt to create a home that already exists is an error. A custom location for
the next pubsub scope can be specified as ``directory-at-host`` or ``directory-at-lan``,
i.e. not both. By default, a composite process makes no pubsub connections. Where a process
in the composition attemps to register information at a higher scope, the process will
automatically connect to the default ``host-cake``. Setting a custom location overrides
the default behaviour.

.. _command-reference-add:

ADD
***

    $ layer-cake add <*executable*> [<*role*> [<*home-path*>]] [<*settings*> …]

Capture the details associated with a new process. Additional *settings* are stored in the *home*,
for subsequent passing to the new process. The command accepts the following;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *name of the process within this composition*
   * - **home-path**
     - string
     - *location of the composition*
   * - **role-count**
     - int
     - *number of copies to add*
   * - **role-start**
     - int
     - *base number for decoration of copies*

A typical command includes an *executable*, a *role-name*, a *home-path* and an optional list of *arguments*.
The *role-name* is optional and defaults to the basename of the *executable*. The command line *arguments* are
used to initialize the *settings* for the new process.

Role names are unique identities for instances of executables. There can only be a single instance of a role
name within a given home.

The ``role-count`` argument can be used to add blocks of processes. The command performs a loop controlled by
the ``role-start`` and ``role-count`` values. On each iteration the command decorates the ``role-name`` with the loop index,
and then adds the process.

.. _command-reference-update:

UPDATE
******

    $ layer-cake update <*search*> […] <*settings*> […]

Update the *settings* associated with one or more existing roles. Save that information within the specified home.
The command accepts the ``home-path`` argument plus whatever arguments are accepted by the selected processes;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*

Value strings can contain spaces and newlines, but complex encodings become increasingly difficult to pass
safely (i.e quote successfully) on the command-line. Consider the following ``edit`` command.

.. _command-reference-edit:

EDIT
****

    $ layer-cake edit <*role*>

Edit the *settings* associated with an existing *role*, in the specified *home*. The command
opens a session with the **layer-cake** text editor. The session starts with a copy of the
current values. If the file is modified and the contents can be successfully decoded, the
*settings* are updated.

To select the text editor, set the ``LC_EDITOR`` environment variable;

.. code-block:: console

	$ LC_EDITOR=nano layer-cake edit server

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *folder path, name of the home*
   * - **home-path**
     - string
     - *folder path, name of the home*

Contents of a *settings* file can be complex. Use of the ``update`` command can be the easier way
to configure a role one setting at a time. Once the *settings* have been populated, the ``edit``
command can be the quick way to make small changes to existing values.

.. _command-reference-delete:

DELETE
******

    $ layer-cake delete <*search*> […]

Delete all the files and folders associated with one or more existing roles. This includes materials created
by the ``layer-cake`` command and those materials created by activities of the operational process.

The command also accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **all-roles**
     - bool
     - *enable deletion of every role*

.. _command-reference-list:

LIST
****

    $ layer-cake list [<*search*> …]

List the matching roles currently defined in the specified *home*, the default is to list all. The command
accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **long-listing**
     - bool
     - *include role details*
   * - **group-role**
     - bool
     - *include the group*
   * - **sub-roles**
     - bool
     - *include the sub-roles*

The default command produces a basic list of the roles within the default home;

.. code::

   $ layer-cake list
   server
   client
   $

Passing the ``long-listing`` argument produces additional information including the *executable* that
performs the *role* and some disk usage statistics (*folders*/*files*/*bytes*);

.. code::

   $ layer-cake list -ll
   factorial                factorial (1/0/0)
   snooze                   snooze (1/0/0)
   zombie                   zombie (1/3/3987)
   totals                   (4/3/3987)
   $

The ``-ll`` *flag* shortform was used for the ``long-listing`` *argument*.

.. _command-reference-destroy:

DESTROY
*******

    $ layer-cake destroy [<*home-path*>]

Destroy all the files and folders associated with the *home*. This includes materials created by the **layer-cake**
command and those materials created by activities of the operational processes. Attempting to destroy a home that
doesn't exist is an error.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*

.. _command-reference-run:

RUN
***

    $ layer-cake run [<*search*> …]

Run instances of the matching roles within the selected *home*, as a *composite process*. The default is to run all roles.
Direct the resulting processes to operate within the confines of the disk spaces managed by the *home*. Route the logs from
all the processes to ``stderr`` and wait for completion of every process or a user intervention, i.e. a control-c. A control-c
initiates a termination protocol with every process still active. The run completes when every process has terminated.

An instance of the ``group-cake`` process is added into every run in a supervisory role. All *role* processes are
children of the ``group-cake`` process. As a supervisor its duties include managing restarts of *roles* as configured
into its *settings*. The ``group-cake`` process can be accessed as the ``group`` role.

The command also accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **main-role**
     - string
     - *role selected as the focus role*

By default logging is disabled. Passing a ``debug-level`` argument enables the output of those logs marked
with the specified level or higher. Log output appears on ``stderr``.

Assigning a ``main-role`` alters some process orchestration behaviour and causes the composite process to exit
with the termination value from the named role, rather than the default table of termination values. If the
``main-role`` terminates it will take down the entire composite process. Without a ``main-role`` the composite
will continue as long as there is a single remaining process.

.. _command-reference-start:

START
*****

    $ layer-cake start [<*search*> …]

Run instances of the matching roles within the selected *home*, as a *composite process*. The default is to run all roles.
Do not wait for completion - return control back to the shell immediately. Direct the resulting processes to operate within
the confines of the disk spaces managed by the *home*. Also, direct the processes to send their logs into the
designated FIFO storage area within the *home*. Attempting to start a role that doesn't exist is an error.

For more information about the running of *composite processes* refer to :ref:`run<command-reference-run>`.

The command accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **main-role**
     - string
     - *role selected as the focus role*

.. _command-reference-stop:

STOP
****

    $ layer-cake stop

Stop all running processes, in the selected *home*. Without a ``home-path`` argument the *home* defaults
to ``.layer-cake`` in the current folder. 

The command also accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*

.. _command-reference-status:

STATUS
******

    $ layer-cake status [<*search*> …]

List the selected roles currently active in the specified *home*. The default is to list all roles. The command
accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **long-listing**
     - bool
     - *enable a more detailed output*
   * - **group-role**
     - bool
     - *include group role within the output*
   * - **sub-roles**
     - bool
     - *include sub-roles within the output*

The simplest form of the command produces a basic list of the active roles within the default home;

.. code::

   $ layer-cake status
   server
   worker
   $

Passing the ``--long-listing`` argument produces additional information including the process ID and
elapsed runtime of each process;

.. code::

   $ layer-cake status -ll
   zombie                   <1292610> 5.2s

.. _command-reference-history:

HISTORY
*******

    $ layer-cake history <*role*>

Present the recent process activity associated with the specified *role*, in the given *home*. The command
accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *name of the role*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **long-listing**
     - bool
     - *enable a more detailed output*

Output includes a start time, elapsed run time and the type of the return value;

.. code::

   $ layer-cake history zombie-0
   [0] 9m35.0s ago … 8m18.8s (Faulted)
   [1] 10.5s ago … 3.4s (Ack)
   $

Each line in the output represents a single process that executed under the identity of the specified
role. An index is included to assist with the use of commands such as ``returned`` and ``log``. The output
is oldest-first, i.e. the line with the index ``[0]`` records the oldest process still remembered by
the *home*.

History information is stored in the *home* as a FIFO of start and stop times, and return values. The
FIFO is limited to a small number of entries (currently this is set at 8).

Passing the ``--long-listing`` argument produces explicit start and end times in full ISO format;

.. code::

   $ layer-cake history zombie -ll
   2023-06-08T00:23:48.905221 … 2021-10-21T06:44:58.965063 (6h21m) Ack
   2021-10-21T06:45:00.068706 … 2021-10-21T06:53:59.069315 (8m59.0s) Ack
   2021-10-21T06:54:04.938309 … 2021-10-21T17:45:38.023162 (10h51m) Ack
   2021-10-21T22:34:13.239548 … 2021-10-21T22:40:08.586523 (5m55.3s) Ack
   2021-10-21T22:40:17.162771 … ?

The question mark ``?`` denotes a process that has not yet returned.

.. _command-reference-returned:

RETURNED
********

    $ layer-cake returned <*role*>

Output the value returned by the process executing as the *role*, in the specified *home*. A
role name is required.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *name of the role*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **start**
     - integer
     - *index into the FIFO of history records*
   * - **timeout**
     - float
     - *number of seconds to wait for the completion of an active role*

The simplest form of the command outputs the JSON encoding of the latest return value;

.. code::

   $ layer-cake returned zombie-0
   {
       "value": [
           "layer-cake.point_runtime.Ack",
           {},
           []
       ]
   }
   $

Where the selected role is also active, the command will wait until the associated process completes
and returns a value. Passing a timeout argument ensures that the command does not wait forever.

.. _command-reference-log:

LOG
***

    $ layer-cake log <*role*> [--<*beginning*>=<*value*] [--<*ending*>=<*value*>]

Output a sequence of logs generated by the *role*, in the specified *home*. The sequence has a beginning
and an ending point. Both are optional and output defaults to a page of the most recent logs. The absence
of an ending (i.e. ``None``) implies “everything from the given starting point”. An attempt to access the
logs of a non-existent role is an error.

The beginning can be expressed as;

* a count of the most recent lines (default),
* a UTC time representation,
* a local time representation,
* a latest day, week, etc, e.g. from the beginning of the current week,
* an index into the ``history`` records for the role,
* or a backward relative time value.

The ending can be expressed as;

* a UTC time representation,
* a local time representation,
* a forward relative time value,
* a count of log records.

The absence of an ending causes the output of all logs after the beginning. The command accepts the
following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *name of the role*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **clock**
     - bool
     - *enable entry and output of local times*
   * - **tail**
     - int
     - *start by rewinding the specified number of lines*
   * - **from_**
     - string
     - *ISO format time, either local or UTC depending on "clock"*
   * - **last**
     - enum
     - *MONTH, WEEK, DAY, HOUR, MINUTE, HALF, QUARTER, TEN or FIVE*
   * - **start**
     - integer
     - *index into the FIFO of history records*
   * - **back**
     - timespan
     - *a negative, relative time value*
   * - **to**
     - string
     - *ISO format time, either local or UTC depending on "clock"*
   * - **span**
     - timespan
     - *a positive, relative time value*
   * - **count**
     - integer
     - *number of records to list*
   * - **sample**
     - string
     - *name of a series of sampled values*
   * - **tags**
     - string
     - *list of USER_TAGs, ignore others*

Simple use looks like;

.. code::

   $ layer-cake log zombie
   2020-11-07T15:52:25.745 + <00000008>lock_and_hold - Created by <00000001>
   2020-11-07T15:52:25.745 > <00000008>lock_and_hold - Sent Ready to <00000001>
   2020-11-07T15:52:25.746 + <00000009>start_vector - Created by <00000001>
   2020-11-07T15:52:25.746 ~ <00000009>start_vector - Executable "/home/dennis/some/project/dist/zombie" as process (1216338)
   2020-11-07T15:52:25.746 + <0000000a>zombie - Created by <00000009>
   2020-11-07T15:52:25.746 ^ <0000000a>zombie - Do nothing until interrupted
   ..

Other uses of the ``log`` command include (output omitted);

.. code::

   $ layer-cake log zombie-0 --clock
   $ layer-cake log zombie-0 --from_=2020-11-07T16:00:44.565       # note that the trailing underscore is sadly required
   $ layer-cake log zombie-0 --last=WEEK
   $ layer-cake log zombie-0 --start=0
   $ layer-cake log zombie-0 --back=7d10s
   $ layer-cake log zombie-0 --to=2020-11-07T17:00
   $ layer-cake log zombie-0 --span=30s
   $ layer-cake log zombie-0 --count=40
   $ layer-cake log zombie-0 --start=1 --count=10
   $ layer-cake log zombie-0 --last=WEEK --sample=metering

Use of the ``clock`` argument causes the output of local time values. To distinguish these from UTC times the ``T`` separator
between the date and time fields is folded to lowercase. Input time values such as ``from_`` are also assumed to be in
UTC format. Use of the ``clock`` argument in a distributed working environment is generally perilous.

.. _layer-cake-command-logging-information:

Exposure to logging occurs in three contexts, from a ``python3 test_worker_10.py`` command, a ``layer-cake run`` command, or from
a ``layer-cake log`` command. The first two stream the logging output from one or more live processes onto ``stderr``, necessitating
the inclusion of a process ID. Each log entry contains the columns listed below, taking note that the process ID does not appear
in ``layer-cake log`` output;

.. list-table::
   :widths: 6 20 15 75
   :header-rows: 1

   * - #
     - Name
     - Type
     - Notes
   * - [0]
     - Process ID
	 - string
     - *process ID of the process that generated the log*
   * - [1]
     - Timestamp
	 - :class:`~.WorldTime`
     - *time the log was generated*
   * - [2]
     - User Tag
	 - :class:`~.USER_TAG`
     - *enumeration of standard async events, e.g. create, send, receive*
   * - [3]
     - Object ID
	 - integer
     - *serial id of the originating object*
   * - [4]
     - Object Type
	 - :ref:`object type<lc-object-type>`
     - *the name of the function or class that generated the log*
   * - [5]
     - Notes
	 - string
     - *description, notes or key-value samples*

.. _command-reference-network:

NETWORK
*******

    $ layer-cake network [<*arguments*> …]

Display the current contents of the publish-subscribe network. This command joins the local publish-subscribe
context and then queries the network for every connected process, publication, subscription, route (subscription
matched to publication) and connected session. By default the command lists the fundamental structure (i.e. processes
only);

.. code-block:: console

	(.env) toby@seneca:~/../multihosting$ layer-cake network
	[LAN] lan-cake (f1a042b8)
	+   [HOST] host-cake (45199baf)
	+   +   [PROCESS] test_worker_10.py (87c00a45)
	+   [HOST] host-cake (fcf744be)
	+   +   [PROCESS] test_server_10.py (0ae5c793)
	+   +   +   [LIBRARY] test_worker_10.py (7abbd14c)
	+   +   [PROCESS] layer-cake (0f7a54d0)

There is a topmost ``LAN`` comprising of two ``HOST`` processes. The second ``HOST`` is running two processes,
one of which is managing a ``LIBRARY`` process. Each process is listed as a scope, the running executable and a
unique id (UUID).

Joining the local publish-subscribe network usually involves connection to the local instance of ``host-cake``.
The ``layer-cake`` CLI behaves in exactly the same manner as any **layer-cake** process - in the absence of other
information, connection to ``host-cake`` is fully automated. In the configuration shown above the ``layer-cake``
process has connected to the second ``host-cake``. There is also the ability to specify the directory
IP and port on the command line, e.g. ``--connect-to-directory``.

.. note::

	A composite process that contains no registrations beyond the ``GROUP`` scope will make no
	automated attempts to connect to a ``host-cake`` and its existence will remain invisible to
	the ``network`` command.

Adding the ``--directory-addresses`` flag decorates the listings with IP and port information;

.. code-block:: console

	(.env) toby@seneca:~/../multihosting$ layer-cake network --directory-addresses
	[LAN] lan-cake (f1a042b8) 192.168.1.176 <C>(not set) <L>0.0.0.0:54195
	+   [HOST] host-cake (45199baf) 192.168.1.13 <C>192.168.1.176:54195 <L>127.0.0.1:54195
	+   +   [PROCESS] test_worker_10.py (87c00a45) 192.168.1.13 <C>127.0.0.1:54195 <L>(not set)
	+   [HOST] host-cake (fcf744be) 192.168.1.106 <C>192.168.1.176:54195 <L>127.0.0.1:54195
	+   +   [PROCESS] test_server_10.py (0ae5c793) 192.168.1.106 <C>127.0.0.1:54195 <L>127.0.0.1:33465
	+   +   +   [LIBRARY] test_worker_10.py (7abbd14c) 192.168.1.106 <C>127.0.0.1:33465 <L>(not set)
	+   +   [PROCESS] layer-cake (cba099a5) 192.168.1.106 <C>127.0.0.1:54195 <L>(not set)

Taking ``test_worker_10.py`` (87c00a45) as an example, the process is running on a host that is known within the local
network as ``192.168.1.13``. It is connected to a parent directory at ``127.0.0.1:54195`` and is not accepting any
connections from sub-directory processes (not set). A standard technique is used to infer the local network address.

The command accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **open-scope**
     - :class:`~.ScopeOfDirectory`
     - *probe to the specified scope, default HOST*
   * - **full-identity**
     - bool
     - *list the full length UUIDs*
   * - **directory-addresses**
     - bool
     - *include structural IP and port information*
   * - **list-published**
     - bool
     - *list all registered names*
   * - **list-subscribed**
     - bool
     - *list all registered searches*
   * - **list-routed**
     - bool
     - *list all matches - routes*
   * - **list-connected**
     - bool
     - *list all current sessions - active routes*

Registered names are marked with a ``#``, followed by the name, unique id, and if relevant, the listening IP
and port. Registered searches are marked with a ``?`` followed by the search pattern and unique id. Routes
are marked with ``<>``, followed by the matched name and then a pair of subscriber-publisher unique ids. Lastly,
connections are marked with a ``>``, followed by the matched name and scope, and either a pair of IP addresses for
the current, active transport or a pair of unique ids.

.. code-block:: console

	[PROCESS] test_server_10.py (0ae5c793)
	+   # "test-multihosting:worker-10:aefbd788-007e-4e0b-b43c-920820bb9c1e" (8611e17e) 0.0.0.0:42615
	+   # "test_worker_10" (87e86ddc)
	+   # "test-multihosting:worker-10:f91a0a51-a0da-487a-a4aa-85b5d8eee9fd" (b0e651d3) 0.0.0.0:41081
	+   ? "test-multihosting:worker-10:[-a-f0-9]+" (4d0ddfee)
	+   ? "test_worker_10" (8d3454e3)
	+   <> "test-multihosting:worker-10:aefbd788-007e-4e0b-b43c-920820bb9c1e" (4d0ddfee -> 8611e17e)
	+   <> "test_worker_10" (8d3454e3 -> 87e86ddc)
	+   <> "test-multihosting:worker-10:f91a0a51-a0da-487a-a4aa-85b5d8eee9fd" (4d0ddfee -> b0e651d3)
	+   ? "test-multihosting:worker-10:[-a-f0-9]+" (4d0ddfee)
	+   +   > "test-multihosting:worker-10:aefbd788-007e-4e0b-b43c-920820bb9c1e"[PROCESS] (4d0ddfee -> 8611e17e)
	+   +   > "test-multihosting:worker-10:0be7bd59-0216-431f-9177-c66d470bfbf9"[LAN] (192.168.1.106:54828 -> 192.168.1.13:39097)
	+   +   > "test-multihosting:worker-10:f91a0a51-a0da-487a-a4aa-85b5d8eee9fd"[PROCESS] (4d0ddfee -> b0e651d3)
	+   ? "test_worker_10" (8d3454e3)
	+   +   > "test_worker_10"[PROCESS] (8d3454e3 -> 87e86ddc)
	+   [LIBRARY] test_worker_10.py (7abbd14c)
	+   +   # "test_worker_10" (87e86ddc)
	+   +   # "test-multihosting:worker-10:f91a0a51-a0da-487a-a4aa-85b5d8eee9fd" (b0e651d3) 0.0.0.0:41081

.. _command-reference-ping:

PING
****

    $ layer-cake ping <*unique id*>

Verify the minimal operation of a specified directory process. This commands joins the local publish-subscribe network,
searches for the given unique id and then runs a series of timed *ping* operations. A small message is sent to the
matched process and a response is expected within a few seconds. The round trip is timed.

.. code-block:: console

	(.env) toby@seneca:~/../multihosting$ layer-cake ping eac32b15
	[0] … 0.010128s
	[1] … 0.010467s
	[2] … 0.010396s
	[3] … 0.01147s

The *ping* messages travel over the directory network. There is no dedicated connection made from ``layer-cake`` to the
specified process. This inherently verifies a minimum operational status of all intervening components.

The command accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **ping-count**
     - integer
     - *number of repetitions*

.. _command-reference-resource:

RESOURCE
********

    $ layer-cake resource <*executable*> <*folder*> … [<*arguments*>]

Perform a synchronization, copying files from *folders* to the storage area within the *home*. The intention is to automate
the update of materials from external sources (e.g. repos, archives) to an area of storage dedicated to the named *executable*;
configuraton files, templates and media files, that do not change at runtime.

Default use of the command lists the changes that would occur;

.. code-block:: console

	$ layer-cake resource media_server.py ~/media
	AddFolder(path=/…/media, target=/…/.layer-cake/resource/media_server.py)
	$

This says that to synchronize the ``~/media`` folder with the ``../resource/media_server.py`` folder, would require the recursive
copying of everything in the source folder. To effect the changes just add the ``make-changes`` option;

.. code-block:: console

	$ layer-cake resource media_server.py ~/media --make-changes
	$ layer-cake resource media_server.py
	media

Without any materials to synchronize, the command defaults to listing the current contents of the target area. Instances of
the *executable* have shared, runtime access to the storage area through the :func:`~.resource_path` function.

The ``resource`` command is one of three commands that can be used to streamline the management of file-based materials, i.e.
materials that are required for the proper execution of the *composite process*;

* ``resource`` … *copy from external locations into shared, home storage area (read-only)*
* ``model`` … *copy from external locations into private, per-role home storage area (read/write)*
* ``script`` … *copy Python modules from locations of executables, into home storage area*

By combining these commands, it is also possible to create a portable image of the *composite process* - a single folder
that can be copied to other locations and executed. The new location only requires the installation of **layer-cake** and
resolution of whatever dependencies the individual application processes may bring.

The concept of a *composite process* is incomplete without addressing the issue of platform resources, including network
addresses and disk storage. The former is supported by publish-subscribe networking, while the latter is supported by the
the :func:`~.resource_path`, :func:`~.model_path` and :func:`~.tmp_path` functions, and the disk areas they provide access
to. It should be noted that **layer-cake** supports the execution of processes both as an element of a *composite process*
and as a standalone process. The three supporting functions ensure appropriate behaviour in the different contexts.

The command accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **full-path**
     - bool
     - *list the full path and name of storage area contents*
   * - **recursive-listing**
     - bool
     - *list content of folders, recursively*
   * - **long-listing**
     - bool
     - *list file attributes*
   * - **make-changes**
     - bool
     - *implement the necessary changes to bring the target area up-to-date*
   * - **clear-all**
     - bool
     - *remove all contents from the target area*

.. _command-reference-model:

MODEL
*****

    $ layer-cake model <*role*> <*folder*> … [<*arguments*>]

Perform a synchronization, copying files from *folders* to the storage area within the *home*. The intention is to automate
the update of materials from external sources (e.g. repos) to an area of storage dedicated to the named *role*. These are
assumed to be operational materials that are likely to change at runtime. As well as synchronizing from the external sources
to the *home* area it is possible to reverse the direction and take a snapshot of what the role has produced. This might be
an archiving operation, e.g. taking reference images of a database for later reinstatement.

Default use of the command lists the changes that would occur;

.. code-block:: console

	$ layer-cake model server ~/db
	AddFolder(path=/…/db, target=/…/.layer-cake/role/server)
	$

This says that to synchronize the ``~/db`` folder with the ``../role/server`` folder, would require the recursive
copying of everything in the source folder. To effect the changes just add the ``make-changes`` option;

.. code-block:: console

	$ layer-cake model server ~/db --make-changes
	$ layer-cake model server
	db

Without any materials to synchronize, the command defaults to listing the current contents of the target area. The server
process has runtime access to the storage area through the :func:`~.model_path` function.

Lastly, to take an image of the operational file materials;

.. code-block:: console

	$ layer-cake model server --get-latest=/home/roger/server-image
	AddFolder(path=/…/.layer-cake/role/server/model/db, target=/home/roger/server-image)
	$ layer-cake model server --get-latest=/home/roger/server-image --make-changes
	$ ls /home/roger/server-image
	db

Refer to the :ref:`resource<command-reference-resource>` command for further information.

The command accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **full-path**
     - bool
     - *list the full path and name of storage area contents*
   * - **recursive-listing**
     - bool
     - *list content of folders, recursively*
   * - **long-listing**
     - bool
     - *list file attributes*
   * - **make-changes**
     - bool
     - *implement the necessary changes to bring the target area up-to-date*
   * - **clear-all**
     - bool
     - *remove all contents from the target area*
   * - **get-latest**
     - str
     - *enable a reverse flow, from the home area to the specified path*

The **layer-cake** library provides file-based persistence for complex application data. Saving a table
looks like;

.. code-block:: python

	import layer_cake as lc

	table_type = lc.def_type(list[list[float]])

	f = lc.File('table', table_type)

	table = [[1.0, 2.0],[3.0, 4.0]]
	f.store(table)

This approach to persistence is further supported in the library with the :func:`~.resource_folder`,
:func:`~.model_folder` and :func:`~.tmp_folder` functions. Further information can be found :ref:`here<folders-and-files>`.

.. _command-reference-script:

SCRIPT
******

    $ layer-cake script [<*arguments*>]

Perform a synchronization, copying files from *source folders* to the storage area within the *home*. During the initiation
of a *composite process*, the modules within the home area are given precedence over the *source folders*, recorded during
the :ref:`add<command-reference-add>` operation.

This command is slightly different to ``resource`` and ``model`` in that the default command performs the analysis
of source and target areas;

.. code-block:: console

	$ layer-cake script
	AddFile(path=/…/http_server.py, target=/…/.layer-cake/script)
	AddFile(path=/…/http_api.py, target=/…/.layer-cake/script)
	AddFile(path=/…/stats.py, target=/…/.layer-cake/script)
	$

This says that to synchronize the *source folders* with the *home* area (i.e. ``.layer-cake/script``), would require the
copying of 3 source files. For some background on exactly what is happening, there are some helpful options;

.. code-block:: console

	$ layer-cake script --list-executables
	server                   /…/http_server.py
	stats                    /…/stats.py
	$

This command provides a list of the references made to Python modules, within the set of *roles*. Non-Python entries -
or rather any executable not ending in ``.py`` - is not included in the efforts of the ``script`` command. The next
useful option derives the list of unique folders present in the list of executables;

.. code-block:: console

	$ layer-cake script --list-paths
	/…/project/src
	$

The output shows that both of the *executables* from the *roles* originate from the same folder. This list of paths
becomes the *source folders* for the synchronization with the *home* area. All materials found in these folders is
copied. To effect the changes just add the ``make-changes`` option;

.. code-block:: console

	$ layer-cake script --make-changes
	$ layer-cake script --list-script
	http_server.py
	http_api.py
	stats.py

Refer to the :ref:`resource<command-reference-resource>` command for further information.

The command accepts the following arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **full-path**
     - bool
     - *list the full path and name of storage area contents*
   * - **recursive-listing**
     - bool
     - *list content of folders, recursively*
   * - **long-listing**
     - bool
     - *list file attributes*
   * - **list-scripts**
     - bool
     - *list the current contents of the target area*
   * - **list-executables**
     - bool
     - *list all configured references to Python modules*
   * - **list-paths**
     - bool
     - *list the set of unique source folders*
   * - **make-changes**
     - bool
     - *implement the necessary changes to bring the target area up-to-date*
   * - **clear-all**
     - bool
     - *remove all contents from the target area*
