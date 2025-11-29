"""Conversation orchestration: simple VAD, turn-taking and silence detection.

This is a minimal state machine with clear extension points for VAD and barge-in handling.
"""
from dataclasses import dataclass, field
import time
from typing import Optional
import logging

logger = logging.getLogger("nyra.conv")

@dataclass
class ConversationState:
    call_id: str
    nyra_speaking: bool = False
    caller_speaking: bool = False
    last_activity_ms: int = field(default_factory=lambda: int(time.time()*1000))
    silence_timeout_ms: int = 3000

    def update_activity(self):
        self.last_activity_ms = int(time.time()*1000)

    def is_silence(self) -> bool:
        return int(time.time()*1000) - self.last_activity_ms > self.silence_timeout_ms

class TurnManager:
    def __init__(self):
        self.sessions = {}

    def start_session(self, call_id: str) -> ConversationState:
        self.sessions[call_id] = ConversationState(call_id=call_id)
        logger.info("start session", extra={"call_id": call_id})
        return self.sessions[call_id]

    def end_session(self, call_id: str):
        if call_id in self.sessions:
            del self.sessions[call_id]

    def get(self, call_id: str) -> Optional[ConversationState]:
        return self.sessions.get(call_id)
