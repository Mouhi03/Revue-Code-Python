"""AST-based checks: length, nesting, complexity, naming, unused vars, duplicates."""
import ast

from .models import Issue

MAX_FUNC_LINES, MAX_NESTING, MAX_COMPLEXITY = 40, 3, 10
OK_SHORT = {"i", "j", "k", "n", "x", "y", "z", "_", "df", "id", "ax", "e", "f"}
BLOCKS = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _depth(node, d=0):
    best = d
    for ch in ast.iter_child_nodes(node):
        best = max(best, _depth(ch, d + 1 if isinstance(ch, BLOCKS) else d))
    return best


def _complexity(fn):
    c = 1
    for n in ast.walk(fn):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp,
                          ast.comprehension, ast.AsyncFor)):
            c += 1
        elif isinstance(n, ast.BoolOp):
            c += len(n.values) - 1
    return c


def analyze_metrics(code: str):
    tree = ast.parse(code)
    issues, named = [], set()

    def add(sev, line, rule, msg):
        issues.append(Issue(sev, line, rule, msg, "ast"))

    for node in ast.walk(tree):
        if isinstance(node, FUNCS):
            n = node.name
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > MAX_FUNC_LINES:
                add("avertissement", node.lineno, "AST-LONG",
                    f"La fonction '{n}' fait {length} lignes (max conseillé : {MAX_FUNC_LINES}).")
            if _depth(node) > MAX_NESTING:
                add("avertissement", node.lineno, "AST-NEST",
                    f"La fonction '{n}' a une imbrication de {_depth(node)} niveaux.")
            if _complexity(node) > MAX_COMPLEXITY:
                add("avertissement", node.lineno, "AST-CPLX",
                    f"La fonction '{n}' a une complexité cyclomatique de {_complexity(node)}.")
            if not ast.get_docstring(node) and not n.startswith("_"):
                add("suggestion", node.lineno, "AST-DOC", f"La fonction '{n}' n'a pas de docstring.")
            if len(n) <= 2 and n not in OK_SHORT and n not in named:
                named.add(n)
                add("suggestion", node.lineno, "AST-NAME", f"Nom de fonction peu explicite : '{n}'.")
            for d in node.args.defaults + node.args.kw_defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    add("avertissement", d.lineno, "AST-MUTDEF",
                        f"Argument par défaut mutable dans '{n}'.")
            stores, loads = {}, set()
            for s in ast.walk(node):
                if isinstance(s, ast.Name):
                    if isinstance(s.ctx, ast.Store):
                        stores.setdefault(s.id, s.lineno)
                    else:
                        loads.add(s.id)
            for var, ln in stores.items():
                if var not in loads and not var.startswith("_"):
                    add("avertissement", ln, "AST-UNUSED", f"Variable '{var}' assignée mais jamais utilisée.")
            for a in node.args.args:
                if a.arg in ("l", "O", "I") and a.arg not in named:
                    named.add(a.arg)
                    add("suggestion", a.lineno, "AST-NAME", f"Nom ambigu '{a.arg}' (confusion avec 1/0).")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if (len(node.id) <= 2 or node.id in ("l", "O", "I")) and node.id not in OK_SHORT \
                    and node.id not in named:
                named.add(node.id)
                add("suggestion", node.lineno, "AST-NAME", f"Nom de variable peu explicite : '{node.id}'.")
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            add("avertissement", node.lineno, "AST-BARE", "'except:' sans type masque toutes les erreurs.")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            add("critique", node.lineno, "AST-EVAL", f"Usage de {node.func.id}() : risque de sécurité.")

    seen = {}
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and len(body) >= 3 and all(isinstance(s, ast.stmt) for s in body):
            for i in range(len(body) - 2):
                key = "|".join(ast.dump(s) for s in body[i:i + 3])
                seen.setdefault(key, []).append(body[i].lineno)
    for lines in seen.values():
        lines = sorted(set(lines))
        if len(lines) > 1 and lines[-1] - lines[0] >= 3:
            add("suggestion", lines[1], "AST-DUP",
                f"Bloc de code dupliqué (lignes {', '.join(map(str, lines))}) : à factoriser.")

    return issues


def compute_score(issues):
    pts = 100 - sum({"critique": 15, "avertissement": 5, "suggestion": 2}[i.severity] for i in issues)
    pts = max(0, pts)
    grade = "A" if pts >= 90 else "B" if pts >= 75 else "C" if pts >= 60 else "D" if pts >= 40 else "E"
    return pts, grade
