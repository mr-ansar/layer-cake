.. layer-cake documentation master file, created by
   sphinx-quickstart on Tue April 18 16:07:56 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

##########
layer-cake
##########

The **layer-cake** library is for anyone developing software that involves multithreading,
multiprocessing or multihosting, usually with the goal of achieving concurrency. Along the way,
it manages to pull off some effective network messaging too. If you are trying to improve the
throughput of a request processing system, or just maintain responsiveness in complex scenarios,
this library is intended for you.

A few highlights include;

* code clarity in a notoriously difficult problem domain,
* consistent model for multithreading, multiprocessing and multihosting,
* trivial changes to switch between the different concurrency mechanisms,
* support for implementation of load sensitive network services,
* extensive support for low stress multihosting.

Installation
************

**layer-cake** can be installed from PyPI using *pip*;

.. code::

	$ cd <new-folder>
	$ python3 -m venv .env
	$ source .env/bin/activate
	$ pip3 install layer-cake

Documentation
*************

The goal of this documentation is to demonstrate the use of the layer cake library to deliver complex examples
of concurrency. It will show how a few pages of concise Python (100 lines over 4 files) can deliver a complete
example of a website backend that operates seamlessly across threads, processes and hosts.

Externally the software offers a standard HTTP interface, while internally it runs a fully asynchronous,
event-driven execution environment. Demonstrations include;

* creation of a pool of request threads with a single call,
* load distribution of requests across the pool,
* detection of periods of heavy loading and appropriate client feedback,
* switching to a pool of request processes with the addition of a single argument,
* switching to a pool of request hosts with around 10 lines of additional code.

The material is arranged as a series of guides. Some background implementation details are covered where this
may explain certain behaviours. A testing client, capable of replicating the workload of large
numbers of clients is provided at the end.

.. toctree::
   :maxdepth: 1

   downloading-the-demonstrations
   concurrency-with-multithreading
   switching-to-multiprocessing
   distribution-with-multihosting
   simulating-http-clients
   layer-cake-command-reference
   layer-cake-type-reference
   folders-and-files
   design-and-implementation
   classes-and-functions

.. only: html

* :ref:`genindex`

Author
******

The **layer-cake** library was developed by Scott Woods (scott.18.ansar@gmail.com). The library has
evolved under the influence of several large projects over many years. It recently moved from C++ to
Python and even more recently, changed name from **ansar-connect** to **layer-cake**. This is a reflection
of significant differences, mostly around the integration with Python type hints.

License
*******

The **layer-cake** library is released under the `MIT License <https://opensource.org/licenses/MIT>`_.
