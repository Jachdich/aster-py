import src.asterpy as asterpy
import base64
import asyncio
# client = asterpy.Client("KingJellyfish", "")
# client.add_server("127.0.0.1", 2345, uuid=2286544141188136)

client = asterpy.Client("newacct", "a")
client.add_server("localhost", 2345, uuid=4645705226395143)

# @client.event
# async def on_packet(packet):
#     print(packet)

responses_pending = {}
lock = asyncio.Condition()

async def get_response(ctx: asterpy.Message):
    async with lock:
        responses_pending[(ctx.author.uuid, ctx.channel.uuid)] = None
        while responses_pending[(ctx.author.uuid, ctx.channel.uuid)] is None:
            await lock.wait()

    response = responses_pending[(ctx.author.uuid, ctx.channel.uuid)]
    del responses_pending[(ctx.author.uuid, ctx.channel.uuid)]
    return response

@client.event
async def on_message(message):
    # await message.channel.send(message.content + " asdf")
    for author_id, channel_id in responses_pending:
        if message.author.uuid == author_id and message.channel.uuid == channel_id:
            print("got the message")
            responses_pending[(author_id, channel_id)] = message
            async with lock:
                lock.notify()

    if message.content == "thing":
        await thing(message)

async def thing(ctx):
    await ctx.channel.send("are u shure (y/n)")
    res = None
    while res is None:
        response = await get_response(ctx)
        if response.content.lower() in ["y", "n"]:
            res = response.content.lower()

    await ctx.channel.send("ok you responded with " + res)

@client.event
async def on_ready():
    print("Ready!")
    channel = client.get_channel_by_name("general")
    message = await channel.send("hello world")
    await message.edit("goodbye world")
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
