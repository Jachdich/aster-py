from .user import User

class Message:
    """Represents a message in a channel on the server"""
    # TODO importing Channel to use as a type hint causes circular imports
    def __init__(self, content: str, user: User, channel, date: int, uuid: int):
        self.content = content
        self.author = user
        self.channel = channel
        #: UNIX timestamp
        self.date = date
        self.uuid = uuid

    async def edit(self, new_content: str):
        await self.channel.client.send({"command": "edit", "message": self.uuid, "new_content": new_content})

    def to_json(self):
        return {"content": self.content, "author_uuid": self.author.uuid, "date": self.date}
    
    def __repr__(self):
        return f"Message({self.content}, {self.author}, {self.channel}, {self.date}, {self.uuid})"
