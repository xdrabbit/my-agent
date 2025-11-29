# Nyra Realtime Voice Telephony System — Prototype

This repository contains a scaffold and minimal implementation for the Nyra realtime telephony system described in the design spec.

Goals:
- Provide a clean, extensible codebase implementing the major modules in the spec
- Include API endpoints for Twilio webhooks, outbound calls, control endpoints, and health
- Provide a mockable Realtime manager and audio pipeline for integration tests
- Offer a Dockerfile and systemd unit for local deployment

How to run (local dev):

1. Create a virtualenv and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn nyra_realtime.main:app --reload
```

2. Run tests with pytest

```bash
pip install -r requirements.txt
pytest -q
```

Configuration is done via `.env` and `config.yaml`.

Security / Local secrets
------------------------

Local secret values (API keys, Twilio tokens, etc.) should be stored in `.env.local`.
This file is intentionally ignored by git — see the provided `.gitignore` which contains
`.env.local` so your secrets are not sent to GitHub. If you accidentally committed a
secret to a public repo, rotate the key immediately and remove the file from the
repository using `git rm --cached .env.local` and a subsequent commit.

Developer convenience: install git hooks
---------------------------------------

This repo includes a pre-commit hook template that protects against accidentally
committing `.env` files into the repository. To enable it locally run:

```bash
./scripts/install-hooks.sh
```

This will set git's `core.hooksPath` to `.githooks/` so the pre-commit script is
run automatically before commits.

Continuous Integration
----------------------

A GitHub Actions CI workflow (`.github/workflows/ci.yml`) verifies on each push or
pull request that no environment files are tracked and runs the test suite. This
acts as a second line of defense in case a secrets file is introduced accidentally.

This is a scaffold for an executor agent to implement the full realtime audio flows. See the `src/nyra_realtime` package for module stubs and APIs.

OpenAI Realtime manager
-----------------------

The repository includes a test-friendly `OpenAIRealtimeManager` (in `src/nyra_realtime/openai_manager.py`). The manager is designed to be injected with a websocket factory object so it can be tested without network access. Production integration should provide a real websocket factory (for example using the `websockets` package) and perform the realtime API handshake and message formats.

Example (test/mock usage):

```py
from nyra_realtime.openai_manager import OpenAIRealtimeManager

async def factory():
	# return a websocket-like object that implements async send/recv/close
	...

mgr = OpenAIRealtimeManager(api_key="$OPENAI_API_KEY", ws_factory=factory)
await mgr.connect()
await mgr.send_audio(b"...pcm frames...")
data = await mgr.receive_voice(timeout=1.0)
await mgr.disconnect()
```

When wiring to a real OpenAI realtime endpoint, use the official message formats and an authenticated websocket connection; the manager's queues and run_forever loop will help keep the service resilient and testable.
