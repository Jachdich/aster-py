import src.asterpy as asterpy
# client = asterpy.Client("127.0.0.1", 2345, "jamsbot", "", 1284344576730345505)
client = asterpy.Client("cospox.com", 2345, "jamsbot", "", 1284344576730345505)

@client.event
def on_message(message):
    message.channel.send(message.content + " asdf")

@client.event
def on_packet(packet):
    print(packet)

@client.event
def on_ready():
    print("Ready!")
    pfp = client.get_pfp(4295143242865525747)
    with open("test_pfp.png", "wb") as f:
        f.write(pfp)
    
    client.send({"command": "ping"})


client.run()
