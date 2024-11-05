from __future__ import annotations
from .message import Message
from .error import AsterError

class Channel:
    """
    Represents an aster channel.
    """
    def __init__(self, client, name: str, uuid: int):
        self.client = client
        self.name = name
        self.uuid = uuid

    async def send(self, message: str, reply_to: int | None=None):
        """
        Send a text message to the channel.

        :param message: The text to be sent
        :param reply_to: The UUID of the message to reply to, or ``None`` if not replying.
        :returns: The ``Message`` object that has been sent
        """
        packet = {"command": "send", "content": message, "channel": self.uuid}
        if reply_to is not None:
            packet["reply"] = reply_to
        response = await self.client.get_response(packet)
        # TODO handle status
        # TODO this is stupid. handle this properly
        if response["status"] != 200:
            raise AsterError(f"Message send failed with code {response['status']}")
        return Message(message, None, self, None, self.client, response["message"])

    async def fetch_history(self, count: int=100, init_message: Message=None) -> list[Message]:
        """
        Fetch the last ``count`` messages from a given channel.

        :param channel: The channel from which to fetch the messages.
        :param count: The number of messages to fetch. (defeault: 100)
        :param init_message: Fetch ``count`` messages before this message. If init_message == None, then fetch the last ``count`` messages.
        :returns: A list of messages.
        """
        request = {"command": "history", "num": count, "channel": self.uuid}
        if init_message is not None:
            request["before_message"] = init_message.uuid
            
        packet = await self.client.get_response(request)
        return [Message(elem["content"], self.client.peers[elem["author_uuid"]], self, self.client, elem["date"], elem["uuid"], reply_uuid=elem.get("reply", None)) for elem in packet["data"]]

    def to_json(self) -> dict:
        return {"name": self.name, "uuid": self.uuid}
