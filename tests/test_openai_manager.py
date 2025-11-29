import asyncio
import time

from nyra_realtime.openai_manager import OpenAIRealtimeManager


class MockWebSocket:
    def __init__(self):
        self.send_buffer = []
        self.recv_queue = asyncio.Queue()
        self.closed = False

    async def send(self, data: bytes):
        # emulate a short send delay
        await asyncio.sleep(0)
        self.send_buffer.append(data)

    async def recv(self):
        # block until a message is available
        return await self.recv_queue.get()

    async def close(self):
        self.closed = True


def _sync_run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_connect_and_disconnect():
    ws = MockWebSocket()

    async def factory():
        return ws

    mgr = OpenAIRealtimeManager(api_key="ok", ws_factory=factory)
    _sync_run(mgr.connect())
    assert mgr.connected is True

    _sync_run(mgr.disconnect())
    assert mgr.connected is False


def test_send_and_receive():
    ws = MockWebSocket()

    async def factory():
        return ws

    mgr = OpenAIRealtimeManager(api_key="ok", ws_factory=factory)
    loop = asyncio.get_event_loop()

    async def scenario():
        await mgr.connect()
        # schedule a send
        await mgr.send_audio(b"hello")

        # allow sender loop to process
        await asyncio.sleep(0.01)
        # the mock websocket should have the frame
        assert ws.send_buffer and ws.send_buffer[0] == b"hello"

        # make the websocket produce a message
        await ws.recv_queue.put(b"tts-frame")
        data = await mgr.receive_voice(timeout=1.0)
        assert data == b"tts-frame"

        await mgr.disconnect()

    loop.run_until_complete(scenario())


def test_reconnect_behavior():
    # factory that fails twice then succeeds
    calls = {"n": 0}

    async def factory():
        calls["n"] += 1
        if calls["n"] <= 2:
            raise ConnectionError("simulated connect failure")
        return MockWebSocket()

    stop = asyncio.Event()
    mgr = OpenAIRealtimeManager(api_key="ok", ws_factory=factory, reconnect_backoff=[0.01, 0.01])

    async def runner():
        # run run_forever in background and stop after a short window
        task = asyncio.create_task(mgr.run_forever(stop))
        # give it time to attempt connects
        await asyncio.sleep(0.08)
        stop.set()
        await task

    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner())

    # we expect at least 3 attempts (2 failures then success or more attempts)
    assert mgr._connect_attempts >= 3
