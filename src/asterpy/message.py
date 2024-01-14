from .user import User
from .channel import Channel

class Message:
    """Represents a message in a channel on the server"""
    def __init__(self, content: str, user: User, channel: Channel, date: int, uuid: int):
        self.content = content
        self.author = user
        self.channel = channel
        #: UNIX timestamp
        self.date = date
        self.uuid = uuid

    def to_json(self):
        return {"content": self.content, "author_uuid": self.author.uuid, "date": self.date}
    
    def __repr__(self):
        return f"Message({self.content}, {self.author}, {self.channel}, {self.date}, {self.uuid})"
