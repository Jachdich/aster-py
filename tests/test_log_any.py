from assert_eq import assert_eq
import src.asterpy as asterpy

async def test_get_user_by_name(client: asterpy.Client, login=True):
    usr = client.servers[0].get_user_by_name("KingJellyfish")
    assert usr is not None
    assert_eq(usr.username, "KingJellyfish")

async def test_metadata(client: asterpy.Client):
    response = await client.servers[0].get_response({"command": "get_metadata"})
    assert_eq(response["status"], 200)
    assert len(response["data"]) > 0
    data = response["data"][0]
    assert_eq(data["name"], "KingJellyfish")
    assert "password" not in data
    assert "pfp" in data
    assert "uuid" in data
