#!/usr/bin/env python3
"""Validate that required environment variables are present without printing values.

This script loads `.env.local` (if present) and checks for a small set of
required environment variables used by Nyra: OPENAI_API_KEY, TWILIO_ACCOUNT_SID,
TWILIO_AUTH_TOKEN, ADMIN_TOKEN. It returns exit code 0 if all are present, and
1 otherwise. The script never prints secret values — only names of missing keys.
"""
import os
import sys
from dotenv import load_dotenv


REQUIRED_KEYS = [
    "OPENAI_API_KEY",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "ADMIN_TOKEN",
]


def main() -> int:
    # load .env.local without printing or overwriting existing environment
    load_dotenv(".env.local", override=False)

    missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
    if missing:
        print("Missing required environment variables:", ", ".join(missing))
        return 1

    print("All required environment variables appear to be present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
