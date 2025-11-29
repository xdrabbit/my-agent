"""OpenAI Realtime websocket factory helpers.

This module provides a factory helper that returns an async callable which will
create and return an active websocket client connection to OpenAI's realtime
endpoint using the configured API key. It is intentionally minimal so the
executor/production implementation can enrich it with robust error handling,
retrying, and official message handshake logic.

NOTE: This factory uses the `websockets` package (already in requirements). The
factory function does not print or log sensitive values. It will raise when
`api_key` is not provided.
"""
from __future__ import annotations

from typing import Optional, Callable, Awaitable, Any
import logging

logger = logging.getLogger("nyra.openai.transport")


def make_openai_ws_factory(api_key: Optional[str], url: Optional[str] = None) -> Callable[[], Awaitable[Any]]:
    """Return an async callable that creates a connected websocket client.

    Example usage:
        factory = make_openai_ws_factory(os.getenv("OPENAI_API_KEY"))
        ws = await factory()

    The returned `ws` object will be the underlying `websockets` protocol
    instance and should implement `send`, `recv`, and `close` async methods.
    """
    if not api_key:
        raise RuntimeError("make_openai_ws_factory requires an api_key")

    try:
        # import here so module import succeeds even if websockets is not used
        import websockets
    except Exception as exc:  # pragma: no cover - import environment
        raise RuntimeError("websockets package is unavailable") from exc

    endpoint = url or "wss://api.openai.com/v1/realtime"

    async def factory() -> Any:
        # Use a conservative set of headers; avoid logging the key itself.
        headers = (
            ("Authorization", f"Bearer {api_key}"),
            ("User-Agent", "nyra-realtime/1.0"),
        )

        logger.info("Opening websocket to OpenAI realtime endpoint")
        ws = await websockets.connect(endpoint, extra_headers=headers)
        return ws

    return factory
