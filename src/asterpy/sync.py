class SyncServer:
    def __init__(self, ip, port, name, pfp, uuid):
        self.ip = ip
        self.port = port
        self.uname = uname
        self.pfp = pfp
        self.uuid = uuid

    def from_json(value):
        return SyncServer(
            value["ip"],
            value["port"],
            value.get("name", ""),
            value.get("pfp", ""),
            value["uuid"]
        )

class SyncData:
    def __init__(self, uname, pfp, servers):
        self.uname = uname
        self.pfp = pfp
        self.servers = servers

    def from_json(value, servers):
        return SyncData(
            value["uname"],
            value["pfp"],
            [SyncServer.from_json(val) for val in servers["data"]]
        )
