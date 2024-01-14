import src.asterpy as asterpy
import base64
import asyncio
# client = asterpy.Client("127.0.0.1", 2345, "jamsbot", "", 1284344576730345505)
# client = asterpy.Client("cospox.com", 2345, "jamsbot", "", 1284344576730345505)
client = asterpy.Client("KingJellyfish", "")
client.add_server("127.0.0.1", 2345, uuid=2286544141188136)

@client.event
async def on_message(message):
    await message.channel.send(message.content + " asdf")

@client.event
async def on_packet(packet):
    print(packet)

@client.event
async def on_ready():
    print("Ready!")
    latest_history = await client.fetch_history(client.get_channel_by_name("general"), count=10)
    earlier_history = await client.fetch_history(client.get_channel_by_name("general"), count=10, init_message=latest_history[0])
    total_history = await client.fetch_history(client.get_channel_by_name("general"), count=20)

    for message in earlier_history:
        print(message.author.username + ": " + message.content)
    for message in latest_history:
        print(message.author.username + ": " + message.content)
    print("\n\n\n")
    for message in total_history:
        print(message.author.username + ": " + message.content)
client.run()
