
from assert_eq import assert_eq
import src.asterpy as asterpy
async def test_forbid_add_channel(client: asterpy.Client, login=True):
    # register_response = await client.servers[0].get_response({"command": "register", "uname": "KingJellyfish", "passwd": "lol"})
    try:
        channel = await client.servers[0].create_channel("hello")
        assert False, "Creating channel succeeded when should have been forbidden"
    except asterpy.AsterError as e:
        assert_eq(e.args[0], "Creating channel failed. Code: 403")

async def test_add_channel(client: asterpy.Client):
    login_response = await client.servers[0].get_response({"command": "login", "uname": "god", "passwd": "god_password"})
    assert_eq(login_response["status"], 200)
    channel = await client.servers[0].create_channel("hello")
    assert channel is not None


# TODO!!!
# idk how to handle this
# should users have individual perms? how to, for testing, make one user get all perms?
# how to, in production, allow the server owner to give themselves perms?
# when channel is created, does it successfully return itself? jank, maybe return uuid in api
# update/delete channel methods
# create/update/delete group methods
# test all of the above
# document all of the above (actually just go through the whole project and document anything that isn't documented)
