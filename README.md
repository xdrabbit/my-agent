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

Environment setup
-----------------

To get started locally, copy `.env.local.sample` to `.env.local` and fill in your
secrets (this repo ignores `.env.local` so your keys are never committed):

```bash
cp .env.local.sample .env.local
# edit .env.local, then start the app
```

Demo: local mock OpenAI manager
------------------------------

There is a small demo which exercises `OpenAIRealtimeManager` with a safe,
local mock websocket (no network traffic or real keys required):

```bash
./scripts/demo_mock_openai.py
```

Switching to a real OpenAI realtime websocket
--------------------------------------------

If you want to test against the real OpenAI Realtime endpoint you can replace
the mock factory used in the demo with a factory that returns a real websocket
client instance. Keep these safety rules in mind:

- Never print secrets (API keys) to logs or console.
- Keep `.env.local` in `.gitignore` and never commit it.
- Use a separate, short-lived API key for testing when possible.

The project's `OpenAIRealtimeManager` accepts a `ws_factory` callable so you
can write a small factory that returns a `websockets` client or similar. The
demo includes comments showing where to add a production factory.

Live websocket demo (optional)
------------------------------

If you want to attempt a brief websocket handshake with the real OpenAI
Realtime endpoint (only if you understand the network implications and your
API key is ready in `.env.local`), there is `scripts/demo_openai_live.py`.
It will only perform a handshake and close — it does not send audio.

Run it carefully from the repository root like:

```bash
PYTHONPATH=./src python scripts/demo_openai_live.py
```

Secret scanning before commits
-----------------------------

We include a lightweight secret scanner `scripts/scan_secrets.py` which is
invoked by the project's pre-commit hook. The scanner looks for known secret
patterns (such as `sk-` OpenAI keys) and high-entropy tokens in staged files
and blocks commits if likely secrets are detected.

You can run the scanner manually against files or the index:

```bash
# run against a working copy file
python scripts/scan_secrets.py path/to/file

# or let it scan the staged commit (used by the pre-commit hook)
python scripts/scan_secrets.py
```

If you prefer automatic loading of values into your shell, consider using tools
like `direnv` or your system's service manager. Example using `direnv`:

1. install direnv
2. create a `.envrc` that contains `dotenv` loading or `export $(cat .env.local)`
3. `direnv allow`


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
