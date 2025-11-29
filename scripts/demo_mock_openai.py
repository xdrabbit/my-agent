#!/usr/bin/env python3
"""Small demo showing use of OpenAIRealtimeManager with a mock websocket.

This is a safe, local demo that does NOT use your real OpenAI API key. It shows
how the manager is constructed, how to queue audio bytes, and how to receive
voice frames produced by a remote endpoint.

If you want to wire a real OpenAI Realtime websocket, follow the comments at
the bottom of the file — do NOT paste your API key into logs or command output.
"""
import asyncio
import os
from dotenv import load_dotenv
from nyra_realtime.openai_manager import OpenAIRealtimeManager


class MockWS:
    """A minimal websocket-like object used for local demos/tests."""

    def __init__(self):
        self._recv_q = asyncio.Queue()
        self.send_buffer = []

    async def send(self, payload: bytes):
        # pretend to send; push into an internal buffer for inspection
        await asyncio.sleep(0)
        self.send_buffer.append(payload)

    async def recv(self):
        # await an item supplied by the demo task
        return await self._recv_q.get()

    async def close(self):
        # demo-only: no real resource to close
        return

    # helper
    async def push_recv(self, data: bytes):
        await self._recv_q.put(data)


async def run_demo():
    ws = MockWS()

    async def factory():
        # This factory creates and returns a websocket-like object.
        # In production you'd return an actual websocket client instance.
        return ws

    # Load .env.local if present; this keeps secrets out of the repo while making
    # the demo convenient for local development. load_dotenv does NOT print
    # values and will not overwrite already-set environment variables.
    load_dotenv(".env.local", override=False)

    mgr = OpenAIRealtimeManager(api_key=os.getenv("OPENAI_API_KEY"), ws_factory=factory)

    print("Connecting to mock OpenAI realtime manager (local demo, no network used)")
    await mgr.connect()

    # schedule background task that simulates remote TTS after a short delay
    async def remote_tts():
        await asyncio.sleep(0.05)
        await ws.push_recv(b"mock-tts-frame-1")
        await asyncio.sleep(0.03)
        await ws.push_recv(b"mock-tts-frame-2")

    asyncio.create_task(remote_tts())

    # send some audio into the manager
    await mgr.send_audio(b"pcm-frame-1")
    await mgr.send_audio(b"pcm-frame-2")

    # receive the two mock TTS frames
    a = await mgr.receive_voice(timeout=1.0)
    print("received:", a)
    b = await mgr.receive_voice(timeout=1.0)
    print("received:", b)

    # cleanup
    await mgr.disconnect()


if __name__ == "__main__":
    asyncio.run(run_demo())

# --------------------------
# Notes for wiring real OpenAI realtime transport
# --------------------------
# To connect to OpenAI's realtime websocket instead of the local MockWS, you
# would replace the `factory()` above with one that uses a real websocket
# client (for example the `websockets` package). Important points:
#  - Do not print environment variables or API keys to stdout/stderr.
#  - Construct the auth headers carefully: Authorization: Bearer <OPENAI_API_KEY>
#  - Use the official message formats for streaming audio and TTS responses.
#  - The manager's queues will keep your code testable — pass a factory that
#    returns a websocket object implementing async send/recv/close.
