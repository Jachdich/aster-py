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
	.. autoattribute:: channels
	
	.. rubric:: Methods

	.. automethod:: __init__
	.. automethod:: call_on_packet
	.. automethod:: connect
	.. automethod:: disconnect
	.. autodecorator:: asterpy.Client.event
	.. automethod:: fetch_emoji
	.. automethod:: fetch_history
	.. automethod:: fetch_sync
	.. automethod:: get_channel
	.. automethod:: get_channel_by_name
	.. automethod:: get_name
	.. automethod:: get_pfp
	.. automethod:: list_channels
	.. automethod:: list_emojis
	.. automethod:: run
	.. automethod:: send


----

.. autoclass:: Channel

	.. rubric:: Attributes
	.. autoattribute:: name
	.. autoattribute:: uid
	.. rubric:: Methods
	.. automethod:: send

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
	.. autoattribute:: uid

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
