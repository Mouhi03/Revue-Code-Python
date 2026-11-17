import os
from pathlib import Path

import streamlit as st

from ai import explainer
from analyzer.linter import ruff_available
from analyzer.security import find_secrets, validate_upload
from pipeline import review
from report.builder import build_markdown, make_diff
from ui import components as ui
from ui.styles import CSS

LEVELS = ["Débutant", "Intermédiaire", "Expérimenté"]


def _favicon():
    try:
        from PIL import Image
        return Image.open(Path(__file__).parent / "assets" / "favicon.png")
    except Exception:
        return None


st.set_page_config(page_title="PyMentor", page_icon=_favicon(), layout="wide")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=5, show_spinner=False)
def installed_models(host: str):
    return explainer.ollama_models(host)


def md(html: str):
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    md(ui.side_title("Moteur d'analyse", first=True))
    api_key = st.text_input(
        "Clé API Anthropic", type="password", placeholder="sk-ant-...",
        help="Laissez ce champ vide pour utiliser Ollama en local. La clé reste en mémoire "
             "le temps de la session : elle n'est ni enregistrée ni affichée.")
    typed_key = api_key.strip()
    uses_claude = bool(typed_key or os.getenv("ANTHROPIC_API_KEY", "").strip())
    if typed_key and not typed_key.startswith("sk-ant-"):
        md(ui.note("warn", "Format inhabituel : les clés Anthropic commencent par `sk-ant-`."))

    try:
        host, host_error = explainer.normalize_host(
            st.session_state.get("ollama_host", explainer.DEFAULT_OLLAMA_HOST)), None
    except ValueError as exc:
        host, host_error = explainer.normalize_host(explainer.DEFAULT_OLLAMA_HOST), str(exc)

    ollama_model, ai_ready = None, True
    if uses_claude:
        md(ui.status("ok", "Claude", "Clé saisie dans l'application." if typed_key
                     else "Clé lue dans la variable ANTHROPIC_API_KEY."))
    else:
        models = installed_models(host)
        if models:
            md(ui.status("ok", "Ollama (local)", "Aucune clé saisie : l'analyse tourne sur cette machine."))
            preferred = os.getenv("OLLAMA_MODEL", "")
            ollama_model = st.selectbox("Modèle Ollama", models,
                                        index=models.index(preferred) if preferred in models else 0)
        elif models is None:
            ai_ready = False
            md(ui.status("warn", "Ollama injoignable",
                         f"Aucune réponse de {host}. Démarrez Ollama ou saisissez une clé API."))
        else:
            ai_ready = False
            md(ui.status("warn", "Ollama sans modèle", "Installez-en un : `ollama pull llama3.1`"))

    use_ai = st.toggle("Utiliser l'IA", value=ai_ready, disabled=not ai_ready) and ai_ready

    with st.expander("Options avancées"):
        st.text_input("Modèle Claude", value=explainer.DEFAULT_CLAUDE_MODEL, key="claude_model")
        st.text_input("Adresse d'Ollama", value=explainer.DEFAULT_OLLAMA_HOST, key="ollama_host")
        if host_error:
            st.error(host_error)

    md(ui.side_title("Analyse"))
    level = st.selectbox("Niveau d'explication", LEVELS)

    md(ui.side_title("Confidentialité"))
    if use_ai and uses_claude:
        md(ui.small("Le code est envoyé à Anthropic pour analyse. Les secrets détectés sont masqués avant l'envoi."))
    elif use_ai:
        md(ui.small("Le code est analysé par Ollama et ne quitte pas cette machine."))
    else:
        md(ui.small("Analyse statique uniquement : rien n'est envoyé hors de cette machine."))
    if not ruff_available():
        md(ui.note("error", "Ruff n'est pas installé : `pip install ruff`."))
    md(ui.small("Cet outil ne garantit pas l'absence d'erreurs et ne remplace pas la revue d'un développeur expérimenté."))

# ---------------------------------------------------------------- input
md(ui.header())

tab_text, tab_file = st.tabs(["Saisir du code", "Importer un fichier .py"])
code = None
with tab_text:
    typed = st.text_area("Code Python", height=300, placeholder="def f(l):\n    ...",
                         label_visibility="collapsed")
    if typed:
        code = typed
with tab_file:
    up = st.file_uploader("Fichier Python", type=["py"], label_visibility="collapsed")
    if up is not None:
        code, err = validate_upload(up.name, up.getvalue())
        if err:
            md(ui.note("error", err))

if st.button("Analyser le code", type="primary"):
    if not code:
        md(ui.note("warn", "Saisissez ou importez du code d'abord."))
    else:
        engine = explainer.resolve_engine(
            typed_key, ollama_model=ollama_model, ollama_host=host,
            claude_model=st.session_state.get("claude_model") or None) if use_ai else None
        if engine and not engine.is_local and find_secrets(code):
            md(ui.note("warn", "Des secrets potentiels ont été détectés : ils seront masqués avant l'envoi à l'IA."))
        wait = (f"Analyse en cours avec {engine.label}. Cela peut prendre une minute en local."
                if engine and engine.is_local else "Analyse en cours...")
        with st.spinner(wait):
            st.session_state["result"] = review(code, level, use_ai, engine)
            st.session_state["code"] = code

# ---------------------------------------------------------------- results
r = st.session_state.get("result")
if r:
    if r.get("error"):
        md(ui.note("error", r["error"]))
        st.stop()
    for n in r["notes"]:
        md(ui.note("info", n))
    md(ui.verdict(r))

    md(ui.section("1. Résumé"))
    st.write(r["summary"])
    md(ui.section("2. Fonctionnement"))
    st.markdown(r["explanation"] or "-")

    md(ui.section("3. Erreurs et problèmes potentiels"))
    if r["issues"]:
        md(ui.issues_list(r["issues"]))
    else:
        md(ui.note("ok", "Aucun problème détecté."))

    md(ui.section("4-5. Suggestions et justifications"))
    if not r["recommendations"]:
        md(ui.note("ok", "Aucune suggestion."))
    for x in r["recommendations"]:
        with st.expander(f"Ligne {x.get('line')} : {x['problem']}"):
            md(ui.recommendation(x))

    md(ui.section("6. Code amélioré"))
    if r["improved_code"]:
        if r["improved_ok"]:
            md(ui.note("ok", "Version vérifiée (syntaxe valide, aucune erreur critique Ruff)."))
        else:
            md(ui.note("warn", "Cette version n'a pas passé les contrôles : relisez-la avec soin."))
        if r.get("changes"):
            st.markdown(r["changes"])
        t1, t2 = st.tabs(["Diff", "Code complet"])
        t1.code(make_diff(st.session_state["code"], r["improved_code"]), language="diff")
        t2.code(r["improved_code"], language="python")
    else:
        st.write("Aucune version améliorée disponible.")

    st.download_button("Télécharger le rapport (Markdown)", build_markdown(r),
                       file_name="rapport_revue.md", mime="text/markdown")
