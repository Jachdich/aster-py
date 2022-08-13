from packets import ContentPacket

class Channel:
    """a channel. Shut up pylint"""
    def __init__(self, client, name, uuid):
        self.client = client
        self.name = name
        self.uuid = uuid

    def send(self, message: str):        
        self.client.send(ContentPacket(message, self))

    def to_json(self):
        return {"name": self.name, "uuid": self.uuid}
