#!/usr/bin/env python3
"""Scan staged files (or files passed on CLI) for high-entropy tokens and known secret patterns.

The script is intentionally conservative — it aims to catch likely accidental secrets
in commits (long tokens and sk- OpenAI keys). It prints file:line for findings but
does not print the secret values themselves.

Exit codes:
 - 0 = no findings
 - 1 = findings
 - 2 = usage/error
"""
import sys
import re
import math
from typing import Iterable
import subprocess


MIN_TOKEN_LENGTH = 30
ENTROPY_THRESHOLD = 4.0


def entropy(s: str) -> float:
    # Shannon entropy per character
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    e = 0.0
    for v in freq.values():
        p = v / len(s)
        e -= p * math.log2(p)
    return e


def tokens_from_line(line: str) -> Iterable[str]:
    # split on delimiters but keep base-like tokens
    return re.findall(r"[A-Za-z0-9-_+/=]{16,}", line)


def is_likely_secret_token(tok: str) -> bool:
    if len(tok) < MIN_TOKEN_LENGTH:
        return False
    # OpenAI keys start with sk-
    if tok.startswith("sk-"):
        return True
    # high entropy indicator
    if entropy(tok) > ENTROPY_THRESHOLD:
        return True
    return False


def scan_text(path: str, text: str):
    findings = []
    for i, line in enumerate(text.splitlines(), start=1):
        for tok in tokens_from_line(line):
            if is_likely_secret_token(tok):
                findings.append((path, i, tok))
    return findings


def staged_files():
    # obtain list of staged files
    proc = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
    if proc.returncode != 0:
        print("Could not determine staged files")
        sys.exit(2)
    for f in proc.stdout.splitlines():
        yield f


def file_contents_from_index(path: str) -> str:
    # read staged version using git show :path
    proc = subprocess.run(["git", "show", f":{path}"], capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout


def main(argv):
    targets = []
    if len(argv) > 1:
        # files provided explicitly
        targets = argv[1:]
    else:
        targets = list(staged_files())

    all_findings = []
    for p in targets:
        txt = file_contents_from_index(p) if len(argv) == 1 else open(p, "r", encoding="utf-8", errors="ignore").read()
        findings = scan_text(p, txt)
        if findings:
            all_findings.extend(findings)

    if all_findings:
        print("Potential secrets detected in the following staged files (values are suppressed):")
        for path, line, tok in all_findings:
            print(f"  {path}:{line}")
        print("Please remove any secrets from the commit and add them to .gitignore or use .env.local")
        return 1

    print("No likely secrets found.")
    return 0


if __name__ == "__main__":
    rc = main(sys.argv)
    sys.exit(rc)
