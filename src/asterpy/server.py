class Server:
    """Represents an aster server"""
    def __init__(self, ip, port, username, password, uuid=None):
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        # in theory, a server is uniquely identified by its IP and port. However, due to DNS, "example.com:2345" will show up
        # as a different server to "123.45.67.89:2345" even if they are the same server.
        # I am not sure if this is a problem or not.
        self.uid = hash((self.ip, self.port))
        self.self_uuid = 0
        self.channels = []
        self.peers = {}
        self.initialised = False
