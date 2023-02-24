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

	ip = "aster server IP"
	port = aster server port
	username = "your username"
	password = "your password"
	
	client = asterpy.Client(ip, port, username, password)

	@client.event
	def on_message(message):
	    if message.content == "ping":
	        message.channel.send("pong")

	@client.event
	def on_ready():
	    print("Ready!")

	client.run()


You can also log in using the UUID of the user, by passing ``uuid=<your uuid>`` in addition to the username.

