import os
import tempfile
import subprocess
from pathlib import Path


def run_validator(tmp_env_content: str | None):
    repo = Path(__file__).resolve().parents[1]
    env_path = repo / ".env.local"
    # create or clean
    if env_path.exists():
        env_path.unlink()
    if tmp_env_content is not None:
        env_path.write_text(tmp_env_content)

    # run the script
    import sys
    proc = subprocess.run([sys.executable, "scripts/validate_env.py"], cwd=str(repo), capture_output=True, text=True)

    # cleanup
    if env_path.exists():
        env_path.unlink()

    return proc.returncode, proc.stdout, proc.stderr


def test_validator_fails_on_missing():
    # empty file -> missing all required
    code, out, err = run_validator("")
    assert code == 1
    assert "Missing required environment variables" in out


def test_validator_passes_when_present():
    content = "OPENAI_API_KEY=abc\nTWILIO_ACCOUNT_SID=1\nTWILIO_AUTH_TOKEN=2\nADMIN_TOKEN=3\n"
    code, out, err = run_validator(content)
    assert code == 0
    assert "All required environment variables" in out
