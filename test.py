responses_pending = {}

async def get_response(client, ctx: asterpy.Message):
	lock = asyncio.Condition()
    async with lock:
        print("acquired")
        responses_pending[(ctx.author.uuid, ctx.channel.uid)] = [lock, None]
        while responses_pending[(ctx.author.uuid, ctx.channel.uid)][1] is None:
            print("waiting...")
            await lock.wait()
        print("after while")

    return responses_pending[(ctx.author.uuid, ctx.channel.uid)][1]

@client.event
async def on_message(message):
    for author_id, channel_id in responses_pending:
        if message.author.uuid == author_id and message.channel.uid == channel_id:
			print("got the message")
            responses_pending[(author_id, channel_id)][1] = message
            responses_pending[(author_id, channel_id)][0].notify()
            del responses_pending[(author_id, channel_id)]


"""
acquired
waiting...
got the message
Task exception was never retrieved
future: <Task finished name='Task-5' coro=<on_message() done, defined at /home/james/Build/aster/asterpy/example.py:27> exception=RuntimeError('cannot notify on un-acquired lock')>
Traceback (most recent call last):
  File "/home/james/Build/aster/asterpy/example.py", line 33, in on_message
    lock.notify()
  File "/usr/local/lib/python3.11/asyncio/locks.py", line 311, in notify
    raise RuntimeError('cannot notify on un-acquired lock')
RuntimeError: cannot notify on un-acquired lock
"""