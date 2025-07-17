.. _folders-and-files:

Folders And Files
#################

This section takes just a few minutes to cover the application persistence available through the :class:`~.Folder`
and :class:`~.file_object.File` types, in the **layer-cake** library.

Registering Application Types
=============================

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
A full description of the type system can be found :ref:`here<layer-cake-type-reference>`.

.. note::

	Once registered with **layer-cake**, a type is available at all those points encodings are
	used. This includes file I/O, networking messaging and process integration. The latter refers to
	the arguments passed on a command-line and the encoding placed on ``stdout``.

Write An Object To A File
=========================

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
=============================

Reading an object from file storage is also carried out using the :class:`~.file_object.File` class.
In fact, we can re-use the same instance from the previous sample:

.. code-block:: python

   d = f.recover()

This results in assignment of a fully formed instance of the ``list[list[float]]`` type, to the ``d``
variable. Details like the filename and expected object type were retained in the ``f`` variable and
re-applied here.

A Few File Details
==================

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
==========================

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
=============================

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
=============================

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
    spool = lc.Folder('spool', te=Job, re='^[-0-9a-fA-F]{27}$')

.. note::

    The ``te`` parameter is optional for the :class:`~.Folder` class, unlike for
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
==============================

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

    spool = lc.Folder('spool', te=Job, re='^[-0-9a-fA-F]{27}$', keys_names=kn)

The `keys_names` parameter delivers a pair of functions to the :class:`~.Folder` object.
These two functions are used internally during the execution of several :class:`~.Folder`
methods, to calculate a key value and a filename.

When the :meth:`~.Folder.recover` method opens a file and loads the contents, this results in an instance
of the ``te``. The method then calls the first function passing the freshly loaded object. The function
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
====================

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
