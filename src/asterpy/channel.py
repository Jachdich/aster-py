from __future__ import annotations
from .message import Message
from .error import AsterError
from .permissions import Permable, Permissions

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .server import Server

class Channel:
    """
    Represents an aster channel.
    """

    _server: Server
    name: str
    uuid: int
    #: Position in the list of channels. Top channel is 0, increasing downwards. There should not be any gaps or duplicate positions.
    position: int
    #: Channel specific permissions. Each entry represents either a user or group, with the associated permission overrides for that entity.
    permissions: dict[Permable, Permissions]
    def __init__(self, server: Server, name: str, uuid: int, position: int, permissions: dict[Permable, Permissions]):
        self._server = server
        self.name = name
        self.uuid = uuid
        self.position = position
        self.permissions = permissions

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
        response = await self._server.get_response(packet)
        # TODO handle status
        # TODO this is stupid. handle this properly
        if response["status"] != 200:
            raise AsterError(f"Message send failed with code {response['status']}")
        return Message(message, None, self, None, self._server, response["message"])

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
            
        packet = await self._server.get_response(request)
        return [Message(elem["content"], self._server.peers[elem["author_uuid"]], self, self._server, elem["date"], elem["uuid"], reply_uuid=elem.get("reply", None)) for elem in packet["data"]]

    def to_json(self) -> dict:
        return {"name": self.name, "uuid": self.uuid, "position": self.position, "permissions": {k: v.to_array() for k, v in self.permissions.values()} }

    def from_json(data: dict[str, any], server: Server):
        return Channel(server, data["name"], data["uuid"], data["position"], {k: Permissions.from_array(v) for k, v in data["permissions"].items()})
