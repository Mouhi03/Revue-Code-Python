"""Explanations and recommendations.

Three engines, picked from what the user configured:
  - Claude : an Anthropic API key was typed in the app (or ANTHROPIC_API_KEY is set).
  - Ollama : no key -> a model served locally by Ollama; the code never leaves the machine.
  - Static : neither is usable -> AST-based explanations, so the app always works offline.
"""
import ast
import http.client
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlparse

from .prompts import SYSTEM_PROMPT, build_user_prompt

DEFAULT_CLAUDE_MODEL = os.getenv("REVIEW_MODEL", "claude-sonnet-5-5")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180"))  # local models can be slow
CLAUDE_TIMEOUT = 120.0

_NETWORK_ERRORS = (OSError, ValueError, http.client.HTTPException)


class EngineError(Exception):
    """An AI engine failed. The message is written for the end user."""


@dataclass(frozen=True)
class Engine:
    kind: str                                        # "claude" | "ollama"
    model: str
    api_key: str = field(default="", repr=False)     # kept out of logs and tracebacks
    host: str = DEFAULT_OLLAMA_HOST

    @property
    def is_local(self) -> bool:
        return self.kind == "ollama"

    @property
    def label(self) -> str:
        return f"{'Ollama' if self.is_local else 'Claude'} ({self.model})"


def normalize_host(host: str) -> str:
    """Accept '127.0.0.1:11434' (Ollama's own convention) and refuse non-HTTP schemes."""
    host = (host or "").strip() or DEFAULT_OLLAMA_HOST
    if "://" not in host:
        host = "http://" + host
    if urlparse(host).scheme not in ("http", "https"):
        raise ValueError("L'adresse d'Ollama doit commencer par http:// ou https://")
    return host.rstrip("/")


def resolve_engine(api_key: str = "", ollama_model: str | None = None,
                   ollama_host: str | None = None, claude_model: str | None = None) -> Engine:
    """A key (typed or in ANTHROPIC_API_KEY) selects Claude; an empty one selects Ollama."""
    key = (api_key or os.getenv("ANTHROPIC_API_KEY", "")).strip()
    if key:
        return Engine("claude", claude_model or DEFAULT_CLAUDE_MODEL, api_key=key)
    return Engine("ollama", ollama_model or DEFAULT_OLLAMA_MODEL,
                  host=normalize_host(ollama_host or DEFAULT_OLLAMA_HOST))


RULE_HELP = {
    "AST-LONG": ("Une longue fonction fait trop de choses à la fois.", "Découpez-la en petites fonctions : plus lisible et testable."),
    "AST-NEST": ("Trop de niveaux d'imbrication rendent le flux difficile à suivre.", "Utilisez des retours anticipés ou extrayez des fonctions."),
    "AST-CPLX": ("Beaucoup de branches = beaucoup de cas à tester.", "Simplifiez la logique pour réduire les risques de bugs."),
    "AST-NAME": ("Un nom court ne dit pas ce que contient la variable.", "Des noms explicites rendent le code auto-documenté."),
    "AST-UNUSED": ("Une variable inutilisée est souvent un reste ou une erreur.", "Supprimez-la ou utilisez-la : code plus clair."),
    "AST-DUP": ("Le même bloc est copié à plusieurs endroits.", "Factorisez dans une fonction : une seule correction à faire."),
    "AST-DOC": ("Sans docstring, il faut lire tout le code pour comprendre la fonction.", "Une phrase suffit pour documenter le rôle."),
    "AST-MUTDEF": ("La valeur par défaut mutable est partagée entre tous les appels.", "Utilisez None puis créez la liste dans la fonction."),
    "AST-BARE": ("'except:' attrape aussi KeyboardInterrupt et masque les vrais bugs.", "Précisez le type d'exception attendu."),
    "AST-EVAL": ("eval/exec exécutent du texte comme du code : faille de sécurité.", "Utilisez ast.literal_eval ou une logique explicite."),
    "F401": ("Un import inutilisé alourdit le fichier.", "Supprimez-le."),
    "F841": ("Variable locale assignée mais jamais lue.", "Supprimez-la ou utilisez-la."),
}


def local_explain(code: str, level: str) -> dict:
    tree = ast.parse(code)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    loops = sum(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))
    conds = sum(isinstance(n, ast.If) for n in ast.walk(tree))
    imports = sorted({a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} |
                     {n.module or "." for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)})
    summary = (f"Programme de {len(code.splitlines())} lignes : {len(funcs)} fonction(s), "
               f"{len(classes)} classe(s), {loops} boucle(s), {conds} condition(s).")
    parts = []
    if imports:
        parts.append(f"**Modules importés :** {', '.join(imports)}.")
    for fn in funcs:
        args = ", ".join(a.arg for a in fn.args.args)
        doc = (ast.get_docstring(fn) or "").split("\n")[0]
        ret = "retourne une valeur" if any(isinstance(n, ast.Return) and n.value for n in ast.walk(fn)) \
            else "ne retourne pas de valeur"
        parts.append(f"- `{fn.name}({args})` : {doc or 'rôle non documenté'} — {ret}.")
    if level == "Débutant":
        parts.append("\n*Rappel : une fonction est un bloc de code réutilisable ; une boucle répète des "
                     "instructions ; une condition (`if`) choisit entre plusieurs chemins.*")
    if level == "Expérimenté":
        from analyzer.metrics import _complexity
        parts.append("\n**Complexité cyclomatique :** " +
                     ", ".join(f"{f.name}={_complexity(f)}" for f in funcs) if funcs else "")
    parts.append("\n*(Analyse statique sans IA. Saisissez une clé API ou démarrez Ollama pour une explication plus riche.)*")
    return {"summary": summary, "explanation": "\n".join(parts)}


def local_recommendations(issues) -> list:
    recs = []
    for i in issues:
        reason, benefit = RULE_HELP.get(i.rule, ("Signalé par l'analyse statique.", "Code plus propre et plus sûr."))
        recs.append({"line": i.line, "severity": i.severity, "problem": i.message,
                     "reason": reason, "benefit": benefit,
                     "caution": "Vérifiez que le comportement du programme reste identique."})
    return recs


def _as_text(value) -> str:
    """Small local models sometimes answer with a list or a dict instead of a string."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(f"- {_as_text(v)}" for v in value)
    if isinstance(value, dict):
        return "\n".join(f"**{k}** : {_as_text(v)}" for k, v in value.items())
    return str(value)


def _clean_recommendations(items) -> list:
    out = []
    for it in items if isinstance(items, list) else []:
        if isinstance(it, dict):
            out.append({"line": it.get("line"), "severity": it.get("severity", "suggestion"),
                        "problem": _as_text(it.get("problem")) or "Point à examiner",
                        "reason": _as_text(it.get("reason")), "benefit": _as_text(it.get("benefit")),
                        "caution": _as_text(it.get("caution"))})
    return out


def _parse_reply(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EngineError("la réponse n'est pas un JSON valide") from exc
    if not isinstance(data, dict):
        raise EngineError("la réponse n'a pas le format attendu")
    for key in ("summary", "explanation", "recommendations"):
        if key not in data:
            raise EngineError(f"réponse incomplète : « {key} » manquant")
    data["summary"] = _as_text(data["summary"])
    data["explanation"] = _as_text(data["explanation"])
    data["recommendations"] = _clean_recommendations(data["recommendations"])
    data["changes"] = _as_text(data.get("changes"))
    improved = data.get("improved_code")
    data["improved_code"] = improved if isinstance(improved, str) and improved.strip() else None
    return data


def claude_explain(code: str, issues, level: str, api_key: str, model: str = DEFAULT_CLAUDE_MODEL) -> dict:
    try:
        import anthropic  # imported lazily: optional dependency
    except ImportError as exc:
        raise EngineError("le paquet « anthropic » n'est pas installé (pip install anthropic)") from exc
    client = anthropic.Anthropic(api_key=api_key, timeout=CLAUDE_TIMEOUT)
    try:
        msg = client.messages.create(model=model, max_tokens=4000, system=SYSTEM_PROMPT,
                                     messages=[{"role": "user", "content": build_user_prompt(code, issues, level)}])
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
        raise EngineError("clé API refusée par Anthropic, vérifiez qu'elle est correcte et active") from exc
    except anthropic.NotFoundError as exc:
        raise EngineError(f"modèle « {model} » introuvable pour cette clé") from exc
    except anthropic.RateLimitError as exc:
        raise EngineError("limite de requêtes atteinte, réessayez dans un instant") from exc
    except anthropic.APIConnectionError as exc:
        raise EngineError("connexion à l'API Anthropic impossible") from exc
    except anthropic.APIStatusError as exc:
        raise EngineError(f"erreur de l'API Anthropic (HTTP {exc.status_code})") from exc
    return _parse_reply("".join(b.text for b in msg.content if b.type == "text"))


def _ollama_call(host: str, path: str, payload: dict | None = None, timeout: float = 5.0) -> dict:
    req = urllib.request.Request(
        normalize_host(host) + path, method="POST" if payload is not None else "GET",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # scheme restricted to http(s) above
        return json.loads(resp.read().decode("utf-8"))


def ollama_models(host: str = DEFAULT_OLLAMA_HOST, timeout: float = 2.0):
    """Names of the installed models, or None if the Ollama server cannot be reached."""
    try:
        data = _ollama_call(host, "/api/tags", timeout=timeout)
    except _NETWORK_ERRORS:
        return None
    return sorted(m["name"] for m in data.get("models", []) if m.get("name"))


def ollama_explain(code: str, issues, level: str, model: str = DEFAULT_OLLAMA_MODEL,
                   host: str = DEFAULT_OLLAMA_HOST) -> dict:
    payload = {"model": model, "stream": False, "format": "json",
               "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": build_user_prompt(code, issues, level)}],
               "options": {"temperature": 0.2, "num_ctx": 8192}}
    try:
        reply = _ollama_call(host, "/api/chat", payload, timeout=OLLAMA_TIMEOUT)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise EngineError(f"modèle « {model} » absent, installez-le avec « ollama pull {model} »") from exc
        raise EngineError(f"Ollama a répondu par une erreur HTTP {exc.code}") from exc
    except TimeoutError as exc:
        raise EngineError("délai dépassé, essayez un modèle plus léger ou un code plus court") from exc
    except _NETWORK_ERRORS as exc:
        raise EngineError(f"Ollama est injoignable à {host}, démarrez-le avec « ollama serve »") from exc
    return _parse_reply((reply.get("message") or {}).get("content", ""))


def explain(code: str, issues, level: str, engine: Engine) -> dict:
    if engine.is_local:
        return ollama_explain(code, issues, level, engine.model, engine.host)
    return claude_explain(code, issues, level, engine.api_key, engine.model)
