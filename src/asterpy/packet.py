import json

class Packet:
    def __init__(self, data: dict):
        self.data = data
    def __str__(self):
        return json.dumps(self.data)

class ContentPacket(Packet):
    def __init__(self, content: str, channel: Channel):
        super().__init__({"command": "content", "content": content, "channel": channel.uuid})

class LeavePacket(Packet):
    def __init__(self): super().__init__({"command": "leave"})
