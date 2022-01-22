import asterpy
client = asterpy.Client("cospox.com", 2345, "jamsbot", "", 1284344576730345505)

@client.event
def on_message(message):
    message.channel.send(message.content + " asdf")

@client.event
def on_ready():
    print("Ready!")

client.run()
