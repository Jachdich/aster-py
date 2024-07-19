"""Simple python wrapper for controlling an aster account"""

import socket
import ssl
import json
import threading
import base64
import asyncio
import random
from typing import *
from .user import User
from .channel import Channel
from .message import Message
from .sync import SyncData, SyncServer
from .emoji import Emoji
from .server import Server
from .client import Client

def fetch_emoji(emoji):
    #emojis of the form <:cospox.com:3245:69420:>
    bits = emoji.split(":")
    if len(bits) != 5:
        raise RuntimeError("Emoji not in correct form!")
    if bits[0] != "<" or bits[-1] != ">":
        raise RuntimeError("Emoji not in correct form!")

    ip = bits[1]
    port = int(bits[2])
    uuid = int(bits[3])

    client = Client(ip, port, "", "", login=False)
    async def on_ready():
        #TODO weird hack
        client.username = await client.fetch_emoji(uuid)
        await client.disconnect()
    client.on_ready = on_ready
    try:
        client.run()
    except OSError: #connection failed for some reason
        return None
    return client.username

def fetch_pfp(ip, port, uuid):
    client = Client(ip, port, "", "", login=False)
    async def on_ready():
        #TODO weird hack
        client.username = await client._fetch_pfp(uuid)
        await client.disconnect()
    client.on_ready = on_ready
    try:
        client.run()
    except OSError: #connection failed for some reason
        return None
    return client.username
