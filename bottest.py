import asterpy
client = asterpy.Client("cospox.com", 2345, "jamsbot", "", None)

def on_message(message):
    print(message.content)

client.message_callback = on_message
client.run()