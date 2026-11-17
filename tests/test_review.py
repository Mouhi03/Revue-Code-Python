import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from analyzer.metrics import analyze_metrics
from analyzer.security import redact_secrets, validate_upload
from analyzer.syntax_checker import check_syntax
from pipeline import review

S = pathlib.Path(__file__).parent / "samples"


def read(name):
    return (S / name).read_text(encoding="utf-8")


def rules(code):
    return {i.rule for i in analyze_metrics(code)}


def test_syntax_error_detected():
    assert check_syntax(read("syntax_error.py"))[0] == 1


def test_good_code_has_no_issues():
    r = review(read("good.py"), use_ai=False)
    assert r["issues"] == [] and r["grade"] == "A"


def test_bad_names_and_unused():
    assert {"AST-NAME", "AST-UNUSED"} <= rules(read("bad_names.py"))


def test_duplicates_bare_except_eval():
    assert {"AST-DUP", "AST-BARE", "AST-EVAL"} <= rules(read("long_dup.py"))


def test_empty_file():
    assert "error" in review(read("empty.py"))


def test_upload_validation():
    assert validate_upload("a.txt", b"x")[1]
    assert validate_upload("a.py", b"x" * 400_000)[1]
    assert validate_upload("a.py", b"\x00\x01")[1]
    assert validate_upload("a.py", b"print(1)")[1] is None


def test_secret_redaction():
    assert "hunter2" not in redact_secrets('password = "hunter2"')


def test_review_does_not_execute_code():
    r = review("import os\nos.system('touch /tmp/pwned_by_review')\n")
    assert not pathlib.Path("/tmp/pwned_by_review").exists() and r["issues"] is not None
