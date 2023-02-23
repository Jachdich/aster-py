# Classes

## Client

### Methods

- [`call_on_packet`](#call_on_packet)
- [`disconnect`](#disconnect)
- [`@event`](#event) (decorator)
- [`fetch_emoji`](#fetch_emoji)
- [`get_channel`](#get_channel)
- [`get_channels`](#get_channels)
- [`get_channel_by_name`](#get_channel_by_name)
- [`get_history`](#get_history)
- [`get_name`](#get_name)
- [`get_pfp`](#get_pfp)
- [`get_sync`](#get_sync)
- [`list_emojis`](#list_emojis)
- [`run`](#run)
- [`send`](#send)

### Fields

- `on_message`
- `on_ready`
- `on_packet`

### `call_on_packet`

`Client.call_on_packet(packet_name: str, callback: Callable, once: bool=True)`

Set up a callback (any function or lambda) to be called when a packet with name `packet_name` is received. If `once` is `True`, this callback will be removed immediately after it is called, and therefore will only run when the next packet of the specified type is received. Alternately, if `once` is `False` the callback is kept indefinitely.

### `disconnect`

`Client.disconnect()`

Disconnect from the aster server

### `event`

`@Client.event`

Register an event handler with the client. This function is intended to be used as a decorator.

Available events:
- `on_ready`: called when the client has initialised
- `on_message`: called whenever the client receives a message. Takes one argument, the message as a [`Message`](#message)
- `on_packet`: called whenever the client receives any packet. Takes one argument, the packet as a `dict`

Example:
```py
@client.event
def on_ready():
    print("Ready") 
```

### `fetch_emoji`

`Client.fetch_emoji(uid: int) -> `[`Emoji`](#emoji)

Ask the connected server for an emoji with the specified UID.

### `get_channel`

`Client.get_channel(uid: int) -> `[`Channel`](#channel)

Return the channel with the specified UID, or `None` if the channel does not exist or has not been cached for some reason.

### `get_channel_by_name`

`Client.get_channel_by_name(name: str) -> `[`Channel`](#Channel)

Return the channel with the specified name, or `None` if the channel does not exist or has not been cached for some reason. Generally, prefer using UIDs rather than names where possible.

# Functions



