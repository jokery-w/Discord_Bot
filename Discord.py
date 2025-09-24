import asyncio
import aiohttp
import json
import websockets
from datetime import datetime, timedelta

#0.________________________________
base_discord = "https://discord.com/api/v10"
gateway_url = f"{base_discord}/gateway/bot"
bot_token = "Add bot token"
Header = {
    "Authorization": f"Bot {bot_token}",
    "Content-Type": "application/json"
}

class Bad:
    def __init__(self):
        self.bad_words = ["a"]

async def message_fetch(channel_id, message_id, guild_id, user_id):
    bad = Bad()
    url = f"{base_discord}/channels/{channel_id}/messages/{message_id}"
    async with aiohttp.ClientSession() as call:
        async with call.get(url, headers=Header) as response:
            if response.status != 200:
                print("there was a bug in the delete message (fix it please) def(message_fetcher)")
                return
            message_data = await response.json()
            content = message_data.get("content", "").lower()

            if any(word in content for word in bad.bad_words):
                async with call.delete(url, headers=Header) as delete_respond:
                    if delete_respond.status == 204:
                        print(f" Deleted message {message_id} for bad content.")
                    else:
                        print("there was a bug in the delete message (fix it please) def(message_fetcher) 2")
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_discord}/users/@me", headers=Header) as bot_res:
                        bot_data = await bot_res.json()
                        bot_power = bot_data["id"]
                    mute_users = await check_role_hierarchy(bot_power, user_id, guild_id, session, Header)
                    if mute_users:
                        await mute(guild_id, user_id, reason="Used prohibited word")
                    else:
                        print("🚫 Cannot mute — target has higher role.")

async def mute(guild_id, user_id, reason="use bad lang"):
    timeout_until = (datetime.utcnow() + timedelta(seconds=5)).isoformat() + "Z"
    payload = {"communication_disabled_until": timeout_until}
    url = f"{base_discord}/guilds/{guild_id}/members/{user_id}"
    headers = Header.copy()
    headers["X-Audit-Log-Reason"] = reason
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=payload, headers=headers) as response:
            if response.status == 200:
                print(f"{user_id} was muted for reason: {reason}")
                await asyncio.sleep(5)

async def check_role_hierarchy(bot_id, target_id, guild_id, session, headers):
    bot_res = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}/members/{bot_id}", headers=headers)
    target_res = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}/members/{target_id}",headers=headers)
    bot_role = (await bot_res.json()).get("roles", [])
    target_role = (await target_res.json()).get("roles", [])

    roles_res = await session.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers=headers)
    all_roles = await roles_res.json()
    role_position = {role["id"]: role["position"] for role in all_roles}
    bot_max = max([role_position.get(r, -1) for r in bot_role], default=-1)
    target_max = max([role_position.get(r, -1) for r in target_role], default=-1)

    return bot_max > target_max


async def discord_fetch():
    async with aiohttp.ClientSession() as fetcher:
        async with fetcher.get(gateway_url, headers=Header) as discord_start:
            data = await discord_start.json()
            return data["url"]

async def heartbeat(ws, interval):
    while True:
        await asyncio.sleep(interval / 1000)
        await ws.send(json.dumps({"op": 1, "d": None}))

async def identify(ws):
    payload = {
        "op": 2,
        "d": {
            "token": bot_token,
            "intents": 3276799,
            "properties": {
                "$os": "linux",
                "$browser": "my_library",
                "$device": "my_library"
            }
        }
    }
    await ws.send(json.dumps(payload))

async def chatty_heart_beat():
    bot = await discord_fetch()
    ws = await websockets.connect(bot)
    hello_raw = await ws.recv()
    hello = json.loads(hello_raw)
    interval = hello["d"]["heartbeat_interval"]
    asyncio.create_task(heartbeat(ws, interval))
    await identify(ws)

    while True:
        msg = await ws.recv()
        data = json.loads(msg)
        print("📨 Event:", data)
        if data.get("t") == "MESSAGE_CREATE":
            d = data["d"]
            channel_id = d["channel_id"]
            message_id = d["id"]
            guild_id = d["guild_id"]
            user_id = d["author"]["id"]

            await message_fetch(channel_id, message_id, guild_id, user_id)

asyncio.run(chatty_heart_beat())
