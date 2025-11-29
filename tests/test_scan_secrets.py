import subprocess
import sys
from pathlib import Path
import tempfile


def run_scan(path: Path):
    proc = subprocess.run([sys.executable, "scripts/scan_secrets.py", str(path)], cwd=str(path.parents[1]), capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_scan_detects_sk_key(tmp_path: Path):
    p = tmp_path / "bad.txt"
    p.write_text("api_key=sk-ABCDEFGHIJKLMNOPQRSTUVXYZ0123456789abcdef")
    code, out, err = run_scan(p)
    assert code == 1
    assert "Potential secrets detected" in out


def test_scan_passes_on_safe_content(tmp_path: Path):
    p = tmp_path / "ok.txt"
    p.write_text("this is normal text with no long tokens or secrets")
    code, out, err = run_scan(p)
    assert code == 0
    assert "No likely secrets found." in out
