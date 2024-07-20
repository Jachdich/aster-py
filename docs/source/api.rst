API Documentation
=================

Naming
------

Generally, functions like ``get_xxxx`` use cached values and functions like ``fetch_xxxx`` block while waiting for a response from the server. Functions like ``list_xxxx`` generally return multiple items, usually but not always from cache.

Classes
-------

.. currentmodule:: asterpy

.. autoclass:: Client

	.. rubric:: Attributes
	.. autoattribute:: servers

	.. rubric:: Methods
	.. autodecorator:: asterpy.Client.event
	.. automethod:: __init__
	.. automethod:: add_server
	.. automethod:: get_user
	.. automethod:: get_channel
	.. automethod:: get_channel_by_name
	.. automethod:: connect
	.. automethod:: run

----

.. autoclass:: Server

	.. rubric:: Attributes
	.. autoattribute:: channels
	.. autoattribute:: peers
	.. autoattribute:: name
	.. autoattribute:: icon
	
	.. rubric:: Methods

	.. automethod:: __init__
	.. automethod:: connect
	.. automethod:: disconnect
	.. automethod:: get_channel
	.. automethod:: get_channel_by_name
	.. automethod:: get_user
	.. automethod:: fetch_user
	.. automethod:: fetch_emoji
	.. automethod:: fetch_sync
	.. automethod:: list_emojis
	.. automethod:: send
	.. automethod:: get_response


----

.. autoclass:: ConnectionMode

	.. rubric:: Attributes
	.. autoattribute:: LOGIN
	.. autoattribute:: REGISTER
	.. autoattribute:: NEITHER

----

.. autoclass:: Channel

	.. rubric:: Attributes
	.. autoattribute:: name
	.. autoattribute:: uuid
	.. rubric:: Methods
	.. automethod:: send
	.. automethod:: fetch_history

----

.. autoclass:: User

	.. rubric:: Attributes
	.. autoattribute:: uuid
	.. autoattribute:: username
	.. autoattribute:: pfp

----

.. autoclass:: Message

	.. rubric:: Attributes
	.. autoattribute:: content
	.. autoattribute:: author
	.. autoattribute:: channel
	.. autoattribute:: date

----

.. autoclass:: Emoji

	.. rubric:: Attributes
	.. autoattribute:: data
	.. autoattribute:: name
	.. autoattribute:: uuid

----

.. autoclass:: SyncServer
	
	.. rubric:: Attributes
	.. autoattribute:: ip
	.. autoattribute:: port
	.. autoattribute:: pfp
	.. autoattribute:: name
	.. autoattribute:: uuid
	.. rubric:: Methods
	.. automethod:: from_json
	
----

.. autoclass:: SyncData

	.. rubric:: Attributes
	.. autoattribute:: uname
	.. autoattribute:: pfp
	.. autoattribute:: servers
	
	.. rubric:: Methods
	.. automethod:: from_json
