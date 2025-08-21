.. _downloading-the-demonstrations:

Downloading The Demonstrations
##############################

All demonstration materials can be downloaded with the following command;

.. code-block:: console

	$ git clone https://github.com/mr-ansar/layer-cake-demos.git

There are three demo sub-folders within the git repo, one for each of the concurrency techniques presented, plus a folder
for a testing client. Each of the concurrency folders contains a small set of files with names starting with ``test_server``,
``test_function`` and ``test_worker``. The server file is the main module and the other files support the main module. All
of these files have a numeric suffix (e.g. ``test_server_1.py``) marking their position in the series of implementations.

After cloning, a virtual environment is needed;

.. code-block:: console

	$ cd layer-cake-demos
	$ python3 -m venv .env
	$ source .env/bin/activate
	$ pip3 install layer-cake

To begin the multithreading demos and verify the environment, enter the following commands (logs appearing in this document
have been reduced to fit);

.. code-block:: console

	$ cd multithreading
	$ python3 test_server_1.py --debug-level=DEBUG
	[01166720] 06:47:54.667 + <0000000e>ListenConnect - Created by <00000001>
	[01166720] 06:47:54.667 < <0000000e>ListenConnect - Received Start from …
	…
	[01166720] 06:47:54.668 < <00000012>server - Received Listening …

A control-c terminates the server. Omitting the ``--debug-level`` results in silent running.
