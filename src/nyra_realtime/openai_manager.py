"""OpenAI Realtime connection manager (test-friendly implementation)

This module provides a small async manager that holds a persistent connection to an OpenAI
Realtime WebSocket endpoint. The manager is intentionally designed to be testable — the
actual underlying WebSocket connection is provided by a `ws_factory` callable so tests can
inject a mock implementation.

Functionality included in this scaffold:
- connect/disconnect with graceful teardown
- send/receive queues for audio frames
- background sender/receiver tasks
- simple reconnect/backoff policy
- event callbacks for connected/disconnected/errors/messages

Note: This is still a scaffold for a working implementation. The executor agent should
replace the mocked parts with a production WebSocket client (for example using the
`websockets` package) and real message formats for the OpenAI realtime API.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Callable, Any, Awaitable

logger = logging.getLogger("nyra.openai")


class OpenAIRealtimeManager:
    """Manage a persistent connection to an OpenAI Realtime websocket.

    Parameters
    - api_key: optional API key used for authentication (informational only in tests)
    - ws_factory: an async callable that returns a websocket-like object with `send` and
      `recv` coroutines and an optional `close()`.
    - url: endpoint URL (string) — stored for diagnostics.
    - reconnect_backoff: iterable of seconds to wait between reconnect attempts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        ws_factory: Optional[Callable[[], Awaitable[Any]]] = None,
        url: str | None = None,
        reconnect_backoff: Optional[list[float]] = None,
    ):
        self.api_key = api_key
        self.url = url or "wss://api.openai.com/v1/realtime"
        self.ws_factory = ws_factory

        # connection state
        self._ws = None
        self.connected = False

        # async queues for I/O
        self._send_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._recv_queue: asyncio.Queue[bytes] = asyncio.Queue()

        # background tasks
        self._sender_task: Optional[asyncio.Task] = None
        self._receiver_task: Optional[asyncio.Task] = None

        # reconnect logic
        self.reconnect_backoff = reconnect_backoff or [0.1, 0.2, 0.5, 1.0]
        self._stop_event: Optional[asyncio.Event] = None

        # event callbacks
        self._on_connected: list[Callable[[], None]] = []
        self._on_disconnected: list[Callable[[Optional[Exception]], None]] = []
        self._on_message: list[Callable[[bytes], None]] = []

        # internal bookkeeping
        self._connect_attempts = 0

    # ----------------
    # public API
    # ----------------
    async def connect(self) -> None:
        """Try a single connection attempt using ws_factory and start I/O tasks.

        If no ws_factory is provided, this method will raise RuntimeError so the
        caller/test must supply a factory for a transport.
        """
        if self.connected:
            return

        if not self.ws_factory:
            raise RuntimeError("No websocket factory provided")

        self._connect_attempts += 1
        logger.info("OpenAIRealtimeManager.connect attempt=%d url=%s", self._connect_attempts, self.url)

        self._ws = await self.ws_factory()
        # the returned object is expected to implement async send/recv and close()
        self.connected = True

        # start background tasks
        loop = asyncio.get_running_loop()
        self._sender_task = loop.create_task(self._sender_loop())
        self._receiver_task = loop.create_task(self._receiver_loop())

        for cb in self._on_connected:
            try:
                cb()
            except Exception:
                logger.exception("on_connected callback failed")

    async def disconnect(self) -> None:
        """Gracefully stop background tasks and close the transport."""
        logger.info("OpenAIRealtimeManager.disconnect")
        self.connected = False

        # cancel background tasks
        if self._sender_task:
            self._sender_task.cancel()
            self._sender_task = None
        if self._receiver_task:
            self._receiver_task.cancel()
            self._receiver_task = None

        # close transport
        try:
            if self._ws and hasattr(self._ws, "close"):
                maybe = self._ws.close()
                if asyncio.iscoroutine(maybe):
                    await maybe
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("error while closing websocket: %s", exc)

        self._ws = None

        for cb in self._on_disconnected:
            try:
                cb(None)
            except Exception:
                logger.exception("on_disconnected callback failed")

    async def send_audio(self, data: bytes) -> None:
        """Queue audio bytes to be sent to the realtime API.

        This is non-blocking — the background sender loop drains the queue.
        """
        await self._send_queue.put(data)

    async def receive_voice(self, timeout: Optional[float] = None) -> bytes:
        """Await the next received voice/audio chunk from the realtime endpoint.

        Returns bytes and may raise asyncio.TimeoutError if a timeout is provided.
        """
        data = await asyncio.wait_for(self._recv_queue.get(), timeout) if timeout else await self._recv_queue.get()
        self._recv_queue.task_done()
        return data

    def register_on_connected(self, cb: Callable[[], None]) -> None:
        self._on_connected.append(cb)

    def register_on_disconnected(self, cb: Callable[[Optional[Exception]], None]) -> None:
        self._on_disconnected.append(cb)

    def register_on_message(self, cb: Callable[[bytes], None]) -> None:
        self._on_message.append(cb)

    # ----------------
    # background control
    # ----------------
    async def _sender_loop(self) -> None:
        """Continuously pull from send queue and write to transport.

        If an error occurs the loop will end and the manager will mark disconnected.
        """
        assert self._ws is not None, "sender started without transport"
        try:
            while self.connected:
                frame = await self._send_queue.get()
                try:
                    if hasattr(self._ws, "send"):
                        send_coro = self._ws.send(frame)
                        if asyncio.iscoroutine(send_coro):
                            await send_coro
                    else:
                        logger.debug("ws has no send() method — dropping frame")
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.exception("sender loop error: %s", exc)
                    # signal disconnect and break — receiver task will also exit
                    self.connected = False
                    for cb in self._on_disconnected:
                        try:
                            cb(exc)
                        except Exception:
                            logger.exception("on_disconnected callback failed")
                    break
                finally:
                    try:
                        self._send_queue.task_done()
                    except Exception:
                        pass
        except asyncio.CancelledError:
            logger.info("sender loop cancelled")

    async def _receiver_loop(self) -> None:
        """Continuously receive frames and place into the recv queue.

        The loop expects the transport to provide an async `recv()` and will push raw
        bytes into the recv queue. Any message handlers are called synchronously in a
        safe manner (exceptions are logged and swallowed).
        """
        assert self._ws is not None, "receiver started without transport"
        try:
            while self.connected:
                try:
                    if hasattr(self._ws, "recv"):
                        result = await self._ws.recv()
                    else:
                        # nothing to receive; sleep and continue
                        await asyncio.sleep(0.01)
                        continue

                    if result is None:
                        # treat None as remote close
                        logger.info("transport closed remote end")
                        self.connected = False
                        for cb in self._on_disconnected:
                            try:
                                cb(None)
                            except Exception:
                                logger.exception("on_disconnected callback failed")
                        break

                    # push into queue and notify callbacks
                    await self._recv_queue.put(result)
                    for cb in self._on_message:
                        try:
                            cb(result)
                        except Exception:
                            logger.exception("on_message callback failed")

                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.exception("receiver loop error: %s", exc)
                    # break out and flag disconnected
                    self.connected = False
                    for cb in self._on_disconnected:
                        try:
                            cb(exc)
                        except Exception:
                            logger.exception("on_disconnected callback failed")
                    break
        except asyncio.CancelledError:
            logger.info("receiver loop cancelled")

    async def run_forever(self, stop_event: asyncio.Event) -> None:
        """Run a connect/reconnect loop until stop_event is set.

        The manager will try to maintain a live connection, applying the configured
        backoff schedule between attempts.
        """
        self._stop_event = stop_event
        backoff_index = 0
        while not stop_event.is_set():
            try:
                await self.connect()
                # connected — wait until disconnected or stop event
                while self.connected and not stop_event.is_set():
                    await asyncio.sleep(0.05)
                # if disconnected, loop to reconnect
                backoff_index = 0
            except Exception as exc:
                logger.exception("connect attempt failed: %s", exc)
                # call disconnect handlers
                self.connected = False
                for cb in self._on_disconnected:
                    try:
                        cb(exc)
                    except Exception:
                        logger.exception("on_disconnected callback failed")

            # apply backoff
            if stop_event.is_set():
                break

        # make sure we perform a graceful disconnect/cleanup when the run loop exits
        try:
            await self.disconnect()
        except Exception:
            logger.exception("error during shutdown cleanup")
            wait = self.reconnect_backoff[min(backoff_index, len(self.reconnect_backoff) - 1)]
            backoff_index += 1
            await asyncio.sleep(wait)

