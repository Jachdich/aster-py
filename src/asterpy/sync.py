from typing import List

class SyncServer:
    """
    Represents a server entry in the SyncData. 
    """
    def __init__(self, ip: str, port: int, name: str, pfp: bytes, uuid: int):
        #TODO figure out if these types are correct
        self.ip = ip
        self.port = port
        self.name = name
        #: PNG-compressed image data
        self.pfp = pfp
        self.uuid = uuid

    def from_json(value: dict):
        """
        Create a SyncServer from an entry in the ``sync_get_servers`` packet.
        
        :param value: The entry to deserialise.
        :rtype: SyncServer
        """
        return SyncServer(
            value["ip"],
            value["port"],
            value.get("name", ""),
            value.get("pfp", ""),
            value["user_uuid"]
        )

class SyncData:
    """
    Represents the data used to sync an aster account across multiple devices.
    This data can be stored on any aster server which the user designates their sync server.
    It contains information such as the current username, profile picture, and server list so they can be consistant across clients.
    """
    def __init__(self, uname: str, pfp: str, servers: List[SyncServer]):
        self.uname = uname
        self.pfp = pfp
        self.servers = servers

    def from_json(value: dict, servers: dict):
        """
        Create a SyncData object from a ``sync_get`` packet and a ``sync_get_servers`` packet.
        
        :param value: A dictionary containing sync data.
        :param servers: A dictionary containing a list of sync server data.
        :returns: The SyncData object, or ``None`` if the packet's status is 404 (no sync data on the server).
        :rtype: Optional[SyncData]
        """
        if value["status"] == 200:
            return SyncData(
                value["uname"],
                value["pfp"],
                [SyncServer.from_json(val) for val in servers["servers"]]
            )
        elif value["status"] == 404:
            # no sync data
            return None