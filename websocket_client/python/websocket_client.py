import asyncio
import json
import logging

import websockets

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("websocket_server")

PORT = 9001
HOST = "127.0.0.1"


async def websocket_handler(websocket, path=None):
    client_address = websocket.remote_address
    logger.info(f"Client connected from {client_address}")
    if path:
        logger.info(f"  Requested path: {path}")

    try:
        async for message in websocket:
            logger.info(f"Received message from {client_address}:")
            try:
                json_data = json.loads(message)
                logger.info(f"  (JSON) {json.dumps(json_data, indent=2)}")
            except json.JSONDecodeError:
                logger.info(f"  (Text) {message}")

    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"Client {client_address} disconnected cleanly.")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.error(f"Client {client_address} disconnected with error: {e}")
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred with client {client_address}: {e}"
        )
    finally:
        logger.info(f"Client {client_address} handler finished.")


async def main():
    logger.info(f"Starting WebSocket server on ws://{HOST}:{PORT}")
    async with websockets.serve(websocket_handler, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
