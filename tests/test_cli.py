import os
import subprocess
import sys
from pathlib import Path


def _run_cli(*args: str):
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, "-m", "rewriteflat", *args],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
    )


def test_help_works():
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "status" in result.stdout
    assert "audit" in result.stdout


def test_status_works():
    result = _run_cli("status")
    assert result.returncode == 0
    assert "name:" in result.stdout
    assert "claim count" in result.stdout
    assert "example count" in result.stdout


def test_audit_works():
    result = _run_cli("audit")
    assert result.returncode == 0
    assert "audit ok" in result.stdout
