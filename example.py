import src.asterpy as asterpy
import base64
import asyncio
# client = asterpy.Client("KingJellyfish", "")
# client.add_server("127.0.0.1", 2345, uuid=2286544141188136)

client = asterpy.Client("KingJellyfishTwo", "asdf")
client.add_server("cospox.com", 2345)
# client.add_server("cospox.com", 2346)

# @client.event
# async def on_packet(packet):
#     print(packet)

@client.event
async def on_message(message):
    # await message.channel.send(message.content + " asdf")
    print(message)


@client.event
async def on_ready():
    print("Ready!")
    channel = client.get_channel_by_name("general")
    reply_to = (await channel.fetch_history(count=1))[0]
    await reply_to.reply("This is a message reply")

    replied = (await channel.fetch_history(count=1))[0]
    print(replied)
    
    # channel = client.get_channel_by_name("general")
    # for i in range(10):
    #     message = await channel.send("hello world")
    # while (message := await channel.fetch_history(count=1))[0].content == "hello world":
    #     await message[0].delete()
    print("done")
#     message = await channel.send("""test
# 🟦🟦🟦🟦🟦🟦🟦🟦
# 🟦🟦🟦🟦🟨🟨🟦🟦
# 🟦🟦🟦🟨🟩🟨🟦🟦
# 🟦🟦🟨🟨🟩🟨🟦🟦
# 🟦🟦🟨🟩🟩🟨🟨🟨
# 🟦🟨🟨🟩🟩🟩🟩🟨
# 🟨🟨🟩🟩🌄🌄🟩🟩
# 🟩🟩🟩🟩🌄🌄🏔️🟩
# """)
    # await message.delete()
    # await message.edit("goodbye world")
    # latest_history = await client.fetch_history(client.get_channel_by_name("general"), count=10)
    # earlier_history = await client.fetch_history(client.get_channel_by_name("general"), count=10, init_message=latest_history[0])
    # total_history = await client.fetch_history(client.get_channel_by_name("general"), count=20)

    # for message in earlier_history:
    #     print(message.author.username + ": " + message.content)
    # for message in latest_history:
    #     print(message.author.username + ": " + message.content)
    # print("\n\n\n")
    # for message in total_history:
    #     print(message.author.username + ": " + message.content)
client.run()
