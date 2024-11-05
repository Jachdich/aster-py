from __future__ import annotations
from .server import Server
from .connection_mode import ConnectionMode
from .debug import debug
from typing import *
import asyncio
if TYPE_CHECKING:
    from .user import User
    from .channel import Channel
from .message import Message

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
        
        self.servers.append(Server(ip, port, username=username, password=password, uuid=uuid, connect_mode=connect_mode))
        self.servers[-1].on_packet = self.__handle_packet
        self.servers[-1].on_ready = self.__handle_ready
    
    def event(self, fn: Callable):
        """
        Register an event handler with the client. Used as a decorator. Possible event handlers are:
            - on_message: Called when any message is received in any channel. ``fn`` must take one argument of type :py:class:`Message`
            - on_packet: Called when any packet of any kind is received. ``fn`` must take one argument of type ``dict``
            - on_ready: Called when the client is finished initialising. ``fn`` must take no arguments.
        """
        setattr(self, fn.__name__, fn)
        return fn

    async def __handle_packet(self, packet: dict, from_server: Server):
        if self.on_packet is not None:
            await self.__start_task(self.on_packet(packet))

        cmd = packet["command"]
        debug(f"command is {cmd}")

        if cmd == "content":
            if self.on_message is not None:
                await self.__start_task(self.on_message(Message(
                    packet["content"],
                    from_server.peers[packet["author_uuid"]],
                    from_server.get_channel(packet["channel_uuid"]),
                    from_server,
                    packet["date"],
                    packet["uuid"],
                    packet.get("reply", None)
                )))

    async def __handle_ready(self):
        if self.on_ready != None and all([server.initialised for server in self.servers]):
            await self.__start_task(self.on_ready())

    def get_user(self, uuid: int) -> Optional[User]:
        """
        Get the :py:class:`User` object corrosponding to the given UUID.
        Prefer using the :py:meth:`Server.get_user` method if you already have the :py:class:`Server` object.

        :param uuid: The UUID of the user.
        :returns: The :py:class:`User` object, or ``None`` if the user doesn't exist.
        """
        for server in self.servers:
            user = server.get_user(uuid)
            if user is not None:
                return user

    def get_channel(self, uuid: int) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object associated with the given ID.
        Prefer using the :py:meth:`Server.get_channel` method if you already have the :py:class:`Server` object.

        :param uuid: The ID of the channel.
        :returns: The channel, or ``None`` if it doesn't exist
        """
        for server in self.servers:
            channel = server.get_channel(uuid)
            if channel is not None:
                return channel

    def get_channel_by_name(self, name: str) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object by referring to its name. Generally, prefer using the ID to reference channels rather than the name if possible.
        Prefer using the :py:meth:`Server.get_channel_by_name` method if you already have the :py:class:`Server` object.

        :param name: The name of the channel.
        :returns: The channel, or ``None`` if it doesn't exist.
        """
        for server in self.servers:
            channel = server.get_channel_by_name(name)
            if channel is not None:
                return channel

    async def __start_task(self, coro: Coroutine):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def connect(self, init_commands: Optional[List[dict]]=None):
        """
        Connect to all servers.
        """
        server_tasks = []
        for s in self.servers:
            server_tasks.append(s.connect())
        await asyncio.gather(*server_tasks)
    
    def run(self, init_commands: Optional[List[dict]]=None):
        """
        Wrapper to call :py:meth:`connect` synchronously.
        """
        asyncio.run(self.connect(init_commands))

