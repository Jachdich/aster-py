from base64 import b64decode
from typing import Optional

class User:
    """Represents a user on the aster server"""
    def __init__(self, uuid: int, username: str, pfp: Optional[bytes]=None):
        self.uuid = uuid
        self.username = username
        #: PNG-compressed image data
        self.pfp = pfp

    def from_json(json):
        pfp_b64 = json.get("pfp", None)
        pfp = None
        if pfp_b64 is not None:
            pfp = b64decode(pfp_b64)
        return User(json["uuid"], json["name"], pfp)

    def update_from_json(self, json):
        pfp_b64 = json.get("pfp", None)
        pfp = None
        if pfp_b64 is not None:
            pfp = b64decode(pfp_b64)

        if pfp is not None: self.pfp = pfp
        if json.get("uuid") is not None: self.uuid = json["uuid"]
        if json.get("name") is not None: self.username = json["name"]
