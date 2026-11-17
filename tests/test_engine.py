import json
import pathlib
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ai import explainer
from pipeline import review

CODE = "import os\n\n\ndef f(l):\n    return l\n"
GOOD_REPLY = {"summary": "Résumé", "explanation": ["étape 1", "étape 2"],
              "recommendations": [{"line": 1, "problem": "Import inutilisé"}],
              "improved_code": "def f(l):\n    return l\n", "changes": "Import retiré"}


class FakeOllama(BaseHTTPRequestHandler):
    models = [{"name": "llama3.1:latest"}]
    reply = GOOD_REPLY
    status = 200

    def log_message(self, *a):
        pass

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {"models": self.models})

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        if self.status != 200:
            return self._send(self.status, {"error": "model not found"})
        content = self.reply if isinstance(self.reply, str) else json.dumps(self.reply)
        self._send(200, {"message": {"role": "assistant", "content": content}})


@pytest.fixture
def ollama():
    FakeOllama.models, FakeOllama.reply, FakeOllama.status = [{"name": "llama3.1:latest"}], GOOD_REPLY, 200
    srv = HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture(autouse=True)
def no_env_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_empty_key_selects_ollama():
    assert explainer.resolve_engine("").kind == "ollama"
    assert explainer.resolve_engine("   ").kind == "ollama"


def test_typed_key_selects_claude_and_is_never_printed():
    e = explainer.resolve_engine("sk-ant-secret123")
    assert e.kind == "claude" and "secret123" not in repr(e) and "secret123" not in e.label


def test_env_key_is_used_when_field_is_empty(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fromenv")
    assert explainer.resolve_engine("").kind == "claude"


def test_host_validation():
    assert explainer.normalize_host("127.0.0.1:11434") == "http://127.0.0.1:11434"
    with pytest.raises(ValueError):
        explainer.normalize_host("file:///etc/passwd")


def test_lists_installed_models(ollama):
    assert explainer.ollama_models(ollama) == ["llama3.1:latest"]
    assert explainer.ollama_models("http://127.0.0.1:9") is None


def test_review_with_ollama(ollama):
    e = explainer.resolve_engine("", "llama3.1:latest", ollama)
    r = review(CODE, use_ai=True, engine=e)
    assert r["ai_used"] and r["engine"] == "Ollama (llama3.1:latest)"
    assert r["explanation"].startswith("- étape 1")          # list coerced to text
    assert r["recommendations"][0]["problem"] == "Import inutilisé"
    assert r["improved_ok"]


def test_ollama_receives_unredacted_code(ollama, monkeypatch):
    seen = {}
    monkeypatch.setattr(explainer, "explain", lambda code, *a: seen.update(code=code) or GOOD_REPLY | {"recommendations": []})
    review('password = "hunter2"\n', use_ai=True, engine=explainer.resolve_engine("", ollama_host=ollama))
    assert "hunter2" in seen["code"]


def test_claude_path_redacts_secrets(monkeypatch):
    seen = {}
    monkeypatch.setattr(explainer, "explain", lambda code, *a: seen.update(code=code) or GOOD_REPLY | {"recommendations": []})
    review('password = "hunter2"\n', use_ai=True, engine=explainer.resolve_engine("sk-ant-x"))
    assert "hunter2" not in seen["code"]


def test_ollama_down_falls_back_to_static():
    e = explainer.resolve_engine("", ollama_host="http://127.0.0.1:9")
    r = review(CODE, use_ai=True, engine=e)
    assert not r["ai_used"] and r["engine"].startswith("Analyse statique")
    assert any("injoignable" in n for n in r["notes"]) and r["issues"]


def test_missing_model_message(ollama):
    FakeOllama.status = 404
    r = review(CODE, use_ai=True, engine=explainer.resolve_engine("", "nope", ollama))
    assert any("ollama pull nope" in n for n in r["notes"])


def test_invalid_json_falls_back(ollama):
    FakeOllama.reply = "pas du json"
    r = review(CODE, use_ai=True, engine=explainer.resolve_engine("", "llama3.1", ollama))
    assert not r["ai_used"] and any("JSON" in n for n in r["notes"])


def test_bad_claude_key_is_reported_without_leaking_it(monkeypatch):
    import anthropic

    def boom(self, **kw):
        raise anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)

    monkeypatch.setattr(anthropic.resources.messages.Messages, "create", boom)
    r = review(CODE, use_ai=True, engine=explainer.resolve_engine("sk-ant-leakme"))
    assert any("clé API refusée" in n for n in r["notes"]) and "leakme" not in json.dumps(r["notes"])
