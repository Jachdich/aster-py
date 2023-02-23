# aster.py

Aster.py is a python implementation of the [Aster](https://github.com/Jachdich/aster-server) protocol, designed for use in bots or custom clients. The syntax is heavily inspired by [discord.py](https://github.com/Rapptz/discord.py).

Currently a work in progress, does not support all of the features of Aster.

PyPI release can be found [here](https://pypi.org/project/asterpy/)


## Documentation

See docs.md

## Example

Ping example (listens for "ping" and responds "pong")
```py
import asterpy

client = asterpy.Client(ip, port, username, password, uuid)

@client.event
def on_message(message):
    if message.content == "ping":
        message.channel.send("pong")

@client.event
def on_ready():
    print("Ready!")

client.run()
```