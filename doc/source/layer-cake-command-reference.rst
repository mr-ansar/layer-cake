.. _layer-cake-command-reference:

Layer Cake Command Reference
############################

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

Breakdown Of Commands
*********************

Composing Collections Of Processes
==================================

* layer-cake :ref:`create<layer-cake-command-reference-create>` <*home*>
* layer-cake :ref:`add<layer-cake-command-reference-add>` <*executable*> <*role*> <*home*> *settings*...
* layer-cake :ref:`update<layer-cake-command-reference-update>` <*role*>... *settings*...
* layer-cake :ref:`edit<layer-cake-command-reference-edit>` <*role*>
* layer-cake :ref:`delete<layer-cake-command-reference-delete>` <*role*>...
* layer-cake :ref:`list<layer-cake-command-reference-list>` <*role*>...
* layer-cake :ref:`destroy<layer-cake-command-reference-destroy>` <*home*>

Managing Operational Processes
==============================

* layer-cake :ref:`run<layer-cake-command-reference-create>` <*role*>
* layer-cake :ref:`start<layer-cake-command-reference-start>` <*role*>
* layer-cake :ref:`stop<layer-cake-command-reference-stop>`
* layer-cake :ref:`status<layer-cake-command-reference-status>` <*role*>
* layer-cake :ref:`history<layer-cake-command-reference-history>` <*role*>
* layer-cake :ref:`returned<layer-cake-command-reference-returned>` <*role*>
* layer-cake :ref:`log<layer-cake-command-reference-log>` <*role*>

Development Automation
======================

* layer-cake :ref:`resource<layer-cake-command-reference-resource>` <*executable*> <*folder*>...
* layer-cake :ref:`model<layer-cake-command-reference-model>` <*role*> <*folder*>...
* layer-cake :ref:`script<layer-cake-command-reference-script>`

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

Composing Collections Of Processes
**********************************

.. _layer-cake-command-reference-create:

CREATE
======

    $ layer-cake create [<*home-path*>]

Create the disk area for a new, empty composite process. The command accepts the following *arguments*;

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
   * - **retry**
     - :class:`~.RetryIntervals`
     - *delay before process restart*
   * - **main-role**
     - integer
     - *return the result of the specified role*

An attempt to create a home that already exists is an error. A custom location for
the next pubsub scope can be specified as ``directory-at-host`` or ``directory-at-lan``,
i.e. not both. By default, a composite process makes no pubsub connections. Where a process
in the composition attemps to register information at a higher scope, the process will
automatically connect to the default ``host-cake``. Setting a custom location overrides
the default behaviour.

.. _layer-cake-command-reference-add:

ADD
===

    $ layer-cake add <*executable*> [<*role-name*> [<*home-path*>]] [\-\-<*name*>=<*value*> …]

Capture the details associated with a new process. Save that information within the specified home. The
command accepts the following additional arguments;

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

Role names are unique identities for instances of executables. There can only be a single instance of a role name within
a given home. Attempting to add a role that already exists is an error.

The ``role-count`` argument can be used to add blocks of processes. The command performs a loop controlled by
the ``role-start`` and ``role-count`` values. On each iteration the command decorates the ``role-name`` with the loop index,
and then adds the process.

.. _layer-cake-command-reference-update:

UPDATE
======

    $ layer-cake update <*role-name*> --<*name*>=<*value*> …

Update the *settings* associated with an existing role. Save that information within the specified home. The command
accepts a *role-name* and a list of *arguments*. Attempting to update a role that doesn't exist is an error.

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

Value strings can contain spaces and newlines, but complex encodings become increasingly difficult to pass
safely (i.e quote successfully) on the command-line. Consider the :ref:`edit<layer-cake-command-reference-edit>`
command.

.. _layer-cake-command-reference-edit:

EDIT
====

    $ layer-cake edit <*role-name*>

Edit the *settings* associated with an existing *role*, in the specified *home*. The command
opens a session with the **layer-cake** text editor. The session starts with a copies of the
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

.. _layer-cake-command-reference-delete:

DELETE
======

    $ layer-cake delete <*role-name*>

Delete all the files and folders associated with the *role-name*. This includes materials created by the ``layer-cake`` command
and those materials created by activities of the operational process. Attempting to delete a role that doesn't exist is
an error.

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

.. _layer-cake-command-reference-list:

LIST
====

    $ layer-cake list [<*role-name*>]

List the *roles* currently defined in the specified *home*. The command accepts the following arguments;

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

.. _layer-cake-command-reference-destroy:

DESTROY
=======

    $ layer-cake destroy [<*home-path*>]

Destroy all the files and folders associated with the *home*. This includes materials created by the layer-cake command
and those materials created by activities of the operational processes. Attempting to destroy a home that doesn't exist
is an error.

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

Managing Operational Processes
******************************

.. _layer-cake-command-reference-run:

RUN
===

    $ layer-cake run [<*role-name*> ..]

Run instances of the specified *roles* within the selected *home*, as a *composite process*. Direct the resulting
processes to operate within the confines of the disk spaces managed by the *home*. Route the logs from all the processes
to ``stderr`` and wait for completion of every process or a user intervention, i.e. a control-c. A control-c initiates
a termination protocol with every process still active. The run completes when every process has terminated.

An instance of the ``group-cake`` process is added into every run in a supervisory role. All *role* processes are
children of the ``group-cake`` process. As a supervisor its duties include managing restarts of *roles* as configured
into its *settings*. The ``group-cake`` process can be accessed as the ``group`` role.

An empty list of *roles* implicitly matches all the *roles* within the *home*.

Without a ``home-path`` argument the *home* defaults to ``.layer-cake`` in the current folder.

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

.. _layer-cake-command-reference-start:

START
=====

    $ layer-cake start [<*role-name*> ..]

Start instances of the specified *roles*, from the given *home*, as a *composite process*. Do not wait for
completion - return control back to the shell immediately. Direct the resulting processes to operate within
the confines of the disk spaces managed by the *home*. Also, direct the processes to send their logs into the
designated FIFO storage area within the *home*. Attempting to start a role that doesn't exist is an error.

For more information about the running of *composite processes* refer to :ref:`run<layer-cake-command-reference-run>`.

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

.. _layer-cake-command-reference-stop:

STOP
====

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

.. _layer-cake-command-reference-status:

STATUS
======

    $ layer-cake status [<*role-name*>...]

List the *roles* currently active in the specified *home*. The command accepts the following explicit arguments;

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

.. _layer-cake-command-reference-history:

HISTORY
=======

    $ layer-cake history <*role-name*>

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
   [0] 9m35.0s ago ... 8m18.8s (Faulted)
   [1] 10.5s ago ... 3.4s (Ack)
   $

Each line in the output represents a single process that executed under the identity of the specified
role. An index is included to assist with the use of commands such as ``returned`` and ``log``. The output
is oldest-first, i.e. the line with the index ``[0]`` records the oldest process still remembered by
the *home*.

History information is stored in the *home* as a FIFO of start and stop times, and return values. The
FIFO is limited to a small number of entries (currently this is set at 8) to cap the overhead associated
with updating the history.

Passing the ``--long-listing`` argument produces explicit start and end times in full ISO format;

.. code::

   $ layer-cake history zombie -ll
   2023-06-08T00:23:48.905221 ... 2021-10-21T06:44:58.965063 (6h21m) Ack
   2021-10-21T06:45:00.068706 ... 2021-10-21T06:53:59.069315 (8m59.0s) Ack
   2021-10-21T06:54:04.938309 ... 2021-10-21T17:45:38.023162 (10h51m) Ack
   2021-10-21T22:34:13.239548 ... 2021-10-21T22:40:08.586523 (5m55.3s) Ack
   2021-10-21T22:40:17.162771 ... ?

The question mark ``?`` denotes a process that has not yet returned.

.. _layer-cake-command-reference-returned:

RETURNED
========

    $ layer-cake returned <*role-name*>

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
           "layer-cake.create.lifecycle.Ack",
           {},
           []
       ]
   }
   $

Where the selected role is also active, the command will wait until the associated process completes
and returns a value. Passing a timeout argument ensures that the command does not wait forever.

.. _layer-cake-command-reference-log:

LOG
===

    $ layer-cake log <role-name> [--<beginning>=value] [--<ending>=<value>]

Output a sequence of logs generated by the *role*, in the specified *home*. The sequence has a beginning
and an ending point. Both are optional and output defaults to a page of the most recent logs. The absence
of an ending (i.e. ``None``) implies “everything from the given starting point”. An attempt to access the
logs of a non-existent role is an error.

The beginning can be expressed as;

* a count of the most recent lines,
* a UTC time representation,
* a local time representation,
* a latest day, week, etc, e.g. from the beginning of the current week,
* an index into the ``history`` records for the role,
* or a backward relative time value.

The ending can be expressed as;

* a UTC time representation,
* a local time representation,
* a forward relative time value,
* or a count of log records.

The command accepts the following arguments;

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
   * - **rewind**
     - int
     - *start by counting back the specified number of lines*
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

Use of the ``clock`` argument causes the output of local time values. To distinguish these from UTC times the ``T`` separator
between the date and time fields is folded to lowercase. Input time values such as ``from_`` are also assumed to be in
UTC format. Use of the ``clock`` argument in a distributed working environment is generally perilous.

Development Automation
**********************

.. _layer-cake-command-reference-resource:

RESOURCE
========

    $ layer-cake resource <*executable*> <*folder*> ...

Perform a synchronization, copying files from *folders* to the storage area within the *home*. The intention is to automate
the update of materials from external sources (e.g. repos, archives) to an area of storage dedicated to the named *executable*;
configuraton files, templates and media files, that do not change at runtime.

Default use of the command lists the changes that would occur;

.. code-block:: console

	$ layer-cake resource media_server.py ~/media
	AddFolder(path=/.../media, target=/.../.layer-cake/resource/media_server.py)
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

* ``resource`` ... *copy from external locations into shared, home storage area (read-only)*
* ``model`` ... *copy from external locations into private, per-role home storage area (read/write)*
* ``script`` ... *copy Python modules from locations of executables, into home storage area*

By combining these commands, it is also possible to create a portable image of the *composite process* - a single folder
that can be copied to other locations and executed. The new location only requires the installation of **layer-cake** and
resolution of whatever dependencies the individual application processes may bring.

The concept of a *composite process* is incomplete without addressing the issue of platform resources, including network
addresses and disk storage. The former is supported by publish-subscribe networking, while the latter is supported by the
the :func:`~.resource_path`, :func:`~.model_path` and :func:`~.tmp_path` functions, and the disk areas they provide access
to. It should be noted that **layer-cake** supports the execution of processes both as a component of a *composite process*
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

.. _layer-cake-command-reference-model:

MODEL
=====

    $ layer-cake model <*role*> <*folder*> ...

Perform a synchronization, copying files from *folders* to the storage area within the *home*. The intention is to automate
the update of materials from external sources (e.g. repos) to an area of storage dedicated to the named *role*. These are
assumed to be operational materials that are likely to change at runtime. As well as synchronizing from the external sources
to the *home* area it is possible to reverse the direction and take a snapshot of what the role has produced. This might be
an archiving operation, e.g. taking reference images of a database for later reinstatement.

Default use of the command lists the changes that would occur;

.. code-block:: console

	$ layer-cake model server ~/db
	AddFolder(path=/.../db, target=/.../.layer-cake/role/server)
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
	AddFolder(path=/.../.layer-cake/role/server/model/db, target=/home/roger/server-image)
	$ layer-cake model server --get-latest=/home/roger/server-image --make-changes
	$ ls /home/roger/server-image
	db

Refer to the :ref:`resource<layer-cake-command-reference-resource>` command for further information.

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

.. _layer-cake-command-reference-script:

SCRIPT
======

    $ layer-cake script

Perform a synchronization, copying files from *source folders* to the storage area within the *home*. During the initiation
of a *composite process*, the modules within the home area are given precedence over the *source folders*, recorded during
the :ref:`add<layer-cake-command-reference-add>` operation.

This command is slightly different to ``resource`` and ``model`` in that the default command performs the analysis
of source and target areas;

.. code-block:: console

	$ layer-cake script
	AddFile(path=/.../http_server.py, target=/.../.layer-cake/script)
	AddFile(path=/.../http_api.py, target=/.../.layer-cake/script)
	AddFile(path=/.../stats.py, target=/.../.layer-cake/script)
	$

This says that to synchronize the *source folders* with the *home* area (i.e. ``.layer-cake/script``), would require the
copying of 3 source files. For some background on exactly what is happening, there are some helpful options;

.. code-block:: console

	$ layer-cake script --list-executables
	server                   /.../http_server.py
	stats                    /.../stats.py
	$

This command provides a list of the references made to Python modules, within the set of *roles*. Non-Python entries -
or rather any executable not ending in ``.py`` - is not included in the efforts of the ``script`` command. The next
useful option derives the list of unique folders present in the list of executables;

.. code-block:: console

	$ layer-cake script --list-paths
	/.../project/src
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

Refer to the :ref:`resource<layer-cake-command-reference-resource>` command for further information.

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

Network Administration
**********************

.. _layer-cake-command-reference-network:

NETWORK
=======

    $ layer-cake network [<*group-name*> [<*home-path*>]]

View the network environment for the specified group within the specified home. Adding the ``--connect-scope`` argument also
provides for configuration of the specified environment, where connections are made from one scope to another scope, always
in an upward direction. Configuration is persistent and may affect the operation of other groups that share a common
ancestor, e.g. HOST, LAN or WAN.

The default command lists the network environment for the ``default`` group in the ``.layer-cake-home`` folder;

.. code::

	$ layer-cake network
	+ GROUP 127.0.0.1:45489

The simplest configuration command connects the same group to the installed **layer-cake-host** service;

.. code::

	$ layer-cake network --connect-scope=GROUP --to-scope=HOST
	$ layer-cake network
	+ HOST 127.0.0.1:32177
	+ GROUP 127.0.0.1:45489

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **group-name**
     - string
     - *group name, name for a collection of processes*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **connect-scope**
     - enumeration
     - *directory scope, start location of a configuration operation*
   * - **to-scope**
     - string
     - *directory scope, end location of a configuration operation*
   * - **product-name**
     - string
     - *directory identity, first part of composite identity for networking*
   * - **product-instance**
     - enumeration
     - *directory identity, second part of composite identity for networking*
   * - **custom-host**
     - string
     - *IP address or name, override a default host*
   * - **custom-port**
     - int
     - *port number, override a default port*
   * - **connect-file**
     - string
     - *file path, address and credentials for connection to layer-cake-wan*
   * - **connect-disable**
     - bool
     - *flag, enable or disable an upward connect from the specified start location*
   * - **published-services**
     - bool
     - *flag, include publisher services in the network listing*
   * - **subscribed_searches**
     - bool
     - *flag, include subscriber searches in the network listing*
   * - **routed_matches**
     - bool
     - *flag, include subscriber-publisher matches in the network listing*
   * - **accepted-processes**
     - bool
     - *flag, include active routes in the network listing*

Adding the ``--product-name`` and ``--product-instance`` arguments to a ``--connect-scope`` command
switches to the use of the named network environment. The default environment is a global environment.

Adding the ``--custom-host`` and/or ``--custom-port`` arguments to a ``--connect-scope`` command
overrides the standard IP and port number values. These must match the configuration created when
installing the layer-cake services; **layer-cake-host** and **layer-cake-lan**.

Connecting an environment to a WAN service requires an *access file* created by the use of
the :ref:`layer-cake directory <layer-cake-command-reference-directory>` command. This is then combined
with a ``--connect-scope`` argument using the ``--connect-file`` argument;

.. code::

	$ layer-cake network --connect-scope=GROUP --connect-file=<access-file>

To drop out a section of the network environment, use the ``--connect-disable`` argument;

.. code::

	$ layer-cake network --connect-scope=GROUP --connect-disable

This deletes any existing connection for the associated GROUP, returning it to private operation.

PING
====

    $ layer-cake ping <*service*> [<*group*> [<*home*>]]

Test connectivity from the current host to the specified service, within the specified network environment. The
command will print a short list of attempts to provoke a response and the time it took to succeed in doing so;

.. code::

	$ layer-cake ping testing-response-time
	[LAN] testing-response-time (6 hops)
	+ received ack after 0.006224s
	+ received ack after 0.022727s
	+ received ack after 0.022349s
	+ received ack after 0.022036s
	+ received ack after 0.0224s
	+ received ack after 0.021623s
	+ received ack after 0.021737s
	+ received ack after 0.023134s

The output shows the level at which the service was found and the number of network components the ping
passes through to reach that destination.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **service-name**
     - string
     - *service, name to search for*
   * - **group-name**
     - string
     - *group, lowest level of the network environment*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **ping-count**
     - int
     - *number, override for the number of pings*

.. _layer-cake-command-reference-signup:

SIGNUP
======

    $ layer-cake signup

All networking at the WAN scope requires an account in the **layer-cake-wan**. To create an account use the ``signup``
command. To access and existing account use the ``login`` command.

The command prompts the user for a list of fields. After entry of the final field the entire set is presented
to the cloud. If there are any problems a diagnostic will be printed. Silence is an indication that a new
account has been created. Further cloud commands can be issued without entry of credentials until there is
an extended period of inactivity (5 minutes). The cloud will mark the account as expired and will require a
login to start a new timer.

All communications with the cloud are encrypted and authenticated. At least for an initial period the
information entered is not used, i.e. an email address is required as a unique identity but no email is
currently being sent. Passwords must be at least 12 characters long and must include alphas, digits and
symbols (e.g. +).

.. note::

	The status of **layer-cake-wan** can be found `here :ref:<wan-networking-and-supporting-service>`.

.. _layer-cake-command-reference-login:

LOGIN
=====

    $ layer-cake login

To recover access to an account, use the login command. Enter an email address and the associated
password. There is either an error message or silence indicating that the account is open for further
commands.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **read**
     - bool
     - *flag, read and display the current login*
   * - **login-id**
     - UUID
     - *identity, read and display the specified login*

.. _layer-cake-command-reference-account:

ACCOUNT
=======

    $ layer-cake account

Access information about the current account or modify the account. The default is a full listing of
account details (minus sensitive information), related logins and directories. The ``--show-identities``
argument can be used to tag the significant entities with a UUID that can be used in other commands.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **read**
     - bool
     - *flag, read and display the current account (default)*
   * - **update**
     - bool
     - *flag, modify attributes of the account*
   * - **delete**
     - bool
     - *flag, delete the current account*
   * - **add-login**
     - bool
     - *flag, add a new user to the current account*
   * - **delete-login**
     - bool
     - *flag, delete an existing user from the current account*
   * - **add-directory**
     - bool
     - *flag, add a new directory to the current account*
   * - **delete-directory**
     - bool
     - *flag, delete an existing directory from the current account*
   * - **show-identities**
     - bool
     - *flag, enable the inclusion of UUIDs for each cloud entity*

Without use of the ``--update`` or ``--delete`` arguments, the default operation is a ``--read``.
Update allows for the modification of the account while the delete operation removes the entire
account along with all its logins and directories. There is no undo.

Additional logins can be added and deleted using the ``--add-login`` and ``--delete-login`` arguments.
The login created during account creation remains the owner of the account and the only
identity that can modify the account in this way.

Additional directories can be added and deleted using the ``--add-directory`` and ``--delete-directory`` arguments.
The account owner is the only identity that can modify the account in this way.

Adding the ``--show-identities`` argument (or the ``-si`` shorthand flag) to a read command results in the
inclusion of a UUID for each account entity.

.. _layer-cake-command-reference-directory:

DIRECTORY
=========

    $ layer-cake directory 

Directories may be read (the default), updated or exported. Deletion occurs as an account operation
and can only be performed by the account owner.

Access credentials can be exported from a directory and used to configure networking environments.
Consider the following command;

.. code::

	$ layer-cake directory --directory-id=765666dc-6cc8-473a-9130-bff9cc378061 --export --access-name=station --export-file=station.access

This creates a ``station.access`` file in the current directory. The file is passed to the :ref:`layer-cake network <layer-cake-command-reference-network>`
command to configure a connection from a GROUP, HOST or LAN to the selected directory.

.. code::

	$ layer-cake network --connect-scope=LAN --connect-file=station.access

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **read**
     - bool
     - *folder path, name of the new home*
   * - **update**
     - bool
     - *folder path, external storage of executables*
   * - **export**
     - bool
     - *folder path, external storage of persistent settings*
   * - **directory_id**
     - UUID
     - *folder path, external storage of process activity*
   * - **export file**
     - string
     - *file path, external storage of read-only materials*
   * - **access_name**
     - string
     - *name, external storage of empty-on-start, transient file materials*
   * - **show-identities**
     - bool
     - *flag, enable inclusion of UUIDs*
