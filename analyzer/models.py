from dataclasses import dataclass

SEVERITIES = ("critique", "avertissement", "suggestion")


@dataclass
class Issue:
    severity: str   # critique | avertissement | suggestion
    line: int
    rule: str
    message: str
    source: str = "ast"   # ast | ruff
