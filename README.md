# PyMentor – Assistant intelligent de revue de code Python

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
pytest -q
```

## Moteur d'analyse

Le moteur se choisit dans la barre latérale, champ « Clé API Anthropic » :

| Champ clé API | Moteur utilisé | Où va le code |
|---|---|---|
| Rempli | Claude (modèle réglable dans « Options avancées ») | Envoyé à Anthropic, secrets masqués |
| Vide | Ollama en local | Reste sur votre machine |
| Vide et Ollama indisponible | Analyse statique (ast + Ruff), sans IA | Reste sur votre machine |

- La clé saisie reste en mémoire pour la session : elle n'est ni écrite sur disque ni affichée. Elle est à ressaisir après un rechargement de la page.
- Une variable d'environnement `ANTHROPIC_API_KEY` est aussi acceptée quand le champ est vide.
- Ollama : installez-le (https://ollama.com), puis `ollama pull llama3.1` et laissez `ollama serve` tourner. L'application détecte les modèles installés et vous laisse choisir. Variables optionnelles : `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` (secondes), `REVIEW_MODEL` (modèle Claude).
- Si le moteur choisi échoue (clé refusée, Ollama arrêté, modèle absent, réponse invalide), l'analyse statique prend le relais et un message explique la cause.

## Structure

- `app.py` : interface Streamlit ; `ui/` : feuille de style et composants HTML ; `.streamlit/config.toml` : thème.
- `pipeline.py` : orchestration ; `ai/` : moteurs Claude et Ollama ; `analyzer/` : ast et Ruff ; `report/` : export Markdown.
