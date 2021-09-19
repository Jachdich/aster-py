"""Simple python wrapper for controlling an aster account"""

import socket
import ssl
import json

class User:
    """Represents a user on the aster server"""
    def __init__(self, uuid: int, username: str):
        self.uuid = uuid
        self.username = username

class Channel:
    """a channel. Shut up pylint"""
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def send(self, message: str):
        self.client.send(message)

class Message:
    """Represents a message in a channel on the server"""
    def __init__(self, content: str, user: User, channel: Channel):
        self.content = content
        self.user = user
        self.channel = channel

class Client:
    """Represents a client connection to one server"""
    def __init__(self, ip: str, port: int, username: str, password: str, uuid=None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.uuid = uuid
        self.message_callback = None
        self.ssock = None
        
    def handle_packet(self, packet):
        # todo handle json decoding error
        packet = json.loads(packet)
        print(packet)
        if packet.get("content", None) is not None:
            if self.message_callback is not None:
                self.message_callback(Message(packet["content"], None, Channel(self, "general")))

        if packet.get("command", None) is not None:
            if packet["command"] == "set":
                if packet["key"] == "self_uuid":
                    print("Your UUID =", packet["value"])

            else:
                print("Got weird command", packet)

    def send(self, message: str):
        self.ssock.send((message + "\n").encode("utf-8"))

    def run(self):
        context = ssl.SSLContext()

        with socket.create_connection((self.ip, self.port)) as sock:
            with context.wrap_socket(sock, server_hostname=self.ip) as ssock:
                self.ssock = ssock
                print(ssock.version())
                if self.uuid is None:
                    ssock.send(b"/register\n")
                else:
                    ssock.send((f"/login {self.uuid}\n").encode("utf-8"))
                ssock.send((f"/nick {self.username}\n/passwd {self.password}\n").encode("utf-8"))
                total_data = b""
                while True:
                    total_data += ssock.recv(1024)
                    if b"\n" in total_data:
                        data = total_data.decode("utf-8").split("\n")
                        total_data = ("\n".join(data[1:])).encode("utf-8")
                        self.handle_packet(data[0])
