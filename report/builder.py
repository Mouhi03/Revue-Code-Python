import difflib

LABEL = {"critique": "Critique", "avertissement": "Avertissement", "suggestion": "Suggestion"}


def make_diff(before: str, after: str) -> str:
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        "avant.py", "apres.py"))


def build_markdown(r: dict) -> str:
    out = ["# Rapport de revue de code Python", ""]
    out += [f"**Score de qualité :** {r['score']}/100 (note {r['grade']})",
            f"**Moteur d'analyse :** {r.get('engine', 'Analyse statique (ast + Ruff)')}", ""]
    out += ["## 1. Résumé du programme", r.get("summary", ""), ""]
    out += ["## 2. Explication du fonctionnement", r.get("explanation", ""), ""]
    out += ["## 3. Erreurs et problèmes potentiels"]
    out += [f"- [{LABEL[i.severity]}] — ligne {i.line} `{i.rule}` : {i.message}" for i in r["issues"]] or ["Aucun problème détecté."]
    out += ["", "## 4. Suggestions d'amélioration"]
    out += [f"- (ligne {x.get('line')}) {x['problem']}" for x in r["recommendations"]] or ["Aucune."]
    out += ["", "## 5. Justification des recommandations"]
    for x in r["recommendations"]:
        out += [f"- **Ligne {x.get('line')} — {x['problem']}**",
                f"  - Raison : {x.get('reason', '')}",
                f"  - Bénéfice : {x.get('benefit', '')}",
                f"  - Précautions : {x.get('caution', '')}"]
    out += ["", "## 6. Code amélioré"]
    if r.get("improved_code"):
        status = "Version vérifiée (syntaxe + Ruff)." if r.get("improved_ok") else "ATTENTION : version non vérifiée, à relire avec soin."
        out += [status, "", "```python", r["improved_code"], "```", r.get("changes", "")]
    else:
        out += ["Aucune version améliorée disponible."]
    out += ["", "---", "*Cet outil ne remplace pas une revue de code par un développeur expérimenté.*"]
    return "\n".join(out)
