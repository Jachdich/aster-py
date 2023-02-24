from typing import Dict, Any

class Emoji:
    """Represents a custom emoji"""
    def __init__(self, name: str, uid: int, data: bytes):
        #: PNG-compressed image data as bytes.
        self.data = data
        self.name = name
        self.uid = uid

    def from_json(value: Dict[str, Any]):
        return Emoji(value["name"], value["uuid"], value["data"])
