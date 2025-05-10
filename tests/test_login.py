from assert_eq import assert_eq
import src.asterpy as asterpy

# TODO maybe find a way to test built in register and login functions of asterpy
async def test_register(client: asterpy.Client):
    register_response = await client.servers[0].get_response({"command": "register", "uname": "KingJellyfish", "passwd": "lol"})
    assert_eq(register_response["status"], 200)

async def test_register_duplicate(client: asterpy.Client):
    register_response = await client.servers[0].get_response({"command": "register", "uname": "KingJellyfish", "passwd": "lol"})
    assert_eq(register_response["status"], 409)
    
async def test_register_while_logged_in(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uname": "KingJellyfish", "passwd": "lol"})
    register_response = await client.servers[0].get_response({"command": "register", "uname": "KingJellyfish", "passwd": "lol"})
    assert_eq(register_response["status"], 405)

async def test_login_while_logged_in(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uname": "KingJellyfish", "passwd": "lol"})
    login_response2 = await client.servers[0].get_response({"command": "login", "uname": "KingJellyfish", "passwd": "lol"})
    assert_eq(login_response2["status"], 405)

async def test_login(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uname": "KingJellyfish", "passwd": "lol"})
    assert_eq(login_response["status"], 200)

async def test_login_wrong_uuid(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uuid": 1356146981, "passwd": "lol"})
    assert_eq(login_response["status"], 404)

async def test_login_wrong_uname(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uname": "KingJellyfish_wrong", "passwd": "lol"})
    assert_eq(login_response["status"], 404)

async def test_login_uuid(client: asterpy.Client):
    client2 = asterpy.Client("KingJellyfish", "lol")
    client2.add_server("localhost", 2345, connect_mode=asterpy.ConnectionMode.LOGIN)
    uuid = 0
    @client2.event
    async def on_ready():
        nonlocal uuid
        uuid = client2.servers[0].self_uuid
        await client2.servers[0].disconnect()

    await client2.connect()
    login_response = await client.servers[0].get_response({"command": "login", "uuid": uuid, "passwd": "lol"})
    assert_eq(login_response["status"], 200)

async def test_login_wrong_pasword(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uname": "KingJellyfish", "passwd": "lmao"})
    assert_eq(login_response["status"], 403)
