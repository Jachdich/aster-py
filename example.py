import src.asterpy as asterpy
client = asterpy.Client("127.0.0.1", 2345, "jamsbot", "", 1284344576730345505)

@client.event
def on_message(message):
    message.channel.send(message.content + " asdf")

@client.event
def on_packet(packet):
    print(packet)

@client.event
def on_ready():
    print("Ready!")
    client.send({"command": "ping"})


client.run()
