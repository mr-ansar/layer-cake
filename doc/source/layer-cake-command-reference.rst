.. _layer-cake-command-reference:

Layer Cake Command Reference
############################

Documentation for the ``ansar`` command-line tool can be found in the following pages. This is the **ansar-connect** implemetation of the
tool that is also provided by `ansar-encode <https://pypi.org/project/ansar-encode>`_ and `ansar-create <https://pypi.org/project/ansar-create>`_.
Refer to the associated documentation for complete information relating to serialization and asynchronous programming, respectively. While this
documentation focuses on networking operations, some material is repeated for convenient browsing.

Definitions, Acronyms And Abbreviations
***************************************

.. list-table::
   :widths: 25 90
   :header-rows: 1

   * - Name
     - Notes
   * - *executable*
     - A loadable image, a file containing machine instructions.
   * - *process*
     - A loaded image, a running instance of an *executable*.
   * - *role*
     - A name unique within a *home*, a context for a *process*.
   * - *group*
     - A name unique within a *home*, a context for one or more *roles*.
   * - *home*
     - A folder, the name of that folder, a collection of *roles* and their associated *processes*.
   * - *encoding*
     - A full **ansar.encode** representation of complex data, using JSON.
   * - *settings*
     - An *encoding*, persistent data loaded by a *process*, tunable operational parameters.
   * - *input*
     - An *encoding*, data passed to a *process* at start time.
   * - *command*
     - Text typed into a command shell, an *executable* name followed by zero or more *words* and *arguments*.
   * - *argument*
     - An element of a *command*, text structured as --<*name*>=<*value*> (double-dash).
   * - *flag*
     - An element of a *command*, short form of an *argument*, -<*initial-letters-of-words*>=<*value*> (single-dash).
   * - *value*
     - A JSON fragment, stripped back alternative to full *encoding*.
   * - *word*
     - An element of a *command*, text not starting with a dash.
   * - *build*
     - A folder containing *executables*, the end of a software tool chain.
   * - *space*
     - An area of disk within a *role* or *home*, refer to ``create``.
   * - *snapshot*
     - A folder containing a copy of *home* folders and files.
   * - *materials*
     - Folders and files.

Breakdown Of Commands
*********************

Composing Collections Of Processes
==================================

* ansar **create** <*home*> *redirects*...
* ansar **add** <*executable*> <*role*> <*home*> *settings*...
* ansar **update** <*role*> <*home*> *settings*...
* ansar **delete** <*role*> <*home*>
* ansar **list** <*role*> <*home*>
* ansar **destroy** <*home*>

Managing Operational Processes
==============================

* ansar **run** <*role*> <*home*>
* ansar **start** <*role*> <*home*>
* ansar **stop** <*group*> <*home*>
* ansar **status** <*role*> <*home*>

Development Automation
======================

* ansar **deploy** <*build*> <*snapshot*> <*home*>
* ansar **snapshot** <*snapshot*> <*home-*>


Network Administration
======================

* ansar **network** <*group*> <*home*>
* ansar **ping** <*service*> <*group*> <*home*>
* ansar **signup**
* ansar **login**
* ansar **account**
* ansar **directory**

General Information
*******************

The ansar tool creates, modifies and deletes a *home*. It implements a set of sub-commands, identifiable as the first *word*
on the command line. Each of these sub-commands accepts further information often including an *executable*, *role* and *home*, as
further *words* on the command line. This positional style of command is concise. There are situations where the approach does
become problematic. For this reason most sub-commands also support the entry of these entities as explicit *arguments*. Ordering
of *arguments* has no significance and skipping an argument does not influence assumptions about the next. The use of both is an
error.

All commands expect an expression of a *home*, whether as a positional word or an argument. If neither of these is present
the command will assume the default ``.ansar-home``.

Searching For Roles
*******************

Several commands (e.g. ``list``, ``status`` and ``set``) operate on one or more *roles*. In these situations the ansar tool uses a
standard set of criteria to resolve a set of matched roles. These are;

.. list-table::
   :widths: 25 90
   :header-rows: 1

   * - Name
     - Notes
   * - role-name
     - *Unique name of a process context, a Python regular expression, or None*.
   * - executable
     - *Name of a file in the home bin, or None*.
   * - invert-search
     - *Resolve the set of roles not matching the criteria*.

These criteria can be applied in different combinations to uncover different subsets of the available roles.
Assuming that there are 5 roles in the specified home, with the names snooze-0, snooze-1, zombie-0, zombie-1
and noop-0;

.. list-table::
   :widths: 20 20 20 40
   :header-rows: 1

   * - role-name
     - executable
     - invert-search
     - Notes
   * - snooze-0
     - None
     - False
     - snooze-0
   * - None
     - None
     - False
     - *all 5 roles*
   * - None
     - snooze
     - False
     - snooze-0, snooze-1
   * - snooze-\\d
     - None
     - False
     - snooze-0, snooze-1
   * - snooze-\\d
     - None
     - True
     - zombie-0, zombie-1, noop-0
   * - [a-z]+?-1
     - None
     - True
     - snooze-0, zombie-0, noop-0

When accessing a single role (e.g. command ``get``) the search is expected to return a list of length 1. In a slight
quirk, this works when the criteria is set to *all* and the home only contains a single role.

Modification Of Live Files
**************************

Commands modifying the contents of a *home* such as ``update`` and ``deploy``, must consider the potential for operational processes
working with those same contents. These commands determine the roles to be affected by their activities and then check for the presence
of associated processes. By default, detection of even a single associated process terminates the command. Passing the ``--force``
argument - before the sub-command - gives the command permission to proceed. Detected processes will be terminated and restarted
after the command is complete.

Composing Collections Of Processes
**********************************

.. _ansar-command-reference-create:

CREATE
======

    $ ansar create [<*home-path*>] [--<*redirect*>=<*path*> …]

Create disk space for the operations of a new composition of processes. The command accepts a *home-path* and zero or
more *folder redirections*. An attempt to create a home that already exists is an error.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **home-path**
     - string
     - *folder path, name of the new home*
   * - **redirect-bin**
     - string
     - *folder path, external storage of executables*
   * - **redirect-settings**
     - string
     - *folder path, external storage of persistent settings*
   * - **redirect-logs**
     - string
     - *folder path, external storage of process activity*
   * - **redirect-resource**
     - string
     - *folder path, external storage of read-only materials*
   * - **redirect-tmp**
     - string
     - *folder path, external storage of empty-on-start, transient file materials*
   * - **redirect-model**
     - string
     - *folder path, external storage of persistent, application file materials*

The ability to redirect storage areas brings several potential benefits. In general it allows for
better management of highly-active and/or bulk storage, such as logs. In the case of ``redirect-bin``
it allows for different variants of the edit-run-debug loop.

Redirections for disk management purposes will often be to shared areas. For this reason the command creates a
unique folder at the specified location. The redirection ``--redirect-logs=/big/fast/disk`` will result in the
creation of the folder ``/big/fast/disk/ansar-logs-<uuid>``, where *uuid*  is a unique identity assigned
to each home. A back-link file called ``.ansar-origin`` is added to the new folder as a record of ownership.
The ``destroy`` command is "redirect aware" and removes all related artefacts.

Redirections to "read-only" storage areas (i.e. ``bin`` and ``resource``) do not cause the creation of unique
folders.

.. _ansar-command-reference-add:

ADD
===

    $ ansar add <*executable*> [<*role-name*> [<*home-path*>]] [--<*name*>=<*value*> …]

Capture the details associated with a new process, to be initiated at some later point. Save that information within the specified
home. The command accepts an *executable*, a *role-name*, a *home-path* and an optional list of *name*\ =\ *value* assignments.
The *executable* must exist within the appropriate home storage area. The *role-name* is optional and defaults to *executable*-0.
The command line assignments are used to initialize the persistent settings for the new process. Refer to the ``update`` command
for further information.

Role names are unique identities for instances of executables. There can only be a single instance of a role name within
a given home. Attempting to add a role that already exists is an error.

The command also accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *role name, explicit name or template*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **start**
     - integer
     - *starting index for the internal iteration, default = 0*
   * - **step**
     - integer
     - *amount to increment on every internal iteration, default = 1*
   * - **count**
     - integer
     - *number of internal iterations, default = 1*
   * - **settings-file**
     - string
     - *file path, JSON encoding, definition of role ettings*
   * - **input-file**
     - string
     - *file path, JSON encoding, definition of role input*

Other arguments are forwarded to a construction instance of the named executable as *name*\ =\ *value* assignments.

Internally, the command performs a loop controlled by the ``start``, ``step`` and ``count`` values. On each
iteration the command uses the *role-name* as a template and performs a substitution, e.g. given the command
``ansar add server`` the default *role-name* (i.e. ``{executable}-{number}``) becomes ``server-0``. The same
substitution is also performed on the value part of every command argument. A new role is added on each iteration
of the loop.

Every new role is initialized with default settings. The ``settings-file`` argument can be used to override those
initial values. The input passed to an operational instance of a role is also initialized with a default value.
The ``input-file`` argument can be used to override that initial value.

To iniitalize *properties* such as ``retry`` and ``storage``, refer to the ``get`` and ``set`` commands.

UPDATE
======

    $ ansar [--force] update [<*role-name*> [<*home-path*>]] [--<*name*>=<*value*> …]

Update the details associated with an existing role. Save that information within the specified home. The command
accepts a *role-name*, a *home-path* and a list of *name*\ =\ *value* assignments. Attempting to update a role that
doesn't exist is an error.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *explicit name, search expression or None*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **executable**
     - string
     - *name of an executable within bin*
   * - **invert-search**
     - bool
     - *apply to roles not matching the search criteria*

The standard `search facility <#searching-for-roles>`_ is available. Use of `force <#modification-of-live-files>`_
may be required.

All -\ -*name*\ =\ *value* settings are forwarded to a construction instance of the executable. The *name* is used
to assign the *value* to the appropriate member of the settings object retained on behalf of each role. Values
are presented as JSON *fragments* - where an appropriate JSON encoding would include quotes, these are supplied by
ansar and should not appear on the command line. Where ``domain`` is a string a proper argument looks like;

.. code::

   ansar update server-0 --domain=company.co.country

Value strings can contain spaces and newlines, but complex encodings become increasingly difficult to pass
safely (i.e quote successfully) on the command-line. Consider the ``settings`` command.

To modify *properties* such as ``retry`` and ``storage``, refer to the ``get`` and ``set`` commands.

DELETE
======

    $ ansar [--force] delete [<*role-name*> [<*home-path*>]]

Delete all the files and folders associated with the *role*. This includes materials created by the ansar command
and those materials created by activities of the operational process. The command also follows any *redirects* specified
at home creation time, clearing and removing folders at external locations. Attempting to delete a role that
doesn't exist is an error.

The command also accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *role name, explicit name or search expression*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **executable**
     - string
     - *name of an executable within bin, search criteria*
   * - **invert-search**
     - bool
     - *apply to roles not matching the search criteria*

The standard `search facility <#searching-for-roles>`_ is available. Use of `force <#modification-of-live-files>`_
may be required.

LIST
====

    $ ansar list [<*role-name*> [<*home-path*>]]

List the *roles* currently defined in the specified *home*. The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *role name, explicit name or search expression*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **executable**
     - string
     - *name of an executable within bin, search criteria*
   * - **invert-search**
     - bool
     - *list roles not matching the search criteria*
   * - **long-listing**
     - bool
     - *enable a more detailed output*
   * - **group**
     - bool
     - *include group roles within the output*
   * - **all-roles**
     - bool
     - *include sub-roles within the output*

The standard `search facility <#searching-for-roles>`_ is available. The simplest form of the command produces a basic
list of the roles within the default home;

.. code::

   $ ansar list
   server-0
   test-client-0
   $

Passing the ``--long-listing`` argument produces additional information including the *executable* that
performs the *role* and some disk usage statistics (*folders*/*files*/*bytes*);

.. code::

   $ ansar list -ll
   factorial-0              factorial (1/0/0)
   snooze-0                 snooze (1/0/0)
   zombie-0                 zombie (1/3/3987)
   totals                   (4/3/3987)
   $

The ``-ll`` *flag* shortform was used for the ``long-listing`` *argument*.

DESTROY
=======

    $ ansar [--force] delete [<*home-path*>]

Destroy all the files and folders associated with the *home*. This includes materials created by the ansar command
and those materials created by activities of the operational processes. The destroy command also follows any
*redirects* specified at creation time, clearing and removing folders at external locations. Attempting to destroy
a home that doesn't exist is an error.

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

Use of `force <#modification-of-live-files>`_ may be required.

Managing Operational Processes
******************************

.. _ansar-command-reference-run:

RUN
===

    $ ansar [--debug-level=<*level*>] [--force] run [<*role-name*> ..]

Run instances of the specified *roles*, from the effective *home*, as a *group* of processes. Direct the resulting
processes to operate within the confines of the disk spaces managed by the *home*. Route the logs from all the processes
to ``stderr`` and wait for completion of every process or a user intervention, i.e. a control-c. A control-c initiates
a termination protocol with every process still active. The run completes when every process has terminated. Lastly,
output a summary table including a list of the values returned by each process. Attempting to run a role that doesn't
exist is an error.

An instance of the ``ansar-group`` process is added into every run as a supervisor process. All *role* processes are
children of the group process. As a supervisor its duties include managing restarts of *roles* as proscribed in its
settings. Group processes are allocated their own space within the *home*, i.e. a group named ``backend`` will appear
in the *home* as the ``group.backend`` *role*. Ansar commands can be used to administer group *roles* in the same manner
as any other *role*, e.g. ``ansar log group.default`` will display any recent activity within the associated ``ansar-group``
process and ``ansar settings group.default`` can be used to view and update its configuration.

An empty list of *roles* implicitly matches all the *roles* within the *home*.

Without a ``--group-name`` argument the *group* defaults to the ``default`` name.

Without a ``--home-path`` argument the *home* defaults to ``.ansar-home`` in the current folder.

The command also accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *role name, explicit name or search expression*
   * - **group-name**
     - string
     - *role name, name of an ansar-group role without the group prefix*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **executable**
     - string
     - *name of an executable within bin, search criteria*
   * - **invert-search**
     - bool
     - *match those roles not matching the search criteria*
   * - **code-path**
     - string
     - *folder path, top of a source tree*
   * - **test-run**
     - bool
     - *enable capture of test reports and output of a test suite*
   * - **test-analyzer**
     - string
     - *name of an executable, called at end-of-run, passed test suite*
   * - **debug-level**
     - enum
     - *enumeration of a common log level, lower level logs discarded*
   * - **forwarding**
     - string
     - *role name, stdin forwarded to the named role*

The standard `search facility <#searching-for-roles>`_ is available. Use of `force <#modification-of-live-files>`_
may be required.

The presence of the ``test-run``  argument enables additional behaviour. The command assumes that one or more
of the processes will produce test information. The information is collated and either passed to an execution
of ``test-analyzer`` or presented on ``stdout``.

A ``code-path`` is assumed to be a folder of associated source files. The folder is searched recursively for any
python modules. The information gathered is used to augment the module information available in any test reports
produced by execution of *roles*.

By default logging is disabled. Passing a ``debug-level`` argument enables the output of those logs marked
with the specified level or higher. Log output appears on ``stderr``.

Input presented to the run command on stdin can be directed to one of the matched roles. The ``forwarding``
argument names the receiving role.

.. _ansar-command-reference-start:

START
=====

    $ ansar [--force] start [<*role-name*> ..]

Start instances of the specified *roles*, from the given *home*, as a *group* of processes. Do not wait for
completion - return control back to the shell immediately. Direct the resulting processes to operate within
the confines of the disk spaces managed by the *home*. Also, direct the processes to send their logs into the
designated FIFO storage area within the *home*. Attempting to start a role that doesn't exist is an error.

An instance of the ``ansar-group`` process is added into every start as a supervisor process. All *role* processes are
children of the group process. As a supervisor its duties include managing restarts of *roles* as proscribed in its
settings. Group processes are allocated their own space within the *home*, i.e. a group named ``backend`` will appear
in the *home* as the ``group.backend`` *role*. Ansar commands can be used to administer group *roles* in the same manner
as any other *role*, e.g. ``ansar log group.default`` will display any recent activity within the associated ``ansar-group``
process and ``ansar settings group.default`` can be used to view and update its configuration.

An empty list of *roles* implicitly matches all the *roles* within the *home*.

Without a ``--group-name`` argument the *group* defaults to the ``default`` name.

Without a ``--home-path`` argument the *home* defaults to ``.ansar-home`` in the current folder.

The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *role name, explicit name or search expression*
   * - **group-name**
     - string
     - *role name, name of an ansar-group role without the group prefix*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **executable**
     - string
     - *name of an executable within bin, search criteria*
   * - **invert-search**
     - bool
     - *match those roles not matching the search criteria*

The standard `search facility <#searching-for-roles>`_ is available. Use of `force <#modification-of-live-files>`_
may be required.

.. _ansar-command-reference-stop:

STOP
====

    $ ansar [--force] stop [<*group*> ..]

Stop those processes associated with the specified *groups*, in the effective *home*. An empty list of *groups* implicitly
matches all the *groups* within the *home*. Without a ``--home-path`` argument the *home* defaults to ``.ansar-home`` in
the current folder. 

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

.. _ansar-command-reference-status:

STATUS
======

    $ ansar status [<*role-name*> [<*home-path*>]]

List the *roles* currently active in the specified *home*. The command accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **role-name**
     - string
     - *role name, explicit name or search expression*
   * - **home-path**
     - string
     - *folder path, name of the home*
   * - **executable**
     - string
     - *name of an executable within bin, search criteria*
   * - **invert-search**
     - bool
     - *list roles not matching the search criteria*
   * - **long-listing**
     - bool
     - *enable a more detailed output*
   * - **group**
     - bool
     - *include group roles within the output*
   * - **all-roles**
     - bool
     - *include sub-roles within the output*

The standard `search facility <#searching-for-roles>`_ is available. The simplest form of the command produces a
basic list of the active roles within the default home;

.. code::

   $ ansar status
   server-0
   $

Passing the ``--long-listing`` argument produces additional information including the process ID and
elapsed runtime of each process;

.. code::

   $ ansar status -ll
   zombie-0                 <1292610> 5.2s

HISTORY
=======

    $ ansar history <*role-name*> [<*home-path*>]

Present the recent process activity associated with the specified *role*, in the given *home*. A *role-name*
is required. The command accepts the following explicit arguments;

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

   $ ansar history zombie-0
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

   $ ansar history zombie-0 -ll
   2023-06-08T00:23:48.905221 ... 2021-10-21T06:44:58.965063 (6h21m) Ack
   2021-10-21T06:45:00.068706 ... 2021-10-21T06:53:59.069315 (8m59.0s) Ack
   2021-10-21T06:54:04.938309 ... 2021-10-21T17:45:38.023162 (10h51m) Ack
   2021-10-21T22:34:13.239548 ... 2021-10-21T22:40:08.586523 (5m55.3s) Ack
   2021-10-21T22:40:17.162771 ... ?

The question mark ``?`` denotes a process that has not yet returned.

RETURNED
========

    $ ansar returned <*role-name*> [<*home-path*>]

Output the value returned by the process executing on behalf of the *role*, in the specified *home*. A
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
   * - **timeout**
     - float
     - *number of seconds to wait for the completion of an active role*
   * - **start**
     - integer
     - *index into the FIFO of history records*

The simplest form of the command outputs the JSON encoding of the latest return value;

.. code::

   $ ansar returned zombie-0
   {
       "value": [
           "ansar.create.lifecycle.Ack",
           {},
           []
       ]
   }
   $

Where the selected role is also active, the command will wait until the associated process completes
and returns a value. Passing a timeout argument ensures that the command does not wait forever.

.. _ansar-command-reference-log:

LOG
===

    $ ansar log <role-name> [<home-path>] [--<beginning>=value] [--<ending>=<value>]

Output a sequence of logs generated by the *role*, in the specified *home*. The sequence has a beginning
and an ending point. Both are optional and default to 5 minutes ago and ``None``, respectively. The absence
of an ending (i.e. ``None``) implies “everything from the given starting point”. An attempt to access the
logs of a non-existent role is an error.

The beginning can be expressed as;

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
   * - **clock**
     - bool
     - *enable entry and output of local times*
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
     - time span
     - *a negative, relative time value*
   * - **to**
     - string
     - *ISO format time, either local or UTC depending on "clock"*
   * - **span**
     - time span
     - *a positive, relative time value*
   * - **count**
     - integer
     - *number of records to list*

Simple use looks like;

.. code::

   $ ansar log zombie-0
   2020-11-07T15:52:25.745 + <00000008>lock_and_hold - Created by <00000001>
   2020-11-07T15:52:25.745 > <00000008>lock_and_hold - Sent Ready to <00000001>
   2020-11-07T15:52:25.746 + <00000009>start_vector - Created by <00000001>
   2020-11-07T15:52:25.746 ~ <00000009>start_vector - Executable "/home/dennis/some/project/dist/zombie" as process (1216338)
   2020-11-07T15:52:25.746 ~ <00000009>start_vector - Working folder "/"
   2020-11-07T15:52:25.746 ~ <00000009>start_vector - Running object "__main__.zombie"
   2020-11-07T15:52:25.746 ~ <00000009>start_vector - Class threads (1) "retries" (1)
   2020-11-07T15:52:25.746 + <0000000a>zombie - Created by <00000009>
   2020-11-07T15:52:25.746 ^ <0000000a>zombie - Do nothing until interrupted
   ..

For further information on the logging format and operational considerations refer to
the `ansar-create <https://pypi.org/project/ansar-create>`_ documentation. Other uses of the ``log`` command
include (output omitted);

.. code::

   $ ansar log zombie-0 --clock
   $ ansar log zombie-0 --from_=2020-11-07T16:00:44.565       # note that the trailing underscore is sadly required
   $ ansar log zombie-0 --last=WEEK
   $ ansar log zombie-0 --start=0
   $ ansar log zombie-0 --back=7d10s
   $ ansar log zombie-0 --to=2020-11-07T17:00
   $ ansar log zombie-0 --span=30s
   $ ansar log zombie-0 --count=40
   $ ansar log zombie-0 --start=1 --count=10

Use of the ``clock`` argument causes the output of local time values. To distinguish these from UTC times the ``T`` separator
between the date and time fields is folded to lowercase. Input time values such as ``from_`` are also assumed to be in
UTC format. Use of the ``clock`` argument in a distributed working environment is generally perilous.

FOLDER
======

    $ ansar folder <*space*> <*role-name*> [<*home-path*>]

Output a folder path as selected by the *space* and *role*, within the specified *home*. The defined spaces are those managed
within a home and potentially *redirected* (refer to the ``create`` command); bin, settings, logs, resource, tmp and model.
Both the *space* and *role* are required.

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

The command is a support feature as the exact location of materials can become detailed;

.. code::

   $ ansar folder logs zombie-0
   /tmp/ansar-logs-8be745af-9813-413f-aa16-dd4b0c975ccd/zombie-0

For some spaces the output folder is the same for all roles, e.g. bin. For the resource space the folder is the same for
all roles configured with a common executable. To sidestep the many permutations of this scenario, a role is always required.

Development Automation
**********************

.. _ansar-command-reference-deploy:

DEPLOY
======

    $ ansar [--force] deploy [<*build-path*> [<*snapshot-path*> [<*home-path*>]]]

Perform an optimal update of the *home*, from external *build* and *snapshot* areas. The command examines source and destination areas and computes
a minimum delta before copying executables and operational files into the appropriate areas of the home. It also evaluates those roles affected
by the imminent changes. Any processes associated with those roles are optionally terminated before copy activities begin and restarted after they are
completed.

The build-path is assumed to be a folder containing executable files. It is at the end of a software build chain. Executables are copied from this
build area into the home bin. Each ``deploy`` command copies those executables determined to be new or modified, as compared to the contents of
the home bin.

The snapshot path is an external image of all the persistent materials - the files and folder structures - supporting the operation of the
home (refer to the ``snapshot`` command for the internal layout of the external image). This is a *global state* of the home, a snapshot of the
settings, input and application files that underpin the features and behaviours of the collection of processes, associated with that home.

The pair of commands - ``snapshot`` and ``deploy`` - can be used to *create and maintain* an external image of an operational home. This meshes
perfectly with the requirements of an efficient edit-run-debug loop. Executables and operational files (in the external image) can be modified
in a development area and transferred into the home with a single command. All of this is carried out in a "least I/O possible" way and with
automated management of associated processes.

Ideally, the external image exists in a repo alongside the related Python modules. The repo then contains all the code *and* all the file-based
materials relating to a multi-process configuration. In this scenario an exact replica of a multi-process solution can be instantiated in a few
minutes, with a clone command and a few make targets. Large files such as databases cannot be included in code repos and will need specific
handling. Small text files such as the JSON encodings used for settings and input are perfectly suited to a repo existence.

It also becomes possible to create and maintain multiple external images, e.g. development, QA and production. These can be deployed to
independent homes or used to switch a single home between entirely different modes of operation.

The command also accepts the following explicit arguments;

.. list-table::
   :widths: 25 15 75
   :header-rows: 1

   * - Name
     - Type
     - Notes
   * - **build-path**
     - string
     - *folder path to executable files*
   * - **snapshot-path**
     - string
     - *folder path, external image*
   * - **home-path**
     - string
     - *folder path, name of the home*

The transfer of materials from the build path into the home is non-destructive, whereas the transfer from the snapshot path into the home is
destructive. In a "destructive" pass, folders and files not present in the source, are clipped off in the destination. This means that deployment
can occur from multiple build paths (i.e. repos) into a common home, but only a single storage path can be the source of operational files.

.. _ansar-command-reference-snapshot:

SNAPSHOT
========

    $ ansar [--force] snapshot <*snapshot-path*> [<*home-path*>]

Perform an optimal update of the *snapshot*, from the latest materials in the *home*. If the ``snapshot-path`` does not exist, the folder is
created. This is a "sync" of an external image with the current "global state" of a home. The command examines source and destination areas and
computes a minimum delta before copying operational files out into the appropriate disk areas.

Given a command like ``$ ansar snapshot selfie``, the result looks like;

.. code:: text

   selfie
   selfie/settings-by-role
   selfie/settings-by-role/snooze-0.json
   selfie/resource-by-executable
   selfie/resource-by-executable/snooze
   selfie/resource-by-executable/zombie
   selfie/resource-by-executable/factorial
   selfie/input-by-role
   selfie/input-by-role/factorial-0.json
   selfie/model-by-role
   selfie/model-by-role/factorial-0
   selfie/model-by-role/snooze-0
   selfie/model-by-role/zombie-0

Where ``snooze`` is an executable with associated *settings*, and ``factorial`` is an executable with associated *input*. Instances of
these executables (i.e. *roles*) cause the creation of those materials under the names ``selfie/settings-by-role/snooze-0.json`` and
``selfie/input-by-role/factorial-0.json``, respectively. The folder names immediately under ``selfie`` are related to different areas in
a home and also describe the structuring of those folders. Materials under the ``resource-by-executable`` are arranged according
to an *executable*, e.g. ``resource-by-executable/snooze``, whereas materials under ``model-by-role`` are arranged by *role*,
e.g. ``model-by-role/snooze-0``. This is a simple reflection of the fact that resources are shared by processes started from a common
executable, while application files under ``model`` are created and maintained by each instance of a process (i.e. a *role*) whatever the
associated executable might be.

The contents of the ``selfie`` folder and folders at the next level down, are under the control of ``snapshot``. Folders such
as ``selfie/model-by-role/snooze-0`` should only be removed as a consequence of an ``ansar delete snooze-0`` command and a
subsequent ``ansar snapshot selfie``. The latter will clip off the redundant folder under ``model-by-role``. Folders and files below
the level of e.g. ``selfie/model-by-role/snooze-0`` are "wild west" as far as ansar is concerned. The specific contents are
executable-dependent.

.. list-table::
   :widths: 25 90
   :header-rows: 1

   * - Name
     - Contents
   * - settings-by-role
     - *.json file per role, persistent application configuration*
   * - setting-value-by-role
     - *JSON fragment, folder per-role and per-member, persistent application configuration*
   * - resource-by-executable
     - *open range folder per-executable, executable-dependent folders and files*
   * - input-by-role
     - *.json file per role, process input*
   * - model-by-role
     - *open range folder per-role, executable-dependent folders and files*

For convenience of data entry, the ``setting-value-by-role`` folder can be created and populated manually. Values of the individual
members of a settings object can be entered into a file, under the appropriate folder structure and this will override the
global settings in ``settings-by-value``. The arrangement looks like;

.. code::

   selfie
   selfie/setting-value-by-role
   selfie/setting-value-by-role/snooze-0
   selfie/setting-value-by-role/snooze-0/seconds

Where the ``seconds`` file contains a JSON fragment appropriate to the member type - in this case a float like ``15.0``. JSON
fragments are simpler than a full JSON encoding and do not include the standard "packaging", e.g. ``{"value": ...}``. Quotes are also
added automatically around JSON types that require them, e,g. strings. Refer to ``update`` for more details on JSON fragments.

Network Administration
**********************

.. _ansar-command-reference-network:

NETWORK
=======

    $ ansar network [<*group-name*> [<*home-path*>]]

View the network environment for the specified group within the specified home. Adding the ``--connect-scope`` argument also
provides for configuration of the specified environment, where connections are made from one scope to another scope, always
in an upward direction. Configuration is persistent and may affect the operation of other groups that share a common
ancestor, e.g. HOST, LAN or WAN.

The default command lists the network environment for the ``default`` group in the ``.ansar-home`` folder;

.. code::

	$ ansar network
	+ GROUP 127.0.0.1:45489

The simplest configuration command connects the same group to the installed **ansar-host** service;

.. code::

	$ ansar network --connect-scope=GROUP --to-scope=HOST
	$ ansar network
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
     - *file path, address and credentials for connection to ansar-wan*
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
installing the ansar services; **ansar-host** and **ansar-lan**.

Connecting an environment to a WAN service requires an *access file* created by the use of
the :ref:`ansar directory <ansar-command-reference-directory>` command. This is then combined
with a ``--connect-scope`` argument using the ``--connect-file`` argument;

.. code::

	$ ansar network --connect-scope=GROUP --connect-file=<access-file>

To drop out a section of the network environment, use the ``--connect-disable`` argument;

.. code::

	$ ansar network --connect-scope=GROUP --connect-disable

This deletes any existing connection for the associated GROUP, returning it to private operation.

PING
====

    $ ansar ping <*service*> [<*group*> [<*home*>]]

Test connectivity from the current host to the specified service, within the specified network environment. The
command will print a short list of attempts to provoke a response and the time it took to succeed in doing so;

.. code::

	$ ansar ping testing-response-time
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

.. _ansar-command-reference-signup:

SIGNUP
======

    $ ansar signup

All networking at the WAN scope requires an account in the **ansar-wan**. To create an account use the ``signup``
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

	The status of **ansar-wan** can be found `here :ref:<wan-networking-and-supporting-service>`.

.. _ansar-command-reference-login:

LOGIN
=====

    $ ansar login

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

.. _ansar-command-reference-account:

ACCOUNT
=======

    $ ansar account

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

.. _ansar-command-reference-directory:

DIRECTORY
=========

    $ ansar directory 

Directories may be read (the default), updated or exported. Deletion occurs as an account operation
and can only be performed by the account owner.

Access credentials can be exported from a directory and used to configure networking environments.
Consider the following command;

.. code::

	$ ansar directory --directory-id=765666dc-6cc8-473a-9130-bff9cc378061 --export --access-name=station --export-file=station.access

This creates a ``station.access`` file in the current directory. The file is passed to the :ref:`ansar network <ansar-command-reference-network>`
command to configure a connection from a GROUP, HOST or LAN to the selected directory.

.. code::

	$ ansar network --connect-scope=LAN --connect-file=station.access

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
