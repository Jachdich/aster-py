Quickstart
==========

Installation
------------

Installation can be done via pip:

.. code-block:: console

	$ pip install asterpy

Alternatively, to use the development version, create a link to the ``asterpy`` directory in your project root:

.. code-block:: console

	$ git clone https://github.com/Jachdich/asterpy
	$ mkdir asterpy-program && cd asterpy-program
	$ ln -s ../asterpy/src/asterpy asterpy

This is not recommended unless you're doing development of asterpy itself.

Prerequisites
-------------

To use asterpy you must have access an aster server, and an account on that server to use. It is possible to create an account using asterpy but it's recommended to use a GUI client.

Example
-------

.. code-block:: python

	import asterpy
	
	client = asterpy.Client("Username", "Password")
	client.add_server("example.com", 2345, uuid=my_uuid)

	@client.event
	async def on_message(message):
	    # check if the message author is us. this requires to check against the self_uuid in the server,
	    # because in aster (unlike discord) uuids are per-server
	    if message.author.uuid == message.server.self_uuid:
	        return
	    if message.content == "ping":
	        await message.channel.send("pong")

	@client.event
	async def on_ready():
	    print("Ready!")

	client.run()


You can log in either using your uuid (shown), or by passing ``username="your_username"`` into ``client.add_server``, or if you omit both parameters it will use the username passed into the constructor.
