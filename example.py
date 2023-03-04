import src.asterpy as asterpy
import base64
import asyncio
# client = asterpy.Client("127.0.0.1", 2345, "jamsbot", "", 1284344576730345505)
# client = asterpy.Client("cospox.com", 2345, "jamsbot", "", 1284344576730345505)
client = asterpy.Client("KingJellyfish", "")
client.add_server("127.0.0.1", 2345, uuid=4682842401153303511)

@client.event
async def on_message(message):
    await message.channel.send(message.content + " asdf")

@client.event
async def on_packet(packet):
    print(packet)

@client.event
async def on_ready():
    print("Ready!")
    pfp = await client._fetch_pfp(4682842401153303511)
    print("got pfp")
    
    await client.send({"command": "ping"})

client.run()
