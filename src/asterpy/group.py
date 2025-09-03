from .permissions import Permissions

class Group:
    """Represents an aster group"""
    uuid: int
    #: Permissions to apply to users in this group.
    permissions: Permissions
    #: Position in the list of groups. Top group is 0, increasing downwards. There should not be any gaps or duplicate positions.
    position: int
    #: Name of the group
    name: str
    #: Colour, as 24-bit RGB that members of the group are associated with
    colour: int
    def __init__(self,
        uuid: int,
        permissions: Permissions,
        position: int,
        name: str,
        colour: int):
        self.uuid = uuid
        self.permissions = permissions
        self.position = position
        self.name = name
        self.colour = colour

    def to_json(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "permissions": self.permissions.to_array(),
            "colour": self.colour,
            "position": self.position
        }
