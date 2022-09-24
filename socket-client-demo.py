import asyncio
import websockets
import time
import json


async def hello():
    async with websockets.connect("ws://localhost:8000/subscribe/state") as websocket:
        while True:
            body = {
                "cookie": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6InVzZXJAZW1haWwuY29tIn0.7mjI9LuSrRs_HCsQsbxueMjOCTP_7Z3-eXtZhGYKSAs",
                "workstation": "testworkstation",
            }
            await websocket.send(json.dumps(body))
            message = await websocket.recv()
            print(message)


asyncio.run(hello())
