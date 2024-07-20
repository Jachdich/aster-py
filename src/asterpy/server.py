from __future__ import annotations
from .connection_mode import ConnectionMode
from .debug import debug
import json
from typing import *
# if TYPE_CHECKING:
from .channel import Channel
from .user import User
from .emoji import Emoji
from .sync import SyncData
import asyncio
import ssl

MY_API_VERSION = [0, 1, 0]

class Server:
    """Represents a client connection to one server"""
    #: Server name
    name: str = ""
    #: PNG-encoded server picture
    icon: bytes = b""
    channels: list[Channel] = []
    #: Map from UUIDs to Users
    peers: dict[int, User] = {}
    
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
        self.icon = b""
        #: UUID of logged in account on this server
        self.self_uuid = uuid
        
        self.peers = {}
        self.channels = []

        self.initialised = False
        self.on_packet = None
        self.on_ready = None

    async def __handle_packet(self, packet: str):
        # todo handle json decoding error
        # todo UPDATE: PROPERLY handle it
        try:
            packet = json.loads(packet)
        except:
            print(f"Unable to decode packet '{packet}'")
            return

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
                

            # TODO add to history?
            # if cmd == "content":
            #     if self.on_message is not None:
            #         await self.__start_task(self.on_message(Message(
            #             packet["content"],
            #             self.peers[packet["author_uuid"]],
            #             self.get_channel(packet["channel_uuid"]),
            #             packet["date"],
            #             packet["uuid"]
            #         )))

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
                self.icon = base64.b64decode(packet["data"])

        if not self.initialised:
            if self.self_uuid != 0 and self.name != "" and len(self.icon) > 0 and len(self.channels) > 0:
                self.initialised = True
                if self.on_ready is not None:
                    await self.on_ready()

        if self.on_packet is not None:
            await self.on_packet(packet, self)

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

    async def get_response(self, packet: dict) -> dict:
        """Send a packet of data to the server and wait for a response.
        :param packet: Data to be sent to the server as python dictionary, converted to JSON before sending.
        :returns: The data from the server, decoded to a python dictionary."""
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
            if self.self_uuid is None:
                await self.send({"command": "login", "uname": self.username, "passwd": self.password})
            else:
                await self.send({"command": "login", "uuid": self.self_uuid, "passwd": self.password})

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
