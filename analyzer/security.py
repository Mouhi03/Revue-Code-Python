"""Input validation and secret redaction. The submitted code is NEVER executed."""
import re

MAX_BYTES = 300 * 1024  # 300 KB

_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\b\s*=\s*(['\"]).+?\2"),
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
]


def validate_upload(filename: str, data: bytes):
    """Return (code, error). Checks extension, size and encoding server-side."""
    if not filename.lower().endswith(".py"):
        return None, "Seuls les fichiers .py sont acceptés."
    if len(data) > MAX_BYTES:
        return None, f"Fichier trop volumineux (max {MAX_BYTES // 1024} Ko)."
    if b"\x00" in data:
        return None, "Le fichier semble binaire, pas du code Python."
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "Le fichier doit être encodé en UTF-8."


def find_secrets(code: str) -> bool:
    return any(p.search(code) for p in _SECRET_PATTERNS)


def redact_secrets(code: str) -> str:
    for p in _SECRET_PATTERNS:
        code = p.sub("<SECRET_MASQUE>", code)
    return code
