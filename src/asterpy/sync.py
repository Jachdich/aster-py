from typing import List

class SyncServer:
    def __init__(self, ip: str, port: int, name: str, pfp: str, uuid: int):
        #TODO figure out if these types are correct
        self.ip = ip
        self.port = port
        self.uname = name
        self.pfp = pfp
        self.uuid = uuid

    def from_json(value):
        return SyncServer(
            value["ip"],
            value["port"],
            value.get("name", ""),
            value.get("pfp", ""),
            value["user_uuid"]
        )

class SyncData:
    def __init__(self, uname: str, pfp: str, servers: list[SyncServer]):
        self.uname = uname
        self.pfp = pfp
        self.servers = servers

    def from_json(value, servers):
        if value["status"] == 200:
            return SyncData(
                value["uname"],
                value["pfp"],
                [SyncServer.from_json(val) for val in servers["servers"]]
            )
        elif value["status"] == 404:
            # no sync data
            return None