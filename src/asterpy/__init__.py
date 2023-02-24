"""Simple python wrapper for controlling an aster account"""

import socket
import ssl
import json
import threading
import base64
from typing import *
from .user import User
from .channel import Channel
from .message import Message
from .sync import SyncData, SyncServer
from .emoji import Emoji

DEBUG = True

class AsterError(Exception):
    pass

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
    def on_ready():
        #TODO weird hack
        client.username = client.fetch_emoji(uuid)
        client.disconnect()
    client.on_ready = on_ready
    try:
        client.run()
    except OSError: #connection failed for some reason
        return None
    return client.username


def fetch_pfp(ip, port, uuid):
    client = Client(ip, port, "", "", login=False)
    def on_ready():
        #TODO weird hack
        client.username = client._fetch_pfp(uuid)
        client.disconnect()
    client.on_ready = on_ready
    try:
        client.run()
    except OSError: #connection failed for some reason
        return None
    return client.username


class Client:
    """Represents a client connection to one server"""
    def __init__(self, ip: str, port: int, username: str, password: str, uuid=None, login=True, register=False):
        """
        :param ip: The IP address to connect to
        
        """
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.uuid = uuid
        self.on_message = None
        self.on_ready = None
        self.on_packet = None
        self.ssock = None
        self.self_uuid = 0
        self.channels = []
        self.name = ""
        self.pfp_b64 = ""
        self.login = login
        self.register = register

        #TODO this is terrible, make it better
        self.waiting_for = None
        self.waiting_data = None
        self.data_lock = threading.Condition()

        self.peers = {}
        self.running = True
        self.initialised = False

        self.packet_callbacks = {}

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
        
    def __handle_packet(self, packet: str):
        # todo handle json decoding error
        # todo UPDATE: PROPERLY handle it
        print(packet)
        try:
            packet = json.loads(packet)
        except:
            print(f"Unable to decode packet '{packet}'")
            return
        if self.on_packet is not None:
            self.on_packet(packet)

        print(f"command is {packet.get('command')}")

        if self.waiting_for is not None and packet.get("command") == self.waiting_for:
            with self.data_lock:
                self.waiting_data = packet
                self.waiting_for = None
                self.data_lock.notify()
        
        if packet.get("command", None) is not None:
            cmd = packet["command"]

            if cmd in self.packet_callbacks:
                to_remove = []
                for cb in self.packet_callbacks[cmd]:
                    cb[0](packet) #call callback
                    if cb[1]: #if only once, then remove callback from list
                        to_remove.append(cb)
                
                for cb in to_remove:
                    self.packet_callbacks[cmd].remove(cb)

            if packet.get("status") != 200:
                print(f"Packet '{cmd}' failed with code {packet.get('status')}")
                return

            if cmd == "content":
                print(packet)
                if self.on_message is not None:
                    self.on_message(Message(
                        packet["content"],
                        self.peers[packet["author_uuid"]],
                        self.get_channel(packet["channel_uuid"]),
                        packet["date"]
                    ))

            elif cmd == "login" or cmd == "register":
                self.self_uuid = packet["uuid"]

            elif cmd == "metadata":
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
                    threading.Thread(target=self.on_ready).start() #TODO weird workaround, make it better

            #if self.self_uuid += 

    def send(self, message: dict[any]):
        """
        Send a packet to the server.

        :param message: The packet to send, as a dictionary.
        """
        #TODO if not connected, raise proper error
        if self.ssock is None:
            raise AsterError("Not connected")
        print((json.dumps(message) + "\n").encode("utf-8"))
        self.ssock.send((json.dumps(message) + "\n").encode("utf-8"))

    def disconnect(self):
        """
        Disconnect from the server.
        """
        #same with this
        self.running = False
        if self.ssock is not None:
            self.send({"command": "leave"})

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

    def get_channel(self, uid: int) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object associated with the given ID.

        :param uid: The ID of the channel.
        :returns: The channel, or ``None`` if it doesn't exist
        """
        for channel in self.channels:
            if channel.uid == uid: return channel

    def get_channel_by_name(self, name: str) -> Optional[Channel]:
        """
        Get the :py:class:`Channel` object by referring to its name. Generally, prefer using the ID to reference channels rather than the name if possible.

        :param name: The name of the channel.
        :returns: The channel, or ``None`` if it doesn't exist.
        """
        for channel in self.channels:
            if channel.name == name.strip("#"):
                return channel

    def list_channels(self) -> List[Channel]:
        """
        :returns: A list of all the channels in the current server.
        """
        return self.channels

    def __add_channel(self, data: Dict[str, Any]):
        self.channels.append(Channel(self, data["name"], data["uuid"]))

    def __block_on(self, command: dict):
        if self.waiting_for is not None:
            raise RuntimeWarning(f"Attempt to __block_on while already waiting for '{self.waiting_for}'!")
            return
        self.waiting_for = command["command"]
        with self.data_lock:
            self.send(command)
            while self.waiting_data is None:
                self.data_lock.wait()

        packet = self.waiting_data
        self.waiting_data = None
        self.waiting_for = None

        return packet
        
    def fetch_sync(self) -> Optional[SyncData]:
        """
        Fetch the :py:class:`SyncData` from the server.

        :returns: The :py:class:`SyncData` object, or ``None`` if the server has no sync data.
        """
        sync_data = self.__block_on({"command": "sync_get"})
        sync_servers = self.__block_on({"command": "sync_get_servers"})
        return SyncData.from_json(sync_data, sync_servers)
                
    def fetch_history(self, channel: Channel) -> List[Message]:
        """
        Fetch the last 100 messages from a given channel.

        :param channel: The channel from which to fetch the messages.
        :returns: A list of messages.
        """
        packet = self.__block_on({"command": "history", "num": 100, "channel": channel.uuid})
        return [Message(elem["content"], self.peers[elem["author_uuid"]], channel, elem["date"]) for elem in packet["data"]]

    def fetch_emoji(self, uid: int) -> Emoji:
        """
        :param uid: ID of the emoji to fetch.
        """
        data = self.__block_on({"command": "get_emoji", "uid": uid})
        if data["code"] == 0:
            return Emoji.from_json(data["data"])
        raise AsterError(f"Get emoji from {self.ip}:{self.port} returned code {data['code']}")

    def _fetch_pfp(self, uuid: int) -> bytes: # TODO naming...
        data = self.__block_on({"command": "get_user", "uuid": uuid})
        return User.from_json(data["data"]).pfp

    def list_emojis(self) -> List[Emoji]:
        """
        Fetch a list of custom emojis from the server.
        """
        data = self.__block_on({"command": "list_emoji"})
        return [Emoji.from_json(n) for n in data["data"]]

    def run(self, init_commands: Optional[List[dict]]=None):
        """
        Connect to the server and listen for packets. This function blocks until :py:meth:`Client.disconnect` is called.

        :param init_commands: Optional list of packets to send to the server after connecting.
        """
        context = ssl.SSLContext()
        with socket.create_connection((self.ip, self.port)) as sock:
            with context.wrap_socket(sock, server_hostname=self.ip) as ssock:
                self.sock = sock
                self.ssock = ssock

                if self.login:
                    if self.uuid is None:
                        self.send({"command": "login", "uname": self.username, "passwd": self.password})
                    else:
                        self.send({"command": "login", "uuid": self.uuid, "passwd": self.password})

                    # todo: check login status before sending further commands?
                    self.send({"command": "get_metadata"})
                    self.send({"command": "list_channels"})
                    self.send({"command": "online"})
                    self.send({"command": "get_name"})
                    self.send({"command": "get_icon"})
                
                if self.register:
                    self.send({"command": "register", "name": self.username, "passwd": self.password})

                    # todo: check register status before sending further commands?
                    self.send({"command": "get_metadata"})
                    self.send({"command": "list_channels"})
                    self.send({"command": "online"})
                    self.send({"command": "get_name"})
                    self.send({"command": "get_icon"})
                
                if init_commands:
                    for cmd in init_commands:
                        self.send(cmd)

                if not self.register and not self.login:
                    self.initialised = True
                    if self.on_ready is not None:
                        threading.Thread(target=self.on_ready).start() #TODO weird workaround, make it better

                total_data = b""
                while self.running:
                    recvd_packet = ssock.recv(1024)
                    if not recvd_packet: break
                    total_data += recvd_packet
                    if b"\n" in total_data:
                        data = total_data.decode("utf-8").split("\n")
                        total_data = ("\n".join(data[1:])).encode("utf-8")
                        self.__handle_packet(data[0])
