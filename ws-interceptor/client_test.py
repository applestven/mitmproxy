import asyncio
import websockets
import random

URI = "ws://127.0.0.1:8765"


async def test():

    async with websockets.connect(URI) as ws:

        while True:

            # 模拟正常包
            normal = b"hello_" + random.randbytes(4)

            # 模拟目标包
            special = bytes.fromhex("65 00 e6 01 02 03")

            await ws.send(normal)
            print("send normal:", normal.hex())

            await asyncio.sleep(1)

            await ws.send(special)
            print("send special:", special.hex())

            await asyncio.sleep(2)


asyncio.run(test())