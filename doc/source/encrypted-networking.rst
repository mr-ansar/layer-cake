.. _encrypted-networking:

Encrypted Networking
********************

Encryption is built into the **layer-cake** library. To activate encryption there is a simple boolean
flag on both the :func:`~.listen` and the :func:`~.connect` functions;

.. code:: python

	import layer_cake as lc

    lc.listen(self, requested_ipp, encrypted=False)
	..
	..
    lc.connect(self, requested_ipp, encrypted=False)
	..
	..

For networking to succeed the values assigned at each end must match; either they are both
``True`` or they are both ``False``. The default is ``False``.

Encryption is based around Curve25519, high-speed, elliptic curve cryptography. There is an initial
Diffie-Hellman style exchange of public keys in cleartext, after which all data frames passing
across the network are encrypted. All key creation and runtime encryption/decryption is performed
by the `Salt <https://nacl.cr.yp.to/>`_ library.

All encryption-related communications is transparent to the application process, including the
initial handshaking.

Encrypted Publish-Subscribe Networking
======================================

Connections are initiated as a consequence of calls to the :func:`~.publish` and the :func:`~.subscribe`
functions. Encryption of these connections is controlled by the ``encrypted`` parameter that can be
passed to :func:`~.publish`;

.. code:: python

	import layer_cake as lc

    lc.publish(self, service_name, encrypted=True)
	..

There is no matching parameter on the call to :func:`~.subscribe`, as the value registered by
the publisher is propagated through to the pubsub connection machinery, i.e. it is set
automatically.

Encrypted Directory Operation
=============================

Connections are created and maintained as a part of directory operation. A directory is either
encrypted or it is not. All processes operating over an encrypted directory must be configured
accordingly. Partial encryption, e.g. only those connections to the ``lan-cake``, is not
supported.

To enable directory encryption within the different processes, use the following process arguments;

+-----------------------+-------------------------+----------------------------------------------+
| Process               | Argument                | Notes                                        |
+=======================+=========================+==============================================+
| ``lan-cake``          | ``encrypted-directory`` | During installaiton of the component.        |
+-----------------------+-------------------------+----------------------------------------------+
| ``host-cake``         | ``encrypted-directory`` | During installaiton of the component.        |
+-----------------------+-------------------------+----------------------------------------------+
| ``group-cake``        | ``encrypted-directory`` | During installaiton of the component.        |
+-----------------------+-------------------------+----------------------------------------------+
| *application process* | ``encrypted-process``   | 1) Automatic within a *composite process*.   |
|                       |                         | 2) On the process command line.              |
+-----------------------+-------------------------+----------------------------------------------+

Examples are provided below;

.. code-block:: console

	$ lan-cake --directory-at-lan='{"host": "192.168.1.176", "port": 54196}' --encrypted-directory
	$ host-cake -debug-level=DEBUG --encrypted-directory

	$ layer-cake create
	$ layer-cake add lan-cake
	$ layer-cake update lan-cake --directory-at-lan='{"host": "192.168.1.176", "port": 54197}'
	$ layer-cake update lan-cake --encrypted-directory
	$ layer-cake start
	$

To enable encryption of application processes use;

.. code-block:: console

	$ python3 test_worker_10.py --encrypted-process

Lastly, to enable encryption of a *composite process*;

.. code-block:: console

	$ layer-cake create --encrypted-directory
	$ layer-cake add test_server_10.py server
	$ layer-cake add test_worker_10.py worker --role-count=8
	$ layer-cake run --debug-level=DEBUG
	..
	16:42:26.031 ~ <0000000f>ListenConnect - Listening (encrypted) on "127.0.0.1:37065", ...
	..
	..
	16:42:26.087 ~ <0000000f>ListenConnect - Connected (encrypted) to "127.0.0.1:37065", ...

Security And Availability Of Directory Services
===============================================

Encryption of network connections brings security of data that is in-flight, at the cost of
additional CPU cycles and development and support difficulties. An obvious need for encryption
might be where LAN messaging is associated with sensitive business information, especially in
the presence of wireless networking. It seems less applicable to localhost messaging
(e.g. a *composite process*) or messaging over a dedicated, wired network segment. Legal
requirements such as the GDPR would have all in-flight data encrypted.

Layer-cake supports encrypted and unencrypted directory operation. It is reasonably simple to
reconfigure a directory to be one or the other, but even simpler to maintain dual directories.
At each point of component installation (i.e. ``group-cake``, ``host-cake`` and ``lan-cake``)
there are two components added. The second is configured to run on a port beside the first
and for encrypted operation;

.. code-block:: console

	$ layer-cake create
	$ layer-cake add lan-cake lan-cake
	$ layer-cake add lan-cake lan-cake-encrypted
	$ layer-cake update lan-cake --directory-at-lan='{"host": "192.168.1.195", "port": 54195}'
	$ layer-cake update lan-cake-encrypted  --directory-at-lan='{"host": "192.168.1.195", "port": 54196}'
	$ layer-cake update lan-cake-encrypted --encrypted-directory
	$ layer-cake start

Default behaviour of **layer-cake** processes will result in connection to the first, unencrypted
directory. This might be for convenience of development work. Production deployments would be
configured to run on the second directory.

For reasons such as security, reliability and performance, there may be benefit in a directory
for the exclusive use of a single solution. The resource footprint of directory components is low
(i.e. CPU cycles, memory peaks) and there is no disk usage other than logging. All **layer-cake**
logging is self-maintaining and capped at around 2Gb per role (i.e. a process within a *composite
process*). Directory components are *not* involved in messaging between application processes, in
the manner of a message broker.
