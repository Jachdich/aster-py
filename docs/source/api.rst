API Documentation
=================

Naming
------

Generally, functions like ``get_xxxx`` use cached values and functions like ``fetch_xxxx`` block while waiting for a response from the server. Functions like ``list_xxxx`` generally return multiple items, usually but not always from cache.

Classes
-------

.. currentmodule:: asterpy

.. autoclass:: Client

	.. automethod:: __init__
	.. automethod:: call_on_packet
	.. autodecorator:: asterpy.Client.event
	.. automethod:: get_pfp
	.. automethod:: get_name
	.. automethod:: get_channel
	.. automethod:: get_channel_by_name
	.. automethod:: list_channels
	.. automethod:: fetch_sync
	.. automethod:: fetch_history
	.. automethod:: fetch_emoji
	.. automethod:: list_emojis
	.. automethod:: run


----

.. autoclass:: Channel

	.. rubric:: Attributes
	.. autoattribute:: name
	.. autoattribute:: uid
	.. rubric:: Methods
	.. automethod:: send

----

.. autoclass:: Emoji

	.. rubric:: Attributes
	.. autoattribute:: name
	.. autoattribute:: uid
	.. rubric:: Methods
	.. automethod:: from_json

