"""Persona configuration, modes, and session injection."""
from pydantic import BaseModel
from typing import Dict, Any
import yaml
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Persona(BaseModel):
    name: str
    description: str
    voice: Dict[str, Any] = {}
    mode: str = "assistant"

DEFAULT_PERSONA = Persona(
    name="Nyra",
    description="Nyra, AI assistant to Tom — always transparent about identity.",
    voice={"style":"warm"},
    mode="assistant",
)

def load_personas(path: str | None = None):
    config_path = Path(path or BASE_DIR / "personas.yaml")
    if not config_path.exists():
        return {"default": DEFAULT_PERSONA}
    with open(config_path, "r") as fh:
        content = yaml.safe_load(fh)
    result = {k: Persona(**v) for k, v in content.items()}
    return result

# Mode switching helper
VALID_MODES = ["assistant", "legal", "warm", "task"]

def is_valid_mode(mode: str) -> bool:
    return mode in VALID_MODES
