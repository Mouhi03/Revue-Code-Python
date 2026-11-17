import ast


def check_syntax(code: str):
    """None if valid, else (line, message). Parsing only, no execution."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as err:
        return (err.lineno or 1, err.msg)
    except (ValueError, RecursionError) as err:
        return (1, str(err))
