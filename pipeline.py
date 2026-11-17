"""Orchestration: syntax -> static analysis -> explanations -> verified improved code."""
from ai import explainer
from analyzer.linter import ruff_fix, run_ruff
from analyzer.metrics import analyze_metrics, compute_score
from analyzer.models import Issue
from analyzer.security import redact_secrets
from analyzer.syntax_checker import check_syntax

_ORDER = {"critique": 0, "avertissement": 1, "suggestion": 2}


def _critical_count(code):
    return sum(i.severity == "critique" for i in run_ruff(code))


def review(code: str, level: str = "Débutant", use_ai: bool = False, engine=None) -> dict:
    code = code.replace("\r\n", "\n")
    res = {"issues": [], "recommendations": [], "summary": "", "explanation": "",
           "improved_code": None, "improved_ok": False, "ai_used": False, "notes": [],
           "engine": "Analyse statique (ast + Ruff)"}
    if not code.strip():
        res["error"] = "Le code est vide."
        return res

    err = check_syntax(code)
    if err:
        res["issues"] = [Issue("critique", err[0], "SYNTAX", f"Erreur de syntaxe : {err[1]}", "ast")]
        res["summary"] = "Le code contient une erreur de syntaxe : l'analyse détaillée est impossible."
        res["recommendations"] = explainer.local_recommendations(res["issues"])
        res["recommendations"][0].update(reason="Python ne peut pas lire le fichier tant que la syntaxe est invalide.",
                                         benefit="Une fois corrigée, l'analyse complète sera disponible.")
        res["score"], res["grade"] = compute_score(res["issues"])
        return res

    seen, issues = set(), []
    for i in analyze_metrics(code) + run_ruff(code):
        if (i.line, i.rule) not in seen:
            seen.add((i.line, i.rule))
            issues.append(i)
    issues.sort(key=lambda i: (_ORDER[i.severity], i.line))
    res["issues"] = issues
    res["score"], res["grade"] = compute_score(issues)

    data = None
    if use_ai:
        engine = engine or explainer.resolve_engine()
        try:
            # Only a remote service gets redacted code; a local Ollama keeps everything on this machine.
            data = explainer.explain(code if engine.is_local else redact_secrets(code), issues, level, engine)
            res["ai_used"], res["engine"] = True, engine.label
        except explainer.EngineError as exc:
            res["notes"].append(f"{engine.label} indisponible : {exc}. Analyse statique utilisée à la place.")
        except Exception as exc:  # unexpected failure -> never crash the review
            res["notes"].append(f"{engine.label} indisponible ({type(exc).__name__}). "
                                "Analyse statique utilisée à la place.")
    if data is None:
        data = explainer.local_explain(code, level)
        data["recommendations"] = explainer.local_recommendations(issues)
        data["improved_code"] = ruff_fix(code)
        data["changes"] = "Corrections automatiques sûres appliquées par Ruff."
    res.update({k: data.get(k) or res[k] for k in ("summary", "explanation", "recommendations", "changes")
                if k in data})

    if issues and not res["recommendations"]:
        res["recommendations"] = explainer.local_recommendations(issues)

    improved = data.get("improved_code")
    if improved and improved.strip() != code.strip():
        res["improved_code"] = improved
        res["improved_ok"] = check_syntax(improved) is None and _critical_count(improved) <= _critical_count(code)
    return res
