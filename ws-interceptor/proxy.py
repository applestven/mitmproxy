import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO)

TARGET_PREFIX = bytes.fromhex("65 00 e6")

UPSTREAM = "ws://118.178.109.182:6082/ws?playerId=129244"


async def handler(client_ws):

    try:
        async with websockets.connect(UPSTREAM) as server_ws:

            async def c2s():
                try:
                    async for msg in client_ws:
                        data = msg if isinstance(msg, bytes) else msg.encode()

                        logging.info(f"[C->S] {data.hex()}")

                        if data.startswith(TARGET_PREFIX):
                            logging.warning(f"DROP PACKET: {data.hex()}")
                            continue

                        await server_ws.send(msg)

                except Exception as e:
                    logging.warning(f"c2s closed: {e}")

            async def s2c():
                try:
                    async for msg in server_ws:
                        data = msg if isinstance(msg, bytes) else msg.encode()

                        logging.info(f"[S->C] {data.hex()}")

                        await client_ws.send(msg)

                except Exception as e:
                    logging.warning(f"s2c closed: {e}")

            task1 = asyncio.create_task(c2s())
            task2 = asyncio.create_task(s2c())

            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_EXCEPTION
            )

            for task in pending:
                task.cancel()

    except Exception as e:
        logging.error(f"connection error: {e}")


async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    logging.info("WS Proxy running on ws://127.0.0.1:8765")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())