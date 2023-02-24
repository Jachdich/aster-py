class Channel:
    """
    Represents an aster channel.
    """
    def __init__(self, client, name: str, uid: int):
        self.client = client
        self.name = name
        self.uid = uid

    def send(self, message: str):
        """
        Send a text message to the channel.

        :param message: The text to be sent
        """
        self.client.send({"command": "send", "content": message, "channel": self.uid})

    def to_json(self) -> dict:
        return {"name": self.name, "uuid": self.uid}
