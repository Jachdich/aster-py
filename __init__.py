import socket
import ssl

class User:
    def __init__(self, uuid: int, username: str):
        self.uuid = uuid
        self.username = username

class Message:
    def __init__(self, content: str, user: User):
        self.content = content
        self.user = user

class Client:
    def __init__(self, ip: str, port: int, username: str, password: str, uuid=None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.uuid = uuid
        self.on_message = None

    def run(self):
        context = ssl.create_default_context()
        
        with socket.create_connection((self.ip, self.port)) as sock:
            with context.wrap_socket(sock, server_hostname=self.ip, verify=False) as ssock:
                print(ssock.version())
                while True:
                    sock.send("/get_name\n")
                    some_data = ssock.recv(1024)
                    print(some_data)