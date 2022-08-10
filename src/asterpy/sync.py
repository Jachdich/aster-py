class SyncServer:
    def __init__(self, ip: str, port: int, name: str, pfp: str, uuid: int):
        #TODO figure out if these types are correct
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
    def __init__(self, uname: str, pfp: str, servers):#: List[SyncServer]):
        self.uname = uname
        self.pfp = pfp
        self.servers = servers

    def from_json(value, servers):
        return SyncData(
            value["uname"],
            value["pfp"],
            [SyncServer.from_json(val) for val in servers["data"]]
        )
