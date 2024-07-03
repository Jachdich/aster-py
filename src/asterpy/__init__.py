"""Simple python wrapper for controlling an aster account"""

import socket
import ssl
import json
import threading
import base64
import asyncio
import random
from typing import *
from enum import Enum, auto
from .user import User
from .channel import Channel
from .message import Message
from .sync import SyncData, SyncServer
from .emoji import Emoji

DEBUG = False

MY_API_VERSION = [0, 1, 0]

class AsterError(Exception):
    pass

class ConnectionMode(Enum):
    """How to authenticate with the aster server."""
    LOGIN = auto()
    REGISTER = auto()
    NEITHER = auto()

def debug(*args):
    if DEBUG:
        print(*args)

def fetch_emoji(emoji):
    #emojis of the form <:cospox.com:3245:69420:>
    bits = emoji.split(":")
    if len(bits) != 5:
        raise RuntimeError("Emoji not in correct form!")
    if bits[0] != "<" or bits[-1] != ">":
        raise RuntimeError("Emoji not in correct form!")

    ip = bits[1]
    port = int(bits[2])
    uuid = int(bits[3])

    client = Client(ip, port, "", "", login=False)
    async def on_ready():
        #TODO weird hack
        client.username = await client.fetch_emoji(uuid)
        await client.disconnect()
    client.on_ready = on_ready
    try:
        client.run()
    except OSError: #connection failed for some reason
        return None
    return client.username

def fetch_pfp(ip, port, uuid):
    client = Client(ip, port, "", "", login=False)
    async def on_ready():
        #TODO weird hack
        client.username = await client._fetch_pfp(uuid)
        await client.disconnect()
    client.on_ready = on_ready
    try:
        client.run()
    except OSError: #connection failed for some reason
        return None
    return client.username


class Client:
    """Represents a client connection to one server"""
    def __init__(self, username: str, password: str):
        """
        :param username: the default username to use for connecting to servers
        :param password: the default password to use for connecting to servers
        
        """
        self.on_message = None
        self.on_ready = None
        self.on_packet = None
        self.servers = {}
        self.name = ""
        self.pfp_b64 = ""

        #TODO this is terrible, make it better
        self.waiting_for = {}
        self.data_lock = asyncio.Condition()
        self.writer = None

        self.running = True

        self.packet_callbacks = {}
        self.tasks = set() # strong references to "set and forget" tasks like ``on_ready``
        self.username = username
        self.password = password

        # TEMP
        self.channels = []
    
    def add_server(self, ip: str, port: int, *, username: str=None, password: str=None, uuid: int=None, connect_mode: ConnectionMode=ConnectionMode.LOGIN):
        """
        Add a server to the list of servers to connect to.
        
        :param ip: the IP to connect to.
        :param port: the port to connect to.
        :param uuid: User ID to log in with. Prefer specifying this over specifying the username, as the UUID will not change even if you change the username.
        :param username: The username to log in with. If neither ``uuid`` or ``username`` are specified, the username passed to the constructor will be used.
        :param password: The password to log in with. If no password is provided, the password passed to the constructor will be used.
        :param login: Whether or not to log in to this server.
        :param register: Whether or not to register an account with this server.
        """
        
        username = username or self.username
        password = password or self.password
        # TODO this is a hack to make it work with single servers for now
        self.ip = ip
        self.port = port
        self.uuid = uuid
        self.self_uuid = uuid
        self.connect_mode = connect_mode
        self.initialised = False
        self.peers = {}
        self.channels = []
        
    
    def event(self, fn: Callable):
        """
        Register an event handler with the client. Possible event handlers are:
            - on_message: Called when any message is received in any channel. ``fn`` must take one argument of type :py:class:`Message`
            - on_packet: Called when any packet of any kind is received. ``fn`` must take one argument of type ``dict``
            - on_ready: Called when the client is finished initialising. ``fn`` must take no arguments.
        """
        setattr(self, fn.__name__, fn)
        return fn

    def call_on_packet(self, packet_name: str, callback: Callable, once=True):
        """
        Set up a callback (any function or lambda) to be called when a packet with name ``packet_name`` is received.
        
        :param packet_name: Type of packet to listen for
        :param callback: The callback function to use
        :param once: Whether to remove the callback after the first call
        
        """
        if not packet_name in self.packet_callbacks:
            self.packet_callbacks[packet_name] = []
        self.packet_callbacks[packet_name].append((callback, once))
        
    async def __handle_packet(self, packet: str):
        # todo handle json decoding error
        # todo UPDATE: PROPERLY handle it
        try:
            packet = json.loads(packet)
        except:
            print(f"Unable to decode packet '{packet}'")
            return
        if self.on_packet is not None:
            await self.__start_task(self.on_packet(packet))

        debug(f"command is {packet.get('command')}")

        if packet.get("command") in self.waiting_for:
            async with self.data_lock:
                self.waiting_for[packet.get("command")][0][1] = packet # wtf
                self.data_lock.notify()
        
        if packet.get("command", None) is not None:
            cmd = packet["command"]

            if cmd in self.packet_callbacks:
                to_remove = []
                for cb in self.packet_callbacks[cmd]:
                    await self.__start_task(cb[0](packet)) #call callback
                    if cb[1]: #if only once, then remove callback from list
                        to_remove.append(cb)
                
                for cb in to_remove:
                    self.packet_callbacks[cmd].remove(cb)

            if packet.get("status") != 200:
                print(f"Packet '{cmd}' failed with code {packet.get('status')}")
                return
            
            if cmd == "login" or cmd == "register":
                await self.__send_multiple([
                    {"command": "get_metadata"},
                    {"command": "list_channels"},
                    {"command": "online"},
                    {"command": "get_name"},
                    {"command": "get_icon"},
                ])

                if self.init_commands:
                    await self.__send_multiple(init_commands)
                

            if cmd == "content":
                if self.on_message is not None:
                    await self.__start_task(self.on_message(Message(
                        packet["content"],
                        self.peers[packet["author_uuid"]],
                        self.get_channel(packet["channel_uuid"]),
                        packet["date"],
                        packet["uuid"]
                    )))

            elif cmd == "API_version":
                # Check that we support the API version that the server supports
                remote_version = packet["version"]

                if remote_version[0] > MY_API_VERSION[0]:
                    # Server too new
                    message = "a newer"
                elif remote_version[0] < MY_API_VERSION[0]:
                    # Server too old
                    message = "an older"

                if remote_version[0] != MY_API_VERSION[0]:
                    # Either case, version doesn't match: raise error
                    my_version_string = ".".join(map(str, MY_API_VERSION))
                    remote_version_string = ".".join(map(str, remote_version))
                    raise AsterError(f"Attempt to connect to a server that only supports {message} API version than we do" + 
                                     f" (We support {my_version_string}," + 
                                     f" they support {remote_version_string})")

                # await self.send({"command": "yes, we are indeed an aster client. please connect.", "data": 69420})
                
            elif cmd == "login" or cmd == "register":
                self.self_uuid = packet["uuid"]

            elif cmd == "get_metadata":
                for elem in packet["data"]:
                    elem_uuid = elem["uuid"]
                    if elem_uuid in self.peers:
                        self.peers[elem_uuid].update_from_json(elem)
                    else:
                        self.peers[elem_uuid] = User.from_json(elem)

            elif cmd == "list_channels":
                for elem in packet["data"]:
                    self.__add_channel(elem)

            elif cmd == "get_name":
                self.name = packet["data"]
            elif cmd == "get_icon":
                self.pfp_b64 = packet["data"]

        if not self.initialised:
            if self.self_uuid != 0 and self.name != "" and self.pfp_b64 != "" and len(self.channels) > 0:
                self.initialised = True
                if self.on_ready != None:
                    await self.__start_task(self.on_ready())

    async def send(self, message: dict[any]):
        """
        Send a packet to the server.

        :param message: The packet to send, as a dictionary.
        """
        # TODO if not connected, raise proper error
        if self.writer is None:
            raise AsterError("Not connected")
        # print((json.dumps(message) + "\n").encode("utf-8"))
        self.writer.write((json.dumps(message) + "\n").encode("utf-8"))
        await self.writer.drain()

    async def disconnect(self):
        """
        Disconnect from the server.
        """
        #same with this
        self.running = False
        if self.writer is not None:
            await self.send({"command": "leave"})

    def get_pfp(self, uuid: int) -> Optional[bytes]:
        """
        Get the profile picture for the user with the corrosponding UUID. This uses cached data.

        :param uuid: The UUID of the user to fetch the profile picture from.
        :returns: PNG-compressed image data, or ``None`` if the user doesn't exist.
        """
        if uuid in self.peers:
            return self.peers[uuid].pfp

    def get_name(self, uuid: int) -> Optional[str]:
        """
        Get the username of the user identified by the given UUID.

        :param uuid: The UUID of the user to get the name of.
        :returns: The name of the user, or ``None`` if the user doesn't exist.
        """
        if uuid == self.self_uuid:
            return self.username
        if uuid in self.peers:
            return self.peers[uuid].username

    def get_channel(self, uuid: int) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object associated with the given ID.

        :param uuid: The ID of the channel.
        :returns: The channel, or ``None`` if it doesn't exist
        """
        for channel in self.channels:
            if channel.uuid == uuid: return channel

    def get_channel_by_name(self, name: str) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object by referring to its name. Generally, prefer using the ID to reference channels rather than the name if possible.

        :param name: The name of the channel.
        :returns: The channel, or ``None`` if it doesn't exist.
        """
        for channel in self.channels:
            if channel.name == name.strip("#"):
                return channel

    def __add_channel(self, data: Dict[str, Any]):
        self.channels.append(Channel(self, data["name"], data["uuid"]))

    async def get_response(self, packet: dict):
        if not packet["command"] in self.waiting_for:
            self.waiting_for[packet["command"]] = []
        queue: list = self.waiting_for[packet["command"]]

        our_index = random.randint(0, 2**63-1) # TODO this isn't very elegent
        queue.append([our_index, None])

        def our_data():
            for i in queue:
                if i[0] == our_index:
                    return i

        async with self.data_lock:
            await self.send(packet)
            while our_data()[1] is None:
                await self.data_lock.wait()

        packet = our_data()
        queue.remove(packet)

        return packet[1]

    async def __start_task(self, coro: Coroutine):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        
    async def fetch_sync(self) -> Optional[SyncData]:
        """
        Fetch the :py:class:`SyncData` from the server.

        :returns: The :py:class:`SyncData` object, or ``None`` if the server has no sync data.
        """
        sync_data = await self.get_response({"command": "sync_get"})
        sync_servers = await self.get_response({"command": "sync_get_servers"})
        return SyncData.from_json(sync_data, sync_servers)
                
    async def fetch_history(self, channel: Channel, count: int=100,  init_message: Message=None) -> List[Message]:
        """
        Fetch the last ``count`` messages from a given channel.

        :param channel: The channel from which to fetch the messages.
        :param count: The number of messages to fetch. (defeault: 100)
        :param init_message: Fetch ``count`` messages before this message. If init_message == None, then fetch the last ``count`` messages.
        :returns: A list of messages.
        """
        request = {"command": "history", "num": count, "channel": channel.uuid}
        if init_message is not None:
            request["before_message"] = init_message.uuid
            
        packet = await self.get_response(request)
        return [Message(elem["content"], self.peers[elem["author_uuid"]], channel, elem["date"], elem["uuid"]) for elem in packet["data"]]

    async def fetch_emoji(self, uuid: int) -> Emoji:
        """
        :param uuid: ID of the emoji to fetch.
        """
        data = await self.get_response({"command": "get_emoji", "uuid": uuid})
        if data["code"] == 0:
            return Emoji.from_json(data["data"])
        raise AsterError(f"Get emoji from {self.ip}:{self.port} returned code {data['code']}")

    async def _fetch_pfp(self, uuid: int) -> bytes: # TODO naming...
        data = await self.get_response({"command": "get_user", "uuid": uuid})
        if data["status"] != 200:
            return None # failed for some reason
        return User.from_json(data["data"]).pfp

    async def list_emojis(self) -> List[Emoji]:
        """
        Fetch a list of custom emojis from the server.
        """
        data = await self.get_response({"command": "list_emoji"})
        return [Emoji.from_json(n) for n in data["data"]]

    async def __send_multiple(self, messages: List[dict]):
        for msg in messages:
            await self.send(msg) # TODO less efficient cos TaskGroup was introduced in 3.11...
    
    async def __login(self):
        if self.connect_mode == ConnectionMode.LOGIN:
            if self.uuid is None:
                await self.send({"command": "login", "uname": self.username, "passwd": self.password})
            else:
                await self.send({"command": "login", "uuid": self.uuid, "passwd": self.password})

        elif self.connect_mode == ConnectionMode.REGISTER:
            await self.send({"command": "register", "uname": self.username, "passwd": self.password})
                
    
    async def __listen(self, reader):
        reader._limit = 64 * 1024 * 1024 # increase limit to 64MiB, cos messages can get big
        while self.running:
            line = await reader.readline()
            if not line: break
            await self.__handle_packet(line)
    
    async def connect(self, init_commands: Optional[List[dict]]=None):
        """
        Connect to the server and listen for packets. This function blocks until :py:meth:`Client.disconnect` is called.

        :param init_commands: Optional list of packets to send to the server after connecting.
        """
        context = ssl.SSLContext()
        reader, writer = await asyncio.open_connection(self.ip, self.port, ssl=context)
        self.writer = writer
        self.init_commands = init_commands
        try:
            if self.connect_mode == ConnectionMode.NEITHER:
                self.initialised = True
                if self.on_ready is not None:
                    self.__start_task(self.on_ready())

            await self.__login()
            await self.__listen(reader)
        finally:
            writer.close()
            await writer.wait_closed()
    
    def run(self, init_commands: Optional[List[dict]]=None):
        """
        Wrapper to call :py:meth:`connect` synchronously.
        """
        asyncio.run(self.connect(init_commands))
