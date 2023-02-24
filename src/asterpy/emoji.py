from typing import Dict, Any

class Emoji:
    """Represents a custom emoji"""
    def __init__(self, name: str, uid: int, data: str):
        self.data = data
        self.name = name
        self.uid = uid

    def from_json(value: Dict[str, Any]):
        """
        Create a new Emoji given a dictionary.

        :param value: The dictionary to construct from.
        """
        return Emoji(value["name"], value["uuid"], value["data"])
