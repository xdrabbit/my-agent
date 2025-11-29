"""Audio pipeline stubs — encoder/decoder, jitter buffer, and framing.

This module provides minimal classes and typed stubs for the real-time audio pipeline.
The executor agent should replace the internal logic with a production-grade implementation that
handles Twilio media chunk conversion, jitter buffering, and encoder/decoder pipelines.
"""
from dataclasses import dataclass
from typing import Optional, List
import logging

logger = logging.getLogger("nyra.audio")

@dataclass
class AudioFrame:
    timestamp_ms: int
    data: bytes
    sample_rate: int = 8000

class JitterBuffer:
    def __init__(self, max_ms: int = 500):
        self.max_ms = max_ms
        self.queue: List[AudioFrame] = []

    def push(self, frame: AudioFrame):
        self.queue.append(frame)
        logger.debug("JitterBuffer.push", extra={"len": len(self.queue)})

    def pop(self) -> Optional[AudioFrame]:
        if not self.queue:
            return None
        return self.queue.pop(0)

class Encoder:
    """Encodes PCM frames into a target format for Twilio or OpenAI

    For now this is a pass-through stub.
    """
    def encode(self, frame: AudioFrame) -> bytes:
        return frame.data

class Decoder:
    """Decodes bytes from remote into AudioFrame

    This is a pass-through stub.
    """
    def decode(self, data: bytes, timestamp_ms:int) -> AudioFrame:
        return AudioFrame(timestamp_ms=timestamp_ms, data=data)
