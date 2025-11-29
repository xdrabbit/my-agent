"""Transcript + metadata logging.

This module formats transcripts and provides a stubbed Chronicle integration.
"""
import json
from typing import Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger("nyra.chronicle")
BASE = Path("./data")
BASE.mkdir(exist_ok=True)

class TranscriptStore:
    def __init__(self, endpoint: str | None = None):
        self.endpoint = endpoint

    def format_transcript(self, call_id: str, items: list, metadata: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "call_id": call_id,
            "items": items,
            "metadata": metadata,
        }
        return payload

    def save_local(self, call_id: str, payload: Dict[str, Any]):
        path = BASE / f"{call_id}.json"
        with open(path, "w") as fh:
            json.dump(payload, fh, indent=2)
        logger.info("Saved local transcript", extra={"path": str(path)})

    def ingest(self, call_id: str, payload: Dict[str, Any]):
        if not self.endpoint:
            logger.warning("Chronicle endpoint not configured, using local store")
            return self.save_local(call_id, payload)
        # TODO: implement HTTP ingestion
        logger.info("Would send to Chronicle", extra={"endpoint": self.endpoint})
