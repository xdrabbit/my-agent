#!/usr/bin/env python3
"""Optional live demo showing the websocket handshake to OpenAI Realtime.

WARNING: This script will attempt to establish a real websocket connection to
the OpenAI Realtime endpoint. It does NOT send audio frames — it demonstrates
the handshake. Only run if you understand the network implications and you
trust the API key in `.env.local`.

Usage:
  PYTHONPATH=./src python scripts/demo_openai_live.py

This script loads `.env.local` (if present) and requires OPENAI_API_KEY to be set.
It is intended for manual use only, and will not be executed from tests or CI.
"""
import asyncio
import os
from dotenv import load_dotenv

from nyra_realtime.openai_transport import make_openai_ws_factory


async def main():
    # load local .env safely
    load_dotenv(".env.local", override=False)
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY is not set in the environment (.env.local). Aborting.")
        return

    factory = make_openai_ws_factory(key)

    print("Attempting websocket handshake to OpenAI realtime endpoint...")
    try:
        ws = await factory()
        # if connect succeeded, show a short confirmation then close
        print("Connected — remote websocket handshake succeeded (no data sent).")
        await ws.close()
        print("Closed connection.")
    except Exception as exc:
        print("Connection failed:", type(exc).__name__, str(exc))


if __name__ == "__main__":
    asyncio.run(main())
