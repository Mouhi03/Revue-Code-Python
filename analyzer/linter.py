"""Wrapper around Ruff (static analysis). Gracefully degrades if Ruff is missing."""
import json
import shutil
import subprocess
import sys

from .models import Issue

_CRITICAL_PREFIXES = ("E9", "F82", "F63", "F7", "F5")
_ARGS = ["--select", "E,F,W,B,SIM,C4", "--ignore", "E501", "--stdin-filename", "code.py"]


def _ruff_cmd():
    exe = shutil.which("ruff")
    return [exe] if exe else [sys.executable, "-m", "ruff"]


def _run(extra, code):
    return subprocess.run(_ruff_cmd() + ["check"] + extra + _ARGS + ["-"],
                          input=code, capture_output=True, text=True, timeout=30)


def ruff_available() -> bool:
    try:
        return subprocess.run(_ruff_cmd() + ["--version"], capture_output=True,
                              timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def run_ruff(code: str):
    try:
        out = _run(["--output-format", "json"], code).stdout
        items = json.loads(out or "[]")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []
    issues = []
    for it in items:
        c = it.get("code") or "RUFF"
        sev = "critique" if c.startswith(_CRITICAL_PREFIXES) else (
            "avertissement" if c[0] in "FEB" else "suggestion")
        issues.append(Issue(sev, it["location"]["row"], c, it["message"], "ruff"))
    return issues


def ruff_fix(code: str):
    """Code with Ruff's safe auto-fixes applied, or None."""
    try:
        r = _run(["--fix"], code)
        return r.stdout if r.stdout.strip() and r.stdout != code else None
    except (OSError, subprocess.SubprocessError):
        return None
