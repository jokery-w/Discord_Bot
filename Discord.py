import asyncio
import aiohttp
import websockets
import json

#0.________________________________
base_discord = "https://discord.com/api/v10/gateway/bot"
get_way = f"{base_discord}/gateway/bot"
bot_token = "bot_token"
Header = {"Authorization": f"Bot {bot_token}"}


async def discord_fetch():
    async with aiohttp.ClientSession() as fetcher:
        async with fetcher.get(base_discord, headers=Header) as discord_start:
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



asyncio.run(chatty_heart_beat())