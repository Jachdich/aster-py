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

class Server:
    """Represents a client connection to one server"""
    def __init__(self, ip: str, port: int, *, username: str=None, password: str=None, uuid: int=None, connect_mode: ConnectionMode=ConnectionMode.LOGIN):
        assert connect_mode == ConnectionMode.LOGIN and password is not None, "You must supply a password if logging in"
        assert connect_mode == ConnectionMode.LOGIN and (username is not None or uuid is not None), "You must supply at least one of username or uuid if logging in"

        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.connect_mode = connect_mode

        self.waiting_for = {}
        self.writer = None

        self.running = True
        self.name = ""
        self.pfp_b64 = ""
        self.self_uuid = uuid
        
        self.peers = {}
        self.channels = []

        self.initialised = False

    async def __handle_packet(self, packet: str):
        # todo handle json decoding error
        # todo UPDATE: PROPERLY handle it
        try:
            packet = json.loads(packet)
        except:
            print(f"Unable to decode packet '{packet}'")
            return

        debug(f"command is {packet.get('command')}")

        if packet.get("command") in self.waiting_for:
            queue: list[asyncio.Future] = self.waiting_for[packet["command"]]
            if len(queue) > 0:
                fut = queue.pop(0)
                fut.set_result(packet)
        
        if packet.get("command", None) is not None:
            cmd = packet["command"]

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

    def __add_channel(self, data: Dict[str, Any]):
        self.channels.append(Channel(self, data["name"], data["uuid"]))

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
        self.running = False
        if self.writer is not None:
            await self.send({"command": "leave"})

    def get_user(self, uuid: int) -> Optional[User]:
        """
        Get the :py:class:`User` object corrosponding to the given UUID.

        :param uuid: The UUID of the user.
        :returns: The :py:class:`User` object, or ``None`` if the user doesn't exist.
        """
        if uuid in self.peers:
            return self.peers[uuid]

    def get_channel(self, uuid: int) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object associated with the given ID.

        :param uuid: The ID of the channel.
        :returns: The :py:class:`Channel`, or ``None`` if it doesn't exist
        """
        for channel in self.channels:
            if channel.uuid == uuid: return channel

    # TODO is this function required?
    def get_name(self) -> str:
        """Get the name of the server."""
        return self.name

    def get_icon(self) -> bytes:
        """
        Get the icon of the server.
        :returns: PNG-compressed image data.
        """
        return base64.b64decode(self.pfp_b64)

    def get_channel_by_name(self, name: str) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object by referring to its name.
        Generally, prefer using the ID to reference channels rather than the name if possible, as the name could change.

        :param name: The name of the channel.
        :returns: The channel, or ``None`` if it doesn't exist.
        """
        for channel in self.channels:
            if channel.name == name.strip("#"):
                return channel

    async def get_response(self, packet: dict):
        if not packet["command"] in self.waiting_for:
            self.waiting_for[packet["command"]] = []
        queue: list = self.waiting_for[packet["command"]]

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        queue.append(future)

        await self.send(packet)
        return await future

    async def fetch_sync(self) -> Optional[SyncData]:
        """
        Fetch the :py:class:`SyncData` from the server.

        :returns: The :py:class:`SyncData` object, or ``None`` if the server has no sync data.
        """
        sync_data = await self.get_response({"command": "sync_get"})
        sync_servers = await self.get_response({"command": "sync_get_servers"})
        return SyncData.from_json(sync_data, sync_servers)
                
    async def fetch_emoji(self, uuid: int) -> Emoji:
        """
        :param uuid: ID of the emoji to fetch.
        """
        data = await self.get_response({"command": "get_emoji", "uuid": uuid})
        if data["code"] == 0:
            return Emoji.from_json(data["data"])
        raise AsterError(f"Get emoji from {self.ip}:{self.port} returned code {data['code']}")

    async def fetch_user(self, uuid: int) -> Optional[User]:
        """
        Fetch a :py:class:`User` fresh from the server. Send a new packet and get the result instead of using cached data.
        :param uuid: The UUID of the user.
        :returns: The :py:class:`User` object, or ``None`` if the user doesn't exist or another error occurred.
        """
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

class Client:
    """Asterpy client that can be connected to multiple servers"""
    def __init__(self, username: str, password: str):
        """
        :param username: the default username to use for connecting to servers
        :param password: the default password to use for connecting to servers
        """
        self.on_message = None
        self.on_ready = None
        self.on_packet = None
        self.servers: list[Server] = []

        self.tasks = set() # strong references to "set and forget" tasks like ``on_ready``
        self.username = username
        self.password = password

    
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
        
        self.servers.append(Server(ip, port, username=username, password=password, uuid, connect_mode))
    
    def event(self, fn: Callable):
        """
        Register an event handler with the client. Possible event handlers are:
            - on_message: Called when any message is received in any channel. ``fn`` must take one argument of type :py:class:`Message`
            - on_packet: Called when any packet of any kind is received. ``fn`` must take one argument of type ``dict``
            - on_ready: Called when the client is finished initialising. ``fn`` must take no arguments.
        """
        setattr(self, fn.__name__, fn)
        return fn

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
            queue: list[asyncio.Future] = self.waiting_for[packet["command"]]
            if len(queue) > 0:
                fut = queue.pop(0)
                fut.set_result(packet)
        
        if packet.get("command", None) is not None:
            cmd = packet["command"]

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
        for server in self.servers:
            pfp = server.get_pfp(uuid)
            if pfp is not None:
                return pfp

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

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        queue.append(future)

        await self.send(packet)
        return await future

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
