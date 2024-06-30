from .message import Message

class Channel:
    """
    Represents an aster channel.
    """
    def __init__(self, client, name: str, uuid: int):
        self.client = client
        self.name = name
        self.uuid = uuid

    async def send(self, message: str):
        """
        Send a text message to the channel.

        :param message: The text to be sent
        :returns: The ``Message`` object that has been sent
        """
        response = await self.client.get_response({"command": "send", "content": message, "channel": self.uuid})
        # TODO handle status
        # TODO this is stupid. handle this properly
        return Message(message, None, self, None, response["message"])

    def to_json(self) -> dict:
        return {"name": self.name, "uuid": self.uuid}
