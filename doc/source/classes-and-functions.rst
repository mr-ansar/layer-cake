.. _classes-and-functions:

Classes And Functions
#####################

Reference information for the significant classes, methods and functions in the
library, appears here.

Listening And Connecting
************************

.. currentmodule:: layer_cake.listen_connect

.. autoclass:: EndOfTransport()
.. autoclass:: ListenForStream
.. autoclass:: ConnectStream
.. autoclass:: Listening
.. autoclass:: Connected
.. autoclass:: Accepted
.. autoclass:: Close
.. autoclass:: Closed
.. autoclass:: NotListening
.. autoclass:: NotConnected

.. autofunction:: connect
.. autofunction:: listen
.. autofunction:: stop_listening

.. currentmodule:: layer_cake.ip_networking

.. autoclass:: HostPort

Publish And Subscribe
*********************

.. currentmodule:: layer_cake.process_directory

.. autofunction:: publish
.. autofunction:: subscribe
.. autofunction:: clear_published
.. autofunction:: clear_subscribed

.. currentmodule:: layer_cake.object_directory

.. autoclass:: Published
.. autoclass:: Subscribed
.. autoclass:: Available
.. autoclass:: Delivered
.. autoclass:: Dropped
.. autoclass:: NotPublished
.. autoclass:: NotSubscribed
.. autoclass:: PublishedCleared
.. autoclass:: SubscribedCleared

Application Startup
*******************

.. currentmodule:: layer_cake.object_startup

.. autofunction:: create

HTTP Integration
****************

.. currentmodule:: layer_cake.http

.. autoclass:: HttpRequest
.. autoclass:: HttpResponse

Message And Registration
************************

.. currentmodule:: layer_cake.message_memory

.. autofunction:: bind_message

.. currentmodule:: layer_cake.bind_type

.. autofunction:: bind
.. autofunction:: bind_point
.. autofunction:: bind_routine
.. autofunction:: bind_stateless
.. autofunction:: bind_statemachine

.. currentmodule:: layer_cake.command_line

.. autoclass:: ScopeOfDirectory
.. autoclass:: ProcessOrigin

.. currentmodule:: layer_cake.virtual_runtime

.. autoclass:: USER_LOG
.. autoclass:: USER_TAG

.. currentmodule:: layer_cake.point_runtime

.. autoclass:: Start
.. autoclass:: Returned
.. autoclass:: Stop
.. autoclass:: Pause
.. autoclass:: Resume
.. autoclass:: Ready
.. autoclass:: NotReady
.. autoclass:: Ping
.. autoclass:: Enquiry
.. autoclass:: Discover
.. autoclass:: Inspect
.. autoclass:: Ack
.. autoclass:: Nak
.. autoclass:: Anything
.. autoclass:: Faulted
.. autoclass:: Aborted
.. autoclass:: TimedOut
.. autoclass:: TemporarilyUnavailable
.. autoclass:: Busy
.. autoclass:: Overloaded
.. autoclass:: OutOfService

.. currentmodule:: layer_cake.convert_type

.. autofunction:: def_type
.. autofunction:: cast_to

.. currentmodule:: layer_cake.virtual_point

.. autoclass:: Point
.. automethod:: Point.create
.. automethod:: Point.send
.. automethod:: Point.reply
.. automethod:: Point.forward
.. automethod:: Point.start
.. automethod:: Point.cancel
.. automethod:: Point.complete
.. automethod:: Point.assign
.. automethod:: Point.progress
.. automethod:: Point.debrief
.. automethod:: Point.working
.. automethod:: Point.on_return
.. automethod:: Point.continuation
.. autoclass:: Threaded
.. autoclass:: T1

.. currentmodule:: layer_cake.point_machine

.. autoclass:: Stateless
.. autoclass:: StateMachine

Portable Type System
********************

.. currentmodule:: layer_cake.message_memory

.. autoclass:: Portable

.. autoclass:: Boolean
.. autoclass:: Integer8
.. autoclass:: Float8
.. autoclass:: Byte
.. autoclass:: Character
.. autoclass:: Rune
.. autoclass:: String
.. autoclass:: Unicode
.. autoclass:: Block
.. autoclass:: Enumeration
.. autoclass:: ClockTime
.. autoclass:: TimeSpan
.. autoclass:: WorldTime
.. autoclass:: TimeDelta
.. autoclass:: UUID
.. autoclass:: UserDefined
.. autoclass:: ArrayOf
.. autoclass:: VectorOf
.. autoclass:: DequeOf
.. autoclass:: SetOf
.. autoclass:: MapOf
.. autoclass:: Type
.. autoclass:: Word
.. autoclass:: Any
.. autoclass:: Address
.. autoclass:: PointerTo

Message I/O
***********

.. currentmodule:: layer_cake.virtual_point

.. autoclass:: Buffering
.. automethod:: Buffering.input

.. currentmodule:: layer_cake.get_response

.. autoclass:: GetResponse

Concurrency
***********

.. currentmodule:: layer_cake.object_spool

.. autoclass:: ObjectSpool

.. currentmodule:: layer_cake.process_object

.. autoclass:: ProcessObject

.. currentmodule:: layer_cake.retry_intervals

.. autoclass:: RetryIntervals

Composite Processes
*******************

.. currentmodule:: layer_cake.home_role

.. autofunction:: resource_path
.. autofunction:: model_path
.. autofunction:: tmp_path

Folders And Files
*****************

.. currentmodule:: layer_cake.folder_object

.. autoclass:: Folder
.. automethod:: Folder.file
.. automethod:: Folder.folder
.. automethod:: Folder.matching
.. automethod:: Folder.each
.. automethod:: Folder.store
.. automethod:: Folder.recover
.. automethod:: Folder.add
.. automethod:: Folder.update
.. automethod:: Folder.remove
.. automethod:: Folder.clear
.. automethod:: Folder.erase
.. automethod:: Folder.exists

.. currentmodule:: layer_cake.file_object

.. autoclass:: File
.. automethod:: File.store
.. automethod:: File.recover
