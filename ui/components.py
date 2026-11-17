"""HTML fragments for the interface. Every dynamic value is escaped: the reviewed code
(and the messages derived from it) is untrusted input."""
import re
from html import escape

_SEVERITIES = (("critique", "critique"), ("avertissement", "avertissement"), ("suggestion", "suggestion"))
_GRADE_CLASS = {"A": "good", "B": "good", "C": "mid", "D": "low", "E": "low"}


def _inline_code(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escape(text))


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if n > 1 else ''}"


def header() -> str:
    return ('<div class="pm-header"><div class="pm-brand"><div class="pm-mark">&lt;/&gt;</div>'
            '<div class="pm-wordmark">PyMentor</div></div>'
            '<div class="pm-tagline">Assistant intelligent de revue de code Python. Analyse statique '
            '(ast + Ruff) et IA pour comprendre, corriger et améliorer son code.</div></div>')


def side_title(text: str, first: bool = False) -> str:
    return f'<div class="pm-side-title{" pm-side-title--first" if first else ""}">{escape(text)}</div>'


def small(text: str) -> str:
    return f'<div class="pm-small">{escape(text)}</div>'


def status(kind: str, title: str, detail: str) -> str:
    """kind: ok | warn | crit | idle"""
    dot = f" pm-dot--{kind}" if kind in ("ok", "warn", "crit") else ""
    return (f'<div class="pm-status"><span class="pm-dot{dot}"></span>'
            f'<div><b>{escape(title)}</b><span>{escape(detail)}</span></div></div>')


def note(kind: str, text: str) -> str:
    """kind: info | ok | warn | error"""
    cls = f" pm-note--{kind}" if kind in ("ok", "warn", "error") else ""
    return f'<div class="pm-note{cls}">{_inline_code(text)}</div>'


def section(title: str) -> str:
    return f'<div class="pm-h">{escape(title)}</div>'


def verdict(result: dict) -> str:
    issues = result["issues"]
    counts = "".join(
        f'<li><span class="pm-dot pm-dot--{dot}"></span>'
        f'{_plural(sum(i.severity == sev for i in issues), label)}</li>'
        for sev, label, dot in (("critique", "critique", "crit"),
                                ("avertissement", "avertissement", "warn"),
                                ("suggestion", "suggestion", "ok")))
    score, grade = int(result["score"]), str(result["grade"])
    return (f'<div class="pm-verdict"><div class="pm-grade pm-grade--{_GRADE_CLASS.get(grade, "low")}">{escape(grade)}</div>'
            f'<div><div class="pm-score-num">{score}<span>/100</span></div>'
            f'<div class="pm-bar"><i style="width:{max(0, min(score, 100))}%"></i></div></div>'
            f'<ul class="pm-counts">{counts}</ul>'
            f'<div class="pm-engine">{escape(result.get("engine", ""))}</div></div>')


def issues_list(issues) -> str:
    rows = "".join(
        f'<div class="pm-issue pm-sev-{i.severity}"><div class="pm-rail"></div>'
        f'<div class="pm-line">L{i.line}</div><div class="pm-rule">{escape(i.rule)}</div>'
        f'<div class="pm-msg">{_inline_code(i.message)}</div><div class="pm-src">{escape(i.source)}</div></div>'
        for i in issues)
    return f'<div class="pm-issues">{rows}</div>'


def recommendation(x: dict) -> str:
    return ('<dl class="pm-rec">'
            f'<dt>Raison</dt><dd>{_inline_code(str(x.get("reason") or "-"))}</dd>'
            f'<dt>Bénéfice</dt><dd>{_inline_code(str(x.get("benefit") or "-"))}</dd>'
            f'<dt>Précautions</dt><dd>{_inline_code(str(x.get("caution") or "-"))}</dd></dl>')
