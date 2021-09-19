import asterpy
client = asterpy.Client("cospox.com", 2345, "jamsbot", "", 1284344576730345505)

def on_message(message):
    print(message.content)

client.message_callback = on_message
client.run()
