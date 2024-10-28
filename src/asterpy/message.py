from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import User
    from .server import Server

class Message:
    """Represents a message in a channel on the server"""
    # TODO importing Channel to use as a type hint causes circular imports
    def __init__(self, content: str, user: User, channel, server: Server, date: int, uuid: int):
        self.content = content
        self.author = user
        self.channel = channel
        self.server = server
        #: UNIX timestamp
        self.date = date
        self.uuid = uuid

    async def edit(self, new_content: str):
        """
        Edit a message. The message must have been sent by the account attempting to edit it.

        :param new_content: The new body text of the message.
        """
        await self.channel.client.send({"command": "edit", "message": self.uuid, "new_content": new_content})

    async def delete(self):
        """Delete this message. This message must be sent by the account that's deleting it."""
        await self.channel.client.send({"command": "delete", "message": self.uuid})

    def to_json(self):
        return {"content": self.content, "author_uuid": self.author.uuid, "date": self.date}
    
    def __repr__(self):
        return f"Message({self.content}, {self.author}, {self.channel}, {self.date}, {self.uuid})"
