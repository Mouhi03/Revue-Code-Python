"""Stylesheet injected into Streamlit. Colours and fonts are tokens on :root."""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #17202A;
  --muted: #5B6776;
  --line: #D8DEE6;
  --panel: #F3F5F8;
  --track: #E4E8EE;
  --accent: #2455A4;
  --crit: #B3261E;  --crit-bg: #FCEFEE;
  --warn: #9A5B00;  --warn-bg: #FDF4E3;
  --ok:   #1F7A4D;  --ok-bg:   #EDF6F1;
  --sans: 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
}

/* ---- page chrome ---- */
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3,
.stApp button, .stApp input, .stApp textarea { font-family: var(--sans); }
.stApp code, .stApp pre, .stApp pre *, [data-testid="stTextArea"] textarea { font-family: var(--mono) !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1080px; padding-top: 2.4rem; padding-bottom: 4rem; }

[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] { padding-top: 1.6rem; }

/* ---- inputs ---- */
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
  background: #fff; border-color: var(--line); border-radius: 6px;
}
[data-testid="stTextArea"] textarea { font-size: 14px; line-height: 1.6; background: #fff; padding: 0.9rem 1rem; }
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { height: 2.2rem; padding-bottom: 0; }
[data-testid="stTabs"] [role="tab"] { font-weight: 500; }
.stButton > button, .stDownloadButton > button {
  border-radius: 6px; font-weight: 500; padding: 0.5rem 1.25rem;
}
[data-testid="stExpander"], [data-testid="stExpander"] details { border: 1px solid var(--line); border-radius: 6px; background: #fff; box-shadow: none; }
[data-testid="stExpander"] details { border: 0; }
[data-testid="stExpander"] summary { font-weight: 500; }
[data-testid="stSidebar"] [data-testid="stExpander"] { background: transparent; box-shadow: none; }

/* ---- header ---- */
.pm-header { padding-bottom: 1.1rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--line); }
.pm-brand { display: flex; align-items: center; gap: 12px; }
.pm-mark {
  display: grid; place-items: center; width: 34px; height: 34px; border-radius: 8px;
  background: var(--accent); color: #fff; font: 500 13px var(--mono);
}
.pm-wordmark { font-size: 28px; font-weight: 600; letter-spacing: -0.02em; color: var(--ink); line-height: 1; }
.pm-tagline { margin-top: 0.65rem; font-size: 15px; color: var(--muted); max-width: 70ch; }

/* ---- sidebar ---- */
.pm-side-title {
  font-size: 13.5px; font-weight: 600; color: var(--ink);
  margin: 1.5rem 0 0.6rem; padding-bottom: 0.4rem; border-bottom: 1px solid var(--line);
}
.pm-side-title--first { margin-top: 0; }
.stApp .pm-small { font-size: 12.5px; line-height: 1.55; color: var(--muted); margin: 0.5rem 0; }
.pm-status {
  display: flex; gap: 10px; align-items: flex-start; margin: 0.6rem 0 0.9rem;
  padding: 0.6rem 0.75rem; background: #fff; border: 1px solid var(--line); border-radius: 6px;
}
.pm-status .pm-dot { margin-top: 6px; flex: none; }
.pm-status b { display: block; font-size: 14px; color: var(--ink); }
.pm-status span { display: block; font-size: 12.5px; line-height: 1.5; color: var(--muted); margin-top: 2px; }
.pm-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; background: var(--muted); }
.pm-dot--ok { background: var(--ok); }
.pm-dot--warn { background: var(--warn); }
.pm-dot--crit { background: var(--crit); }

/* ---- results ---- */
.pm-h {
  font-size: 17px; font-weight: 600; color: var(--ink);
  margin: 2.4rem 0 0.9rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--line);
}
.pm-verdict {
  display: grid; grid-template-columns: auto minmax(150px, 210px) 1fr auto; gap: 1.6rem;
  align-items: center; padding: 1rem 1.25rem; border: 1px solid var(--line); border-radius: 8px; background: #fff;
}
.pm-grade {
  width: 54px; height: 54px; display: grid; place-items: center; border-radius: 8px;
  font-size: 28px; font-weight: 600; color: #fff;
}
.pm-grade--good { background: var(--ok); }
.pm-grade--mid  { background: var(--warn); }
.pm-grade--low  { background: var(--crit); }
.pm-score-num { font-size: 26px; font-weight: 600; line-height: 1; color: var(--ink); }
.pm-score-num span { font-size: 14px; font-weight: 400; color: var(--muted); margin-left: 3px; }
.pm-bar { height: 6px; margin-top: 0.6rem; background: var(--track); border-radius: 3px; overflow: hidden; }
.pm-bar i { display: block; height: 100%; background: var(--accent); }
.pm-counts { list-style: none; display: flex; flex-wrap: wrap; gap: 0.4rem 1.2rem; margin: 0; padding: 0; font-size: 14px; }
.pm-counts li { display: flex; align-items: center; gap: 7px; color: var(--ink); }
.pm-engine { font-size: 13px; color: var(--muted); text-align: right; }

.pm-note {
  margin: 0.6rem 0; padding: 0.65rem 0.9rem; font-size: 14px; line-height: 1.55; color: var(--ink);
  background: var(--panel); border: 1px solid var(--line); border-left: 3px solid var(--accent); border-radius: 6px;
}
.pm-note--warn  { background: var(--warn-bg); border-color: #EBD3A3; border-left-color: var(--warn); }
.pm-note--error { background: var(--crit-bg); border-color: #EBC1BD; border-left-color: var(--crit); }
.pm-note--ok    { background: var(--ok-bg);   border-color: #BFDECD; border-left-color: var(--ok); }

.pm-issues { border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: #fff; }
.pm-issue {
  display: grid; grid-template-columns: 4px 56px 116px 1fr 44px; gap: 0 14px;
  align-items: baseline; padding: 0.72rem 1rem 0.72rem 0; border-top: 1px solid var(--line);
}
.pm-issue:first-child { border-top: 0; }
.pm-rail { align-self: stretch; margin: -0.72rem 0; }
.pm-line { font: 500 13px var(--mono); color: var(--muted); }
.pm-rule { justify-self: start; font: 500 12px var(--mono); padding: 2px 8px; border-radius: 4px; }
.pm-msg { font-size: 14.5px; line-height: 1.5; color: var(--ink); }
.pm-msg code { font-size: 13px; background: var(--panel); padding: 1px 5px; border-radius: 4px; }
.pm-src { font: 12px var(--mono); color: var(--muted); text-align: right; }
.pm-sev-critique .pm-rail { background: var(--crit); }
.pm-sev-critique .pm-rule { background: var(--crit-bg); color: var(--crit); }
.pm-sev-avertissement .pm-rail { background: var(--warn); }
.pm-sev-avertissement .pm-rule { background: var(--warn-bg); color: var(--warn); }
.pm-sev-suggestion .pm-rail { background: var(--ok); }
.pm-sev-suggestion .pm-rule { background: var(--ok-bg); color: var(--ok); }

.pm-rec { display: grid; grid-template-columns: 110px 1fr; gap: 0.5rem 1rem; margin: 0; font-size: 14.5px; line-height: 1.55; }
.pm-rec dt { color: var(--muted); font-weight: 500; }
.pm-rec dd { margin: 0; color: var(--ink); }

@media (max-width: 760px) {
  .pm-verdict { grid-template-columns: auto 1fr; gap: 1rem 1.2rem; }
  .pm-counts, .pm-engine { grid-column: 1 / -1; text-align: left; }
  .pm-issue { grid-template-columns: 4px auto 1fr; gap: 0.35rem 12px; }
  .pm-msg { grid-column: 2 / -1; }
  .pm-src { display: none; }
  .pm-rec { grid-template-columns: 1fr; gap: 0.1rem; }
  .pm-rec dd { margin-bottom: 0.6rem; }
}
"""
