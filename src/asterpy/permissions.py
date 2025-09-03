from dataclasses import dataclass
from typing import Self

Perm = bool | None

@dataclass
class UserUuid:
    """The UUID represents a user"""
    uuid: int

@dataclass
class GroupUuid:
    """The UUID represents a group"""
    uuid: int

Permable = UserUuid | GroupUuid

def int_to_perm(i: int) -> Perm:
    if i == 0: return None
    if i == 1: return True
    if i == 2: return False
def perm_to_int(p: Perm) -> int:
    if i == None: return 0
    if i == True: return 1
    if i == False: return 2

def byte_to_perms(b: int) -> list[Perm]:
    return [
        int_to_perm((b >> 0) & 0b11),
        int_to_perm((b >> 2) & 0b11),
        int_to_perm((b >> 4) & 0b11),
        int_to_perm((b >> 6) & 0b11),
    ]

def perms_to_byte(p: list[Perm]) -> int:
    (perm_to_int(p[0]) << 0) \
        | (perm_to_int(p[1]) << 2)\
        | (perm_to_int(p[2]) << 4)\
        | (perm_to_int(p[3]) << 6)

@dataclass
class Permissions:
    """Represents the permissions associated with a user, group, or channel.
    Each element can be either ``True``, ``False``, or ``None``; with None represeng
    a "default" that takes its value from the previous level in the hierarchy.
    The permissions hierarchy is roughly that more specific permissions override
    less specific.
    
    - Server default permissions
    - Permissions assigned to a user's groups, in order
    - Permissions that apply to a user or group in a specific channel"""

    #: Create or edit channels, including moving them up/down and changing the group/user specific permissions.
    modify_channels: Perm
    #: Update the icon or name of the server.
    modify_icon_name: Perm
    #: Create or edit groups and their permissions. Only groups below (i.e. a greater position) the user's highest group are able to be modified.
    modify_groups: Perm
    #: Add or remove groups from users.
    modify_user_groups: Perm
    #: Add or remove users from the ban list.
    ban_users: Perm
    #: Send messages to a channel.
    send_messages: Perm
    #: Receive messages and read the history of a channel.
    read_messages: Perm
    #: Delete other user's messages. Note that a user may always delete their own messages.
    manage_messaes: Perm
    #: Join a voice channel and transmit audio.
    join_voice: Perm
    #: Be able to see a channel in the channel list.
    view_channel: Perm

    @staticmethod
    def from_array(b: list[int]) -> Self:
        """Create a :py:class:`Permissions` object from a serialised array of bytes"""
        perms = sum([byte_to_perms(i) for i in b], [])
        if len(perms) > 10:
            perms = perms[:10]
        return Permissions(*perms)

    def to_array(self):
        """Serialise into an array of bytes"""
        return [
            perms_to_byte([
                self.modify_channels,
                self.modify_icon_name,
                self.modify_groups,
                self.modify_user_groups,
            ]),
            perms_to_byte([
                self.ban_users,
                self.send_messages,
                self.read_messages,
                self.manage_messages,
            ]),
            perms_to_byte([
                self.join_voice,
                self.view_channel,
                None,
                None,
            ]),
        ]
