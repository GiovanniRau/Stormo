"""
Mini-dashboard per la previsione della domanda e la pianificazione delle scorte.
STORMO - Caso di studio: Leonardo S.p.A. - Divisione Aeronautica (magazzino ricambi).

Avvio:  streamlit run app.py
"""
import base64
import os
import sys
from statistics import NormalDist

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))
from config import ARTICOLI, DATA_VERSIONE, IMPRESA, MESI_TEST, NOME_APP, ORIZZONTE, VERSIONE  # noqa: E402
from generatore import genera_serie  # noqa: E402
from previsione import NOMI_BREVI, NOMI_METODI, confronta_metodi, previsione_futura  # noqa: E402
from scorte import TIPI_SCORTA, calcola_scorte  # noqa: E402

st.set_page_config(page_title="STORMO - Previsione della domanda e scorte",
                   page_icon=os.path.join(BASE, "assets", "jet.svg"), layout="wide")

ART = {a["codice"]: a for a in ARTICOLI}
st.session_state.setdefault("tema", "chiaro")
SCURO = st.session_state["tema"] == "scuro"
# Palette: stessi ruoli, colori diversi per il tema chiaro e per quello notturno
P = {
    "sfondo": "#0E1626" if SCURO else "#F7F8FA",
    "card": "rgba(22,34,58,.94)" if SCURO else "rgba(255,255,255,.9)",
    "bordo": "#2A3B5E" if SCURO else "#D5DCE4",
    "riga": "#22314F" if SCURO else "#E3E8EE",
    "testo": "#E6EBF2" if SCURO else "#1B2A41",
    "testo2": "#B7C3D6" if SCURO else "#3D4B61",
    "muted": "#8FA0BA" if SCURO else "#5B6B82",
    "titolo": "#F2F5FA" if SCURO else "#14213D",
    "evidenza": "#1C2C4A" if SCURO else "#E3ECF6",
    "neutro": "#3A4A68" if SCURO else "#C9D2DD",
    "barre": "#3E5F8A" if SCURO else "#B9CBE0",
    "griglia": "#22314F" if SCURO else "#E3E8EE",
}
BLU = "#5B9BD5" if SCURO else "#1F4E79"
BLU_SCURO = "#E6EBF2" if SCURO else "#14213D"      # colore "inchiostro" di linee e testi nei grafici
ROSSO = "#FF5A6E" if SCURO else "#C8102E"
GRIGIO = "#6F7F99" if SCURO else "#9AA5B4"
COLORI_SCORTE = {"Scorta ciclica": BLU, "Scorta di sicurezza": ROSSO,
                 "Scorta pipeline": GRIGIO, "Scorta anticipata": "#E8A33D"}
SPIEGAZIONI_SCORTE = {
    "Scorta ciclica": "Metà del lotto economico: i pezzi presenti in media perché si ordina a lotti.",
    "Scorta di sicurezza": "Cuscinetto contro gli errori di previsione: cresce con l'incertezza e il lead time.",
    "Scorta pipeline": "Pezzi già ordinati e in viaggio durante il lead time del fornitore.",
    "Scorta anticipata": "Pezzi accumulati prima dei picchi che la capacità mensile non riesce a coprire.",
}
MESI_IT = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
FONT = "Source Sans Pro, Segoe UI, Helvetica, Arial, sans-serif"


def svg_b64(nome):
    with open(os.path.join(BASE, "assets", nome), "rb") as f:
        return base64.b64encode(f.read()).decode()


def mese_it(d):
    return f"{MESI_IT[d.month - 1]} {d.year}"


def fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def euro(x):
    if abs(x) >= 1e6:
        return f"€ {fmt(x / 1e6, 2)} mln"
    return f"€ {fmt(x)}"


# ---------------------------------------------------------------------------
# Stile grafico
# ---------------------------------------------------------------------------

FONT_FACES = "".join(
    f"@font-face {{ font-family: 'IBM Plex Sans'; font-weight: {p}; font-style: normal; font-display: swap;"
    f" src: url(data:font/woff2;base64,{svg_b64(os.path.join('font', f'ibm-plex-sans-latin-{p}-normal.woff2'))})"
    f" format('woff2'); }}" for p in (400, 500, 600, 700))

TEMA_SCURO_CSS = """
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: var(--sfondo) !important; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"], [data-testid="stMain"] label,
[data-testid="stMain"] p, [data-testid="stMain"] li { color: var(--testo); }
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3, [data-testid="stMain"] strong {
    color: var(--titolo); }
.stTabs [data-baseweb="tab"] { color: var(--testo2); }
.stTabs [aria-selected="true"] { color: var(--accento) !important; }
[data-testid="stMain"] [data-baseweb="select"] > div, [data-testid="stMain"] [data-testid="stExpander"] details,
[data-testid="stMain"] .stDownloadButton button, [data-testid="stMain"] [data-testid="stBaseButton-secondary"] {
    background: var(--card) !important; color: var(--testo) !important; border-color: var(--bordo) !important; }
[data-testid="stMain"] [data-testid="stExpander"] summary { color: var(--testo); }
[data-testid="stMain"] [data-baseweb="tag"] { background: var(--accento) !important; }
[data-testid="stMain"] [data-baseweb="select"], [data-testid="stMain"] [data-baseweb="select"] * {
    background-color: var(--card) !important; color: var(--testo) !important; border-color: var(--bordo) !important; }
[data-testid="stMain"] [role="radiogroup"] label p { color: var(--testo) !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li { background: #16223A; color: #E6EBF2; }
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--bordo); }
[data-testid="stMain"]::before { filter: brightness(3.2) saturate(.6); opacity: .06 !important; }
""" if SCURO else ""

st.markdown(f"""
<style>
{FONT_FACES}
/* barra laterale: carattere IBM Plex Sans */
[data-testid="stSidebar"], [data-testid="stSidebar"] * {{ font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif !important; }}
[data-testid="stSidebar"] [data-testid="stIconMaterial"], [data-testid="stSidebar"] .material-symbols-rounded,
[data-testid="stSidebar"] [data-testid="stExpanderIcon"] * {{ font-family: 'Material Symbols Rounded' !important; }}
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-size: .86rem; font-weight: 500; letter-spacing: .01em; }}
/* pulsante per riaprire la barra laterale: sotto la bandiera, ben visibile */
[data-testid="stExpandSidebarButton"] {{ position: fixed !important; top: 150px !important; left: 14px !important;
    z-index: 1000002 !important; width: 40px; height: 40px; border-radius: 8px !important;
    background: #14213D !important; color: #E6EBF2 !important; border: 1px solid #2E4170 !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.25); }}
[data-testid="stExpandSidebarButton"]:hover {{ background: #22325A !important; }}
[data-testid="stExpandSidebarButton"] * {{ color: #E6EBF2 !important; }}
/* pulsante Home nella barra laterale */
.st-key-pulsante_home button {{ justify-content: flex-start; background: transparent; border: 1px solid #2E4170;
    color: #C9D6E8; font-size: .85rem; }}
.st-key-pulsante_home button:hover {{ background: rgba(141,184,227,.1); border-color: #8DB8E3; color: #FFFFFF; }}
/* selettore degli articoli a schede */
[data-testid="stSidebar"] [role="radiogroup"] {{ gap: .45rem; }}
[data-testid="stSidebar"] [role="radiogroup"] > div {{ position: relative; width: 100%; padding: .65rem .8rem;
    border: 1px solid #2E4170; border-radius: 6px; background: rgba(255,255,255,.03); cursor: pointer;
    transition: background .15s, border-color .15s; }}
[data-testid="stSidebar"] [role="radiogroup"] > div:hover {{ background: rgba(141,184,227,.08); border-color: #4C6A9E; }}
[data-testid="stSidebar"] [role="radiogroup"] > div[data-selected="true"] {{ background: rgba(141,184,227,.14);
    border-color: #8DB8E3; box-shadow: inset 4px 0 0 #8DB8E3; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] {{ margin: 0; padding: 0; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"]::before {{ content: ""; position: absolute; inset: 0; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {{ display: none; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p {{ font-weight: 600; font-size: .9rem; line-height: 1.25;
    white-space: normal; color: #E6EBF2; margin: 0; }}
[data-testid="stSidebar"] [data-testid="stRadioCaption"] {{ padding-left: 0 !important; margin-top: .2rem; }}
[data-testid="stSidebar"] [data-testid="stRadioCaption"] p {{ font-size: .72rem !important; font-weight: 500;
    letter-spacing: .07em; text-transform: uppercase; color: #8DA2C0 !important; margin: 0; }}
[data-testid="stSidebar"] [role="radiogroup"] > div[data-selected="true"] [data-testid="stRadioCaption"] p {{ color: #8DB8E3 !important; }}
:root {{ --sfondo: {P['sfondo']}; --card: {P['card']}; --bordo: {P['bordo']}; --riga: {P['riga']};
         --testo: {P['testo']}; --testo2: {P['testo2']}; --muted: {P['muted']}; --titolo: {P['titolo']};
         --neutro: {P['neutro']}; --accento: {BLU}; --evidenza: {P['evidenza']}; }}
{TEMA_SCURO_CSS}
/* interruttore del tema, in basso a destra */
.st-key-interruttore_tema {{ position: fixed; bottom: 18px; right: 22px; z-index: 1000001; width: auto !important; }}
.st-key-interruttore_tema button {{ border-radius: 999px; width: 44px; height: 44px; padding: 0;
    background: var(--card); border: 1px solid var(--bordo); color: var(--titolo);
    box-shadow: 0 4px 14px rgba(0,0,0,.18); }}
.st-key-interruttore_tema button:hover {{ border-color: var(--accento); color: var(--accento); }}
/* tabelle */
.tab-wrap {{ overflow: auto; border: 1px solid var(--bordo); border-radius: 4px; background: var(--card); margin-bottom: .8rem; }}
.tab-wrap table {{ border-collapse: collapse; width: 100%; font-size: .86rem; color: var(--testo); }}
.tab-wrap th {{ position: sticky; top: 0; background: var(--evidenza); color: var(--muted); font-weight: 600;
    text-align: left; padding: .45rem .6rem; border-bottom: 1px solid var(--bordo); white-space: nowrap; }}
.tab-wrap td {{ padding: .4rem .6rem; border-bottom: 1px solid var(--riga); text-align: right; white-space: nowrap; }}
.tab-wrap tbody th {{ position: static; background: transparent; color: var(--testo); font-weight: 500;
    border-bottom: 1px solid var(--riga); }}
.tab-wrap td:first-child, .tab-wrap td.testo {{ text-align: left; }}
.tab-wrap tr.evidenziata td, .tab-wrap tr.evidenziata th {{ background: var(--evidenza); font-weight: 700; }}
[data-testid="stMain"]::before {{
    content: ""; position: fixed; right: -2vw; top: 20vh; width: 50vw; height: 50vw;
    background: url("data:image/svg+xml;base64,{svg_b64('jet.svg')}") no-repeat center / contain;
    opacity: 0.07; transform: rotate(-30deg); pointer-events: none; z-index: 0;
}}
.tricolore {{
    position: fixed; top: 0; left: 0; width: 175px; height: 175px; z-index: 1000000;
    background: url("data:image/svg+xml;base64,{svg_b64('tricolore.svg')}") no-repeat top left / contain;
    pointer-events: none;
}}
[data-testid="stSidebarHeader"] {{ height: 8.5rem; }}
.intestazione {{ border-bottom: 2px solid {BLU}; padding-bottom: .9rem; margin-bottom: 1.2rem; }}
.intestazione .sopratitolo {{ font-size: .78rem; letter-spacing: .14em; text-transform: uppercase;
    color: var(--muted); font-weight: 600; }}
.intestazione h1 {{ font-size: 2.05rem; font-weight: 700; margin: .2rem 0 .3rem 0; padding: 0;
    color: var(--titolo); letter-spacing: -.01em; }}
.intestazione .sottotitolo {{ font-size: .95rem; color: var(--testo2); }}
[data-testid="stMetric"] {{ background: var(--card); border: 1px solid var(--bordo);
    border-left: 4px solid {BLU}; border-radius: 4px; padding: .65rem .95rem; }}
[data-testid="stMetricLabel"] p {{ font-size: .74rem; text-transform: uppercase; letter-spacing: .06em;
    color: var(--muted); font-weight: 600; }}
[data-testid="stMetricValue"] {{ font-size: 1.45rem; font-weight: 600; color: var(--titolo); }}
.stTabs [data-baseweb="tab-list"] {{ gap: .3rem; border-bottom: 1px solid var(--bordo); }}
.stTabs [data-baseweb="tab"] {{ font-weight: 600; letter-spacing: .02em; padding: .5rem 1rem; }}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{ font-size: .8rem; text-transform: uppercase;
    letter-spacing: .12em; color: #8DB8E3; font-weight: 700; margin-top: .8rem; }}
.nota {{ font-size: .84rem; color: var(--muted); margin: .1rem 0 .6rem 0; }}
.lettura {{ background: var(--card); border-left: 3px solid {BLU}; padding: .55rem .9rem;
    font-size: .88rem; color: var(--testo2); margin: .3rem 0 .8rem 0; }}
.lettura b {{ color: var(--titolo); }}
.pill {{ display: inline-block; padding: .12rem .6rem; border-radius: 999px; font-size: .74rem;
    font-weight: 700; letter-spacing: .05em; text-transform: uppercase; }}
.verde {{ background: #DDF1E4; color: #1E6B3A; }}
.giallo {{ background: #FCEFCF; color: #8A5A00; }}
.rosso {{ background: #F8DADD; color: #9B1C2C; }}
.scheda-titolo {{ font-weight: 700; font-size: 1.02rem; color: var(--titolo); margin-bottom: .1rem; }}
.scheda-sotto {{ font-size: .82rem; color: var(--muted); }}
.riga-kpi {{ display: flex; justify-content: space-between; font-size: .86rem; padding: .18rem 0;
    border-bottom: 1px solid var(--riga); }}
.riga-kpi span:last-child {{ font-weight: 600; color: var(--titolo); }}
.tipo-scorta {{ background: var(--card); border: 1px solid var(--bordo); border-radius: 4px;
    padding: .6rem .8rem; height: 100%; }}
.tipo-scorta .nome {{ font-weight: 700; font-size: .9rem; }}
.tipo-scorta .valore {{ font-size: 1.35rem; font-weight: 600; color: var(--titolo); }}
.tipo-scorta .descr {{ font-size: .78rem; color: var(--muted); }}
</style>
<div class="tricolore"></div>
""", unsafe_allow_html=True)


def stile(fig, altezza, titolo_y=None, legenda=True):
    fig.update_layout(height=altezza, template="simple_white", font=dict(family=FONT, size=13, color=P["testo"]),
                      paper_bgcolor=P["card"].replace(".94", "0.94").replace(".9)", "0.9)"),
                      plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=30, l=10, r=10, b=10), yaxis_title=titolo_y, showlegend=legenda,
                      legend=dict(orientation="h", y=-0.16, x=0, font=dict(size=12, color=P["testo"])),
                      hoverlabel=dict(font_family=FONT))
    fig.update_yaxes(showgrid=True, gridcolor=P["griglia"], linecolor=P["bordo"], tickcolor=P["bordo"])
    fig.update_xaxes(linecolor=P["bordo"], tickcolor=P["bordo"])
    fig.update_traces(mode="lines", selector=dict(type="scatter"))
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    return fig


def tabella(dati, indice=True, altezza=None):
    """Tabella HTML che segue i colori del tema (chiaro o notturno)."""
    sty = dati if hasattr(dati, "to_html") and hasattr(dati, "data") else dati.style
    testo = [c for c in sty.data.columns
             if sty.data[c].dtype == object or pd.api.types.is_string_dtype(sty.data[c])]
    if testo:
        sty = sty.set_properties(subset=testo, **{"text-align": "left"})
    if not indice:
        sty = sty.hide(axis="index")
    html = "".join(r.strip() for r in sty.to_html().splitlines() if r.strip())
    alt = f"max-height:{altezza}px;" if altezza else ""
    st.markdown(f'<div class="tab-wrap" style="{alt}">{html}</div>', unsafe_allow_html=True)


def cambia_tema():
    st.session_state["tema"] = "chiaro" if st.session_state["tema"] == "scuro" else "scuro"


with st.container(key="interruttore_tema"):
    st.button("", icon=":material/light_mode:" if SCURO else ":material/dark_mode:", on_click=cambia_tema,
              help="Passa al tema chiaro" if SCURO else "Passa al tema notturno", key="pulsante_tema")


def lettura(testo):
    st.markdown(f'<div class="lettura"><b>Come leggere il grafico.</b> {testo}</div>', unsafe_allow_html=True)



# ---------------------------------------------------------------------------
# Parametri di scenario in unità reali (uno scenario per ciascun articolo)
# ---------------------------------------------------------------------------
def var_base(a):        # variabilità mensile in % (per l'articolo intermittente: dispersione dei lotti)
    return a["cv_rumore"] * 100 if a["cv_rumore"] > 0 else 50.0


def picco_base(a):      # picco stagionale in % sopra la media
    return max(a["profilo"]) * a["stagionalita"] * 100 if a["profilo"] else 0.0


def limite_trend(a):
    return max(2 * abs(a["trend"]), 0.05 * a["livello"], 0.2)


def default_scenario(a):
    return {"var": var_base(a), "trend": float(a["trend"]), "picco": picco_base(a),
            "lt": float(a["lead_time"]), "ls": a["livello_servizio"] * 100}


for a in ARTICOLI:
    for k, v in default_scenario(a).items():
        st.session_state.setdefault(f"{k}_{a['codice']}", v)


def parametri(c, base=False):
    a = ART[c]
    s = default_scenario(a) if base else {k: st.session_state[f"{k}_{c}"] for k in default_scenario(a)}
    k_stag = s["picco"] / picco_base(a) if picco_base(a) > 0 else 1.0
    return (s["var"] / var_base(a), s["trend"], k_stag, s["lt"], s["ls"] / 100)


def ripristina(c):
    for k, v in default_scenario(ART[c]).items():
        st.session_state[f"{k}_{c}"] = v


@st.cache_data(show_spinner=False)
def analizza(codice, k_var, trend, k_stag, lt, ls, criterio, n, alpha):
    art = ART[codice]
    serie = genera_serie(art, k_variabilita=k_var, k_stagionalita=k_stag, trend=trend)
    tab, migliore, prev_test = confronta_metodi(serie, MESI_TEST, criterio, n=n, alpha=alpha)
    futuro = {m: previsione_futura(serie, m, ORIZZONTE, n=n, alpha=alpha) for m in NOMI_METODI}
    scorte = calcola_scorte(futuro[migliore], tab.loc[migliore, "RMSE"], art,
                            lead_time=lt, livello_servizio=ls)
    return serie, tab, migliore, prev_test, futuro, scorte


def semaforo(wape):
    if wape < 15:
        return "verde", "Prevedibile"
    if wape < 40:
        return "giallo", "Attenzione"
    return "rosso", "Critico"


# ---------------------------------------------------------------------------
# Pagina di benvenuto
# ---------------------------------------------------------------------------
st.session_state.setdefault("entrato", False)
if not st.session_state["entrato"]:
    if st.session_state.pop("torna_su", False):
        script = """<script>
        const d = window.parent.document;
        ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', 'section.main'].forEach(s => {
            const e = d.querySelector(s); if (e) e.scrollTo({top: 0, behavior: "instant"}); });
        window.parent.scrollTo(0, 0);
        </script>"""
        if hasattr(st, "iframe"):                      # versioni recenti di Streamlit
            st.iframe(script, height=1)
        else:                                          # versioni precedenti
            import streamlit.components.v1 as components
            components.html(script, height=0)
    st.markdown("""<style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display:none}
    .benv-pre {font-size:1.05rem !important; letter-spacing:.42em; text-transform:uppercase; color:var(--titolo);
               opacity:.38; font-weight:600; margin:0 0 .35rem .3rem}
    .benv-nome {font-size:4rem !important; font-weight:800 !important; letter-spacing:.24em; color:var(--titolo); margin:0; line-height:1.05}
    .benv-sotto {font-size:1.2rem !important; color:var(--testo2); margin:.7rem 0 1.4rem 0; max-width:900px}
    .benv-tit {font-size:.8rem; letter-spacing:.14em; text-transform:uppercase; color:var(--accento); font-weight:700;
               border-bottom:2px solid var(--accento); padding-bottom:.3rem; margin:1.4rem 0 .9rem 0}
    .passo {background:var(--card); border:1px solid var(--bordo); border-top:3px solid var(--accento);
            padding:.9rem 1rem; height:100%}
    .passo .n {font-size:1.6rem; font-weight:800; color:var(--neutro)}
    .passo .t {font-weight:700; color:var(--titolo); margin:.1rem 0 .3rem 0}
    .passo .d {font-size:.86rem; color:var(--muted)}
    .dato {display:flex; justify-content:space-between; padding:.38rem 0; border-bottom:1px solid var(--riga); font-size:.92rem}
    .dato span:first-child {color:var(--muted)} .dato span:last-child {font-weight:600; color:var(--titolo); text-align:right}
    .piede {text-align:center; font-size:.75rem; color:var(--muted); margin-top:2.5rem; letter-spacing:.06em}
    </style>""", unsafe_allow_html=True)
    st.markdown(f"""<div style="margin-top:1rem"><div class="benv-pre">Benvenuto in</div><div class="benv-nome">{NOME_APP}</div>
    <div class="benv-sotto">Piattaforma di analisi predittiva per l'ottimizzazione delle scorte
    nel supporto logistico aeronautico</div><div style="width:90px;height:4px;background:#1F4E79"></div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="benv-tit">Che cosa fa il programma</div>', unsafe_allow_html=True)
    passi = [("01", "Legge la domanda",
              "Raccoglie quattro anni di richieste di ricambi e ne riconosce l'andamento: stabile, in crescita, "
              "stagionale o irregolare."),
             ("02", "Sceglie la previsione migliore",
              "Mette alla prova cinque metodi di previsione sugli ultimi dodici mesi e, per ogni ricambio, adotta "
              "quello che sbaglia meno."),
             ("03", "Calcola le scorte",
              "Stabilisce quanti pezzi tenere a magazzino e quando riordinarli, per non lasciare un velivolo a terra "
              "senza immobilizzare risorse inutili."),
             ("04", "Simula gli imprevisti",
              "Mostra subito cosa succede a scorte e costi se il fornitore rallenta, la domanda cambia o si "
              "chiede più sicurezza.")]
    for col, (n, t, d) in zip(st.columns(4), passi):
        col.markdown(f'<div class="passo"><div class="n">{n}</div><div class="t">{t}</div><div class="d">{d}</div></div>',
                     unsafe_allow_html=True)

    st.markdown('<div class="benv-tit">L\'impresa</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    gruppo = [("Società", "Leonardo S.p.A."), ("Settore", "Aerospazio, difesa e sicurezza"),
              ("Sede", "Roma"), ("Presenza", "Italia e principali mercati internazionali")]
    divisione = [("Divisione", "Aeronautica"), ("Attività", "Velivoli militari e aerostrutture"),
                 ("Programmi", "Eurofighter, F-35, M-346, C-27J"),
                 ("Ambito analizzato", "Magazzino ricambi del supporto logistico")]
    for col, tit, righe in ((c1, "Gruppo", gruppo), (c2, "Divisione", divisione)):
        col.markdown(f"**{tit}**" + "".join(f'<div class="dato"><span>{k}</span><span>{v}</span></div>' for k, v in righe),
                     unsafe_allow_html=True)
    st.markdown('<p class="nota" style="margin-top:.8rem">I dati di domanda sono generati e coerenti con il contesto: '
                'i dati reali della Difesa non sono pubblici.</p>', unsafe_allow_html=True)

    for _c in ART:                       # prepara i calcoli in anticipo: la transizione sarà immediata
        analizza(_c, *parametri(_c, base=True), "RMSE", 3, 0.30)
    st.write("")
    _, cb, _ = st.columns([2, 1, 2])
    if cb.button("Accedi alla dashboard", type="primary", width="stretch"):
        st.session_state["entrato"] = True
        st.session_state["transizione"] = True
        st.rerun()
    st.markdown(f'<div class="piede">{NOME_APP} &middot; versione {VERSIONE} &middot; 2026</div>', unsafe_allow_html=True)
    st.stop()




# ---------------------------------------------------------------------------
# Barra laterale
# ---------------------------------------------------------------------------
def torna_home():
    st.session_state["entrato"] = False
    st.session_state["torna_su"] = True


st.sidebar.button("Torna alla home", icon=":material/home:", on_click=torna_home, width="stretch",
                  key="pulsante_home")
st.sidebar.markdown("## Articolo")
codice = st.sidebar.radio("Ricambio analizzato", list(ART), key="articolo", label_visibility="collapsed",
                          format_func=lambda c: ART[c]["nome"],
                          captions=[f"{c} · {ART[c]['andamento']}" for c in ART])
art = ART[codice]
u = art["unita"]

st.sidebar.markdown("## Scenario")
st.sidebar.slider("Variabilità mensile della domanda (± %)", 0.0, float(round(var_base(art) * 3)), key=f"var_{codice}",
                  step=1.0, format="%.0f %%",
                  help="Quanto le richieste oscillano in modo casuale da un mese all'altro. "
                       "Per il modulo avionico indica la dispersione della dimensione dei lotti.")
lim = round(limite_trend(art), 2)
st.sidebar.slider(f"Trend ({u} in più o in meno ogni mese)", -lim, lim, key=f"trend_{codice}",
                  step=round(lim / 40, 2) or 0.01, format="%.2f")
if picco_base(art) > 0:
    st.sidebar.slider("Picco stagionale (% sopra la media)", 0.0, float(round(picco_base(art) * 2)), key=f"picco_{codice}",
                      step=5.0, format="%.0f %%", help="Di quanto la domanda del mese di punta supera la media.")
else:
    st.sidebar.caption("Picco stagionale: non presente per questo articolo.")
st.sidebar.slider("Lead time del fornitore (mesi)", 0.5, 12.0, key=f"lt_{codice}", step=0.5, format="%.1f mesi")
st.sidebar.caption(f"Pari a circa {fmt(st.session_state[f'lt_{codice}'] * 4.33)} settimane.")
st.sidebar.slider("Livello di servizio (%)", 80.0, 99.5, key=f"ls_{codice}", step=0.5, format="%.1f %%",
                  help="Probabilità di non restare senza pezzi durante il lead time.")
st.sidebar.button("Ripristina caso base", on_click=ripristina, args=(codice,), width="stretch")

with st.sidebar.expander("Impostazioni dei metodi previsionali"):
    n = st.slider("Periodi della media mobile (n)", 2, 12, 3)
    alpha = st.slider("Costante di livellamento α", 0.05, 0.95, 0.30, 0.05)
    criterio = st.selectbox("Criterio di scelta del metodo migliore", ["RMSE", "MAE", "WAPE %", "MAPE %"])

st.sidebar.markdown(f'<p style="font-size:.75rem;color:#8DA2C0;margin-top:1.5rem">Versione {VERSIONE} '
                    f'&middot; {DATA_VERSIONE}</p>', unsafe_allow_html=True)

RIS = {c: analizza(c, *parametri(c), criterio, n, alpha) for c in ART}
RIS_BASE = {c: analizza(c, *parametri(c, base=True), criterio, n, alpha) for c in ART}
modificato = {c: parametri(c) != parametri(c, base=True) for c in ART}

serie, tab, migliore, prev_test, futuro, scorte = RIS[codice]

if st.session_state.pop("transizione", False):
    st.markdown(f"""<style>
    .transizione {{ position: fixed; inset: 0; z-index: 2000000; pointer-events: none;
                    animation: nascondi 0s 1.9s forwards; }}
    .tendina {{ position: absolute; inset: 0; background: var(--sfondo);
                animation: swipe 1.35s .25s cubic-bezier(.65,0,.35,1) forwards; }}
    .volo {{ position: absolute; top: 38vh; left: -340px; width: 300px; height: 300px;
             background: url("data:image/svg+xml;base64,{svg_b64('jet.svg')}") no-repeat center / contain;
             transform: rotate(90deg); filter: drop-shadow(0 18px 18px rgba(20,33,61,.25));
             animation: volo 1.35s .25s cubic-bezier(.65,0,.35,1) forwards; }}
    .scia {{ position: absolute; top: calc(38vh + 150px); left: 0; height: 2px; width: 0;
             background: linear-gradient(90deg, rgba(31,78,121,0), rgba(31,78,121,.45));
             animation: scia 1.35s .25s cubic-bezier(.65,0,.35,1) forwards; }}
    @keyframes swipe {{ to {{ transform: translateX(100vw); }} }}
    @keyframes volo {{ to {{ left: calc(100vw + 40px); }} }}
    @keyframes scia {{ 0% {{ width: 0; opacity: 1 }} 80% {{ opacity: 1 }} 100% {{ width: 100vw; opacity: 0 }} }}
    @keyframes nascondi {{ to {{ visibility: hidden; }} }}
    </style>
<div class="transizione"><div class="tendina"></div><div class="scia"></div><div class="volo"></div></div>""",
                unsafe_allow_html=True)


serie_b, tab_b, migliore_b, _, futuro_b, scorte_b = RIS_BASE[codice]

# ---------------------------------------------------------------------------
# Intestazione
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="intestazione">
  <div class="sopratitolo">STORMO &nbsp;|&nbsp; Supporto logistico ricambi &nbsp;|&nbsp; Versione {VERSIONE}</div>
  <h1>Previsione della domanda e pianificazione delle scorte</h1>
  <div class="sottotitolo"><b>{IMPRESA['nome']}</b> &mdash; {IMPRESA['settore']}</div>
</div>""", unsafe_allow_html=True)

schede = st.tabs(["Panoramica", "Domanda e previsioni", "Accuratezza dei metodi", "Scorte",
                  "Confronto scenari", "Analisi di sensibilità", "Impresa e dati"])


def kpi_articolo():
    st.markdown(f"**{art['nome']}** &nbsp;·&nbsp; andamento {art['andamento'].lower()}"
                + ("&nbsp;·&nbsp; <span class='pill giallo'>scenario modificato</span>" if modificato[codice] else ""),
                unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 0.9, 1, 1, 1])
    d = lambda v, vb: fmt(v - vb) if modificato[codice] and round(v - vb) != 0 else None  # noqa: E731
    c1.metric("Metodo migliore", NOMI_BREVI[migliore])
    c2.metric("Errore medio (WAPE)", f"{fmt(tab.loc[migliore, 'WAPE %'], 1)} %")
    c3.metric("Punto di riordino", f"{fmt(scorte['Punto di riordino'])} {u}",
              d(scorte["Punto di riordino"], scorte_b["Punto di riordino"]), delta_color="inverse")
    c4.metric("Scorta media", f"{fmt(scorte['Scorta media totale'])} {u}",
              d(scorte["Scorta media totale"], scorte_b["Scorta media totale"]), delta_color="inverse")
    c5.metric("Valore scorta", euro(scorte["Valore scorta media (EUR)"]))


# ---------------------------------------------------------------------------
# 0. Panoramica
# ---------------------------------------------------------------------------
with schede[0]:
    tot_val = sum(RIS[c][5]["Valore scorta media (EUR)"] for c in ART)
    tot_cost = sum(RIS[c][5]["Costo annuo totale (EUR)"] for c in ART)
    critici = sum(semaforo(RIS[c][1].loc[RIS[c][2], "WAPE %"])[0] == "rosso" for c in ART)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Articoli monitorati", len(ART))
    k2.metric("Valore totale delle scorte", euro(tot_val))
    k3.metric("Costo annuo di gestione", euro(tot_cost))
    k4.metric("Articoli critici", critici)
    st.markdown('<p class="nota">Semaforo basato sull\'errore di previsione del metodo migliore (WAPE): '
                '<span class="pill verde">Prevedibile</span> sotto il 15%, '
                '<span class="pill giallo">Attenzione</span> tra 15% e 40%, '
                '<span class="pill rosso">Critico</span> oltre il 40%.</p>', unsafe_allow_html=True)

    for riga in (ARTICOLI[:2], ARTICOLI[2:]):
        cols = st.columns(2)
        for col, a in zip(cols, riga):
            c = a["codice"]
            s, tb, mg, _, fu, sc = RIS[c]
            colore, etichetta = semaforo(tb.loc[mg, "WAPE %"])
            with col.container(border=True):
                st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center">
                    <div><div class="scheda-titolo">{a['nome']}</div>
                    <div class="scheda-sotto">{c} · andamento {a['andamento'].lower()}
                    {'· scenario modificato' if modificato[c] else ''}</div></div>
                    <span class="pill {colore}">{etichetta}</span></div>""", unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_scatter(x=s.index, y=s.values, line=dict(color=BLU_SCURO, width=1.8), name="Storico",
                                hovertemplate="%{x|%m/%Y}: %{y:.0f}<extra></extra>")
                fig.add_scatter(x=fu[mg].index, y=fu[mg].values, line=dict(color=ROSSO, width=2.2), name="Previsione",
                                hovertemplate="%{x|%m/%Y}: %{y:.1f}<extra></extra>")
                stile(fig, 150, legenda=False).update_layout(margin=dict(t=5, l=5, r=5, b=5))
                fig.update_xaxes(showticklabels=True, tickformat="%Y")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"spark_{c}")
                righe = [("Metodo migliore", NOMI_METODI[mg]),
                         ("Errore medio (WAPE)", f"{fmt(tb.loc[mg, 'WAPE %'], 1)} %"),
                         ("Domanda prevista (12 mesi)", f"{fmt(sc['Domanda annua prevista'])} {a['unita']}"),
                         ("Punto di riordino", f"{fmt(sc['Punto di riordino'])} {a['unita']}"),
                         ("Scorta media / copertura", f"{fmt(sc['Scorta media totale'])} {a['unita']} · "
                                                      f"{fmt(sc['Copertura (mesi)'], 1)} mesi"),
                         ("Valore della scorta", euro(sc["Valore scorta media (EUR)"]))]
                st.markdown("".join(f'<div class="riga-kpi"><span>{k}</span><span>{v}</span></div>'
                                    for k, v in righe), unsafe_allow_html=True)
    lettura("Ogni riquadro riassume un ricambio: la linea scura è la domanda degli ultimi quattro anni, "
            "quella rossa la previsione dei prossimi dodici mesi. Per analizzare un articolo selezionalo "
            "nella barra laterale e apri le schede successive.")

# ---------------------------------------------------------------------------
# 1. Domanda e previsioni
# ---------------------------------------------------------------------------
with schede[1]:
    kpi_articolo()
    altri = st.multiselect("Confronta con altri metodi (facoltativo)", [m for m in NOMI_METODI if m != migliore],
                           format_func=lambda m: NOMI_METODI[m], placeholder="Seleziona uno o più metodi")
    lettura(f"La <b>linea {'bianca' if SCURO else 'blu scura'}</b> è la domanda reale. Nella <b>fascia grigia</b> (ultimi {MESI_TEST} mesi) "
            "il programma verifica i metodi: la <b>linea tratteggiata</b> mostra cosa avrebbero previsto mese "
            "per mese. A destra della linea <b>Oggi</b> c'è la <b>previsione rossa</b> per i prossimi "
            f"{ORIZZONTE} mesi; la <b>fascia rossa chiara</b> indica l'incertezza al livello di servizio scelto.")
    z = NormalDist().inv_cdf(scorte["Livello di servizio"])
    f = futuro[migliore]
    banda = z * tab.loc[migliore, "RMSE"]
    oggi = serie.index[-1]

    fig = go.Figure()
    fig.add_vrect(x0=prev_test.index[0] - pd.Timedelta(days=15), x1=oggi + pd.Timedelta(days=15),
                  fillcolor=P["evidenza"], opacity=0.7, line_width=0, layer="below",
                  annotation_text="Periodo di verifica", annotation_position="top left",
                  annotation_font=dict(size=12, color=P["muted"]))
    if modificato[codice]:
        fig.add_scatter(x=serie_b.index, y=serie_b.values, name="Domanda caso base",
                        line=dict(color=GRIGIO, width=1.5, dash="dot"), hovertemplate="%{y:.0f}")
    fig.add_scatter(x=serie.index, y=serie.values, name="Domanda reale", line=dict(color=BLU_SCURO, width=2.6),
                    hovertemplate="%{y:.0f}")
    for m, col in zip([migliore] + altri, [ROSSO, "#2E7D5B", "#E8A33D", "#6B5B95", "#1F77B4", "#8C564B"]):
        fig.add_scatter(x=prev_test.index, y=prev_test[m], name=f"Verifica: {NOMI_BREVI[m]}",
                        line=dict(color=col, width=1.8, dash="dash"), hovertemplate="%{y:.1f}")
        if m != migliore:
            fig.add_scatter(x=futuro[m].index, y=futuro[m].values, name=f"Previsione: {NOMI_BREVI[m]}",
                            line=dict(color=col, width=1.8), hovertemplate="%{y:.1f}")
    fig.add_scatter(x=list(f.index) + list(f.index[::-1]),
                    y=list(f.values + banda) + list(np.clip(f.values - banda, 0, None)[::-1]),
                    fill="toself", fillcolor="rgba(200,16,46,0.12)", line=dict(width=0),
                    name="Intervallo di incertezza", hoverinfo="skip")
    fig.add_scatter(x=[oggi] + list(f.index), y=[serie.values[-1]] + list(f.values),
                    name=f"Previsione: {NOMI_BREVI[migliore]}", line=dict(color=ROSSO, width=3),
                    hovertemplate="%{y:.1f}")
    fig.add_vline(x=oggi, line=dict(color=BLU_SCURO, width=1.2, dash="dot"))
    fig.add_annotation(x=oggi, y=1.02, yref="paper", text=f"Oggi ({mese_it(oggi)})", showarrow=False,
                       font=dict(size=12, color=BLU_SCURO), xanchor="left")
    stile(fig, 480, f"Domanda ({u} al mese)").update_layout(hovermode="x unified")
    fig.update_xaxes(hoverformat="%m/%Y", dtick="M6", tickformat="%m/%Y")
    st.plotly_chart(fig)

    st.markdown(f"**Previsione mensile con il metodo migliore ({NOMI_METODI[migliore]})**")
    tabp = pd.DataFrame({"Previsione": f.values, "Minimo": np.clip(f.values - banda, 0, None),
                         "Massimo": f.values + banda}, index=[mese_it(d) for d in f.index]).T
    tabella(tabp.style.format(lambda v: fmt(v)))

# ---------------------------------------------------------------------------
# 2. Accuratezza
# ---------------------------------------------------------------------------
with schede[2]:
    kpi_articolo()
    lettura(f"Ogni barra è l'errore medio commesso da un metodo nei {MESI_TEST} mesi di verifica, misurato con "
            f"l'indicatore <b>{criterio}</b>. <b>Barra più corta = previsione più accurata.</b> "
            "Il metodo evidenziato in blu è quello scelto per calcolare le scorte.")
    t = tab.sort_values(criterio, ascending=False)
    fig = go.Figure(go.Bar(y=t["Metodo"], x=t[criterio], orientation="h",
                           marker_color=[BLU if i == migliore else P["neutro"] for i in t.index],
                           text=[fmt(v, 1) for v in t[criterio]], textposition="outside",
                           hovertemplate="%{y}: %{x:.2f}<extra></extra>"))
    stile(fig, 360, legenda=False).update_layout(xaxis_title=f"{criterio} (più basso è meglio)")
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=P["griglia"])
    st.plotly_chart(fig)

    tt = tab.copy().sort_values(criterio)
    tt.insert(0, "Scelto", ["Sì" if i == migliore else "" for i in tt.index])
    tabella(tt.style.format({c: (lambda v: fmt(v, 2)) for c in tt.columns if c not in ("Metodo", "Scelto")})
                 .apply(lambda r: ["font-weight: 700; background-color: var(--evidenza)" if r.name == migliore else ""
                                   for _ in r], axis=1), indice=False)
    with st.expander("Significato degli indicatori di errore"):
        st.markdown("- **ME (bias)**: errore medio con segno; se positivo il metodo sottostima, se negativo sovrastima.\n"
                    "- **MAE**: errore assoluto medio, nella stessa unità della domanda.\n"
                    "- **RMSE**: radice dell'errore quadratico medio; penalizza gli errori grandi. È usato per la "
                    "scorta di sicurezza.\n"
                    "- **MAPE**: errore percentuale medio (esclusi i mesi con domanda zero).\n"
                    "- **WAPE**: errore assoluto totale diviso per la domanda totale; adatto anche alla domanda "
                    "intermittente.")

    st.markdown("**Metodo scelto per ciascun articolo**")
    righe = [{"Articolo": ART[c]["nome"], "Andamento": ART[c]["andamento"],
              "Metodo migliore": NOMI_METODI[RIS[c][2]], criterio: round(RIS[c][1].loc[RIS[c][2], criterio], 2),
              "WAPE %": round(RIS[c][1].loc[RIS[c][2], "WAPE %"], 1)} for c in ART]
    tabella(pd.DataFrame(righe).loc[:, lambda d: ~d.columns.duplicated()], indice=False)

# ---------------------------------------------------------------------------
# 3. Scorte
# ---------------------------------------------------------------------------
with schede[3]:
    kpi_articolo()
    cols = st.columns(4)
    for col, tipo in zip(cols, TIPI_SCORTA):
        delta = scorte[tipo] - scorte_b[tipo]
        var = (f"<span style='font-size:.8rem;color:{ROSSO if delta > 0 else '#1E6B3A'}'> "
               f"({'+' if delta > 0 else ''}{fmt(delta)} vs base)</span>") if modificato[codice] and round(delta) else ""
        col.markdown(f"""<div class="tipo-scorta"><div class="nome" style="color:{COLORI_SCORTE[tipo]}">
            &#9632; {tipo}</div><div class="valore">{fmt(scorte[tipo])} {u}{var}</div>
            <div class="descr">{SPIEGAZIONI_SCORTE[tipo]}</div></div>""", unsafe_allow_html=True)

    st.write("")
    lettura("Ogni barra è la scorta media totale, divisa nelle quattro tipologie. La lunghezza dei tratti colorati "
            "indica quanti pezzi servono per ciascuna ragione e la percentuale indica il peso sul totale. "
            "Confrontando le due barre si vede quale componente cambia nello scenario.")
    fig = go.Figure()
    casi = ["Scenario", "Caso base"] if modificato[codice] else ["Caso base"]
    dati = {"Caso base": scorte_b, "Scenario": scorte}
    for tipo in TIPI_SCORTA:
        vals = [dati[cs][tipo] for cs in casi]
        tot = [dati[cs]["Scorta media totale"] for cs in casi]
        fig.add_bar(y=casi, x=vals, name=tipo, orientation="h", marker_color=COLORI_SCORTE[tipo],
                    text=[f"{fmt(v)} ({fmt(v / tt * 100)}%)" if tt and v / tt > 0.06 else "" for v, tt in zip(vals, tot)],
                    textposition="inside", insidetextanchor="middle",
                    hovertemplate=f"{tipo}: %{{x:.0f}} {u}<extra></extra>")
    for cs in casi:
        fig.add_annotation(y=cs, x=dati[cs]["Scorta media totale"], text=f"<b>{fmt(dati[cs]['Scorta media totale'])}</b>",
                           showarrow=False, xanchor="left", xshift=6)
    stile(fig, 190 + 90 * len(casi)).update_layout(barmode="stack", xaxis_title=f"Scorta media ({u})",
                                                   legend=dict(y=1.02, yanchor="bottom", traceorder="normal"),
                                                   margin=dict(t=50))
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=P["griglia"])
    st.plotly_chart(fig)

    if picco_base(art) > 0 or scorte["Scorta anticipata"] > 0:
        st.markdown("**Scorta anticipata mese per mese**")
        lettura("Le barre azzurre sono la domanda prevista; la linea tratteggiata è la quantità massima che il "
                "fornitore riesce a consegnare in un mese. Quando la domanda supera la linea, i pezzi mancanti "
                "vanno acquistati nei mesi precedenti: l'area arancione è la scorta accumulata in anticipo.")
        prof = scorte["_profilo_anticipata"]
        fig = go.Figure()
        fig.add_bar(x=prof.index, y=futuro[migliore].values, name="Domanda prevista", marker_color=P["barre"],
                    hovertemplate="%{y:.0f}")
        fig.add_scatter(x=prof.index, y=prof.values, name="Scorta anticipata a fine mese", fill="tozeroy",
                        line=dict(color="#E8A33D", width=2), fillcolor="rgba(232,163,61,0.35)",
                        hovertemplate="%{y:.0f}")
        fig.add_scatter(x=prof.index, y=[scorte["_capacita"]] * len(prof), name="Capacità mensile del fornitore",
                        line=dict(color=BLU_SCURO, dash="dash"), hovertemplate="%{y:.0f}")
        stile(fig, 360, u).update_layout(hovermode="x unified")
        fig.update_xaxes(hoverformat="%m/%Y", tickformat="%m/%Y", dtick="M1")
        st.plotly_chart(fig)

    with st.expander("Dettaglio dei calcoli"):
        voci = ["Domanda annua prevista", "Lead time (mesi)", "Livello di servizio", "EOQ (lotto economico)",
                "Punto di riordino"] + TIPI_SCORTA + ["Scorta media totale", "Copertura (mesi)",
                                                      "Valore scorta media (EUR)", "Costo annuo totale (EUR)"]
        df = pd.DataFrame({"Caso base": [scorte_b[v] for v in voci], "Scenario": [scorte[v] for v in voci]}, index=voci)
        df["Variazione %"] = (df["Scenario"] / df["Caso base"].replace(0, np.nan) - 1) * 100
        tabella(df.style.format(lambda v: "–" if pd.isna(v) else fmt(v, 2)))

# ---------------------------------------------------------------------------
# 4. Confronto scenari
# ---------------------------------------------------------------------------
with schede[4]:
    lettura("Ogni ricambio ha un proprio scenario, impostato selezionandolo nella barra laterale. Le scorte sono "
            "espresse in <b>euro</b>, così articoli con unità diverse diventano confrontabili. Per ogni articolo la "
            "barra superiore è il caso base e quella inferiore lo scenario.")
    righe = []
    for c in ART:
        for caso, r in (("Caso base", RIS_BASE[c][5]), ("Scenario", RIS[c][5])):
            righe.append({"Articolo": c, "Caso": caso, **{tp: r[tp] * ART[c]["costo_unitario"] for tp in TIPI_SCORTA},
                          "Totale": r["Valore scorta media (EUR)"], "Costo annuo": r["Costo annuo totale (EUR)"]})
    dfc = pd.DataFrame(righe)
    codici = list(ART)
    fig = make_subplots(rows=2, cols=2, subplot_titles=[ART[c]["nome"] for c in codici],
                        horizontal_spacing=0.14, vertical_spacing=0.2)
    for i, c in enumerate(codici):
        d = dfc[dfc["Articolo"] == c]
        for tipo in TIPI_SCORTA:
            fig.add_bar(y=d["Caso"], x=d[tipo], name=tipo, orientation="h", marker_color=COLORI_SCORTE[tipo],
                        legendgroup=tipo, showlegend=(i == 0), row=i // 2 + 1, col=i % 2 + 1,
                        hovertemplate=f"{tipo}: € %{{x:,.0f}}<extra></extra>")
        fig.update_xaxes(range=[0, d["Totale"].max() * 1.32], row=i // 2 + 1, col=i % 2 + 1)
        for _, r in d.iterrows():
            fig.add_annotation(y=r["Caso"], x=r["Totale"], text=f"<b>{euro(r['Totale'])}</b>", showarrow=False,
                               xanchor="left", xshift=4, font=dict(size=11), row=i // 2 + 1, col=i % 2 + 1)
    stile(fig, 560).update_layout(barmode="stack", legend=dict(y=1.08, yanchor="bottom", traceorder="normal"),
                                  margin=dict(t=80, r=20))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=P["griglia"], tickprefix="€ ", tickformat="~s")
    fig.update_annotations(font_size=12)
    st.plotly_chart(fig)
    st.markdown('<p class="nota">Ogni riquadro ha una propria scala: il kit F-35 vale molto di più degli altri '
                'articoli, e su un\'unica scala gli altri non sarebbero leggibili.</p>', unsafe_allow_html=True)

    sint = dfc.pivot(index="Articolo", columns="Caso", values=["Totale", "Costo annuo"])
    sint = sint[[("Totale", "Caso base"), ("Totale", "Scenario"), ("Costo annuo", "Caso base"),
                 ("Costo annuo", "Scenario")]]
    sint.columns = ["Totale - Caso base", "Totale - Scenario", "Costo base", "Costo scenario"]
    sint["Variazione valore %"] = (sint["Totale - Scenario"] / sint["Totale - Caso base"] - 1) * 100
    sint.loc["TOTALE"] = sint.sum()
    sint.loc["TOTALE", "Variazione valore %"] = (sint.loc["TOTALE", "Totale - Scenario"]
                                                 / sint.loc["TOTALE", "Totale - Caso base"] - 1) * 100
    sint.columns = ["Valore scorta - base (€)", "Valore scorta - scenario (€)", "Costo annuo - base (€)",
                    "Costo annuo - scenario (€)", "Variazione valore %"]
    tabella(sint.style.format(lambda v: fmt(v)).format(lambda v: f"{'+' if v > 0 else ''}{fmt(v, 1)} %",
                                                            subset=["Variazione valore %"]))


# ---------------------------------------------------------------------------
# 5. Analisi di sensibilità: più scenari a confronto
# ---------------------------------------------------------------------------
with schede[5]:
    st.markdown(f"**{art['nome']}** &nbsp;·&nbsp; andamento {art['andamento'].lower()}", unsafe_allow_html=True)
    st.markdown('<p class="nota">Si fa variare un solo parametro alla volta, lasciando tutti gli altri al caso base, '
                'e si confrontano scorte e costi di tutti gli scenari insieme.</p>', unsafe_allow_html=True)
    b = default_scenario(art)
    opzioni = {
        "Lead time del fornitore": ("lt", [0.5, 1, 2, 3, 4, 6], lambda v: f"{fmt(v, 1)} mesi"),
        "Livello di servizio": ("ls", [90, 95, 97.5, 99, 99.5], lambda v: f"{fmt(v, 1)} %"),
        "Variabilità della domanda": ("var", [round(b["var"] * k, 1) for k in (0.5, 1, 1.5, 2, 3)],
                                      lambda v: f"± {fmt(v)} %"),
    }
    if picco_base(art) > 0:
        opzioni["Picco stagionale"] = ("picco", [round(b["picco"] * k) for k in (0.5, 0.75, 1, 1.25, 1.5)],
                                       lambda v: f"+{fmt(v)} %")
    scelta = st.radio("Parametro da analizzare", list(opzioni), horizontal=True)
    chiave, valori, etichetta = opzioni[scelta]
    if b[chiave] not in valori:
        valori = sorted(valori + [b[chiave]])

    righe = []
    for v in valori:
        s = dict(b)
        s[chiave] = v
        k_stag = s["picco"] / picco_base(art) if picco_base(art) > 0 else 1.0
        sc = analizza(codice, s["var"] / var_base(art), s["trend"], k_stag, s["lt"], s["ls"] / 100,
                      criterio, n, alpha)[5]
        righe.append({"Scenario": etichetta(v) + (" (base)" if v == b[chiave] else ""), "valore": v,
                      **{tp: sc[tp] for tp in TIPI_SCORTA}, "Scorta media totale": sc["Scorta media totale"],
                      "Punto di riordino": sc["Punto di riordino"],
                      "Valore scorta (€)": sc["Valore scorta media (EUR)"],
                      "Costo annuo (€)": sc["Costo annuo totale (EUR)"]})
    dfs = pd.DataFrame(righe)
    base_row = dfs[dfs["valore"] == b[chiave]].iloc[0]
    dfs["Variazione costo"] = (dfs["Costo annuo (€)"] / base_row["Costo annuo (€)"] - 1) * 100

    lettura(f"Ogni colonna è uno scenario con un diverso valore di <b>{scelta.lower()}</b>; i colori mostrano come "
            "si compone la scorta media. La colonna con il bordo scuro è il caso base. Il grafico a destra mostra "
            "come cresce il <b>costo annuo</b> di gestione al variare del parametro.")
    g1, g2 = st.columns([1.5, 1])
    with g1:
        fig = go.Figure()
        for tipo in TIPI_SCORTA:
            fig.add_bar(x=dfs["Scenario"], y=dfs[tipo], name=tipo, marker_color=COLORI_SCORTE[tipo],
                        hovertemplate=f"{tipo}: %{{y:.0f}} {u}<extra></extra>")
        for _, r in dfs.iterrows():
            fig.add_annotation(x=r["Scenario"], y=r["Scorta media totale"], text=f"<b>{fmt(r['Scorta media totale'])}</b>",
                               showarrow=False, yshift=10)
        i_base = int(dfs.index[dfs["valore"] == b[chiave]][0])
        fig.add_shape(type="rect", xref="x", yref="paper", x0=i_base - 0.45, x1=i_base + 0.45, y0=0, y1=1,
                      line=dict(color=BLU_SCURO, width=2.5, dash="dot"), fillcolor="rgba(91,155,213,0.08)", layer="below")
        stile(fig, 420, f"Scorta media ({u})").update_layout(barmode="stack", legend=dict(y=1.02, yanchor="bottom",
                                                                                         traceorder="normal"),
                                                             margin=dict(t=50))
        st.plotly_chart(fig)
    with g2:
        fig = go.Figure()
        fig.add_scatter(x=dfs["Scenario"], y=dfs["Costo annuo (€)"], mode="lines+markers", name="Costo annuo",
                        line=dict(color=ROSSO, width=3), marker=dict(size=9),
                        hovertemplate="€ %{y:,.0f}<extra></extra>")
        stile(fig, 420, "Costo annuo di gestione (€)", legenda=False).update_layout(margin=dict(t=50))
        fig.update_traces(mode="lines+markers")
        fig.update_yaxes(tickprefix="€ ", tickformat="~s")
        fig.update_xaxes(tickangle=0, tickfont=dict(size=11),
                         ticktext=[s.replace(" (base)", "<br>(base)") for s in dfs["Scenario"]], tickvals=dfs["Scenario"])
        st.plotly_chart(fig)

    st.markdown("**Tabella degli scenari**")
    tab_s = dfs.drop(columns=["valore"]).set_index("Scenario")
    tabella(tab_s.style.format(lambda v: fmt(v))
                 .format(lambda v: f"{'+' if v > 0 else ''}{fmt(v, 1)} %", subset=["Variazione costo"])
                 .apply(lambda r: ["font-weight:700;background-color:var(--evidenza)" if "(base)" in r.name else "" for _ in r],
                        axis=1))

    primo, ultimo = dfs.iloc[0], dfs.iloc[-1]
    comp = max(TIPI_SCORTA, key=lambda tp: abs(ultimo[tp] - primo[tp]))
    st.markdown(f'<div class="lettura"><b>In sintesi.</b> Passando da {primo["Scenario"].replace(" (base)", "")} a '
                f'{ultimo["Scenario"].replace(" (base)", "")}, la scorta media passa da {fmt(primo["Scorta media totale"])} a '
                f'{fmt(ultimo["Scorta media totale"])} {u} e il costo annuo da {euro(primo["Costo annuo (€)"])} a '
                f'{euro(ultimo["Costo annuo (€)"])}. La componente che reagisce di più è la '
                f'<b>{comp.lower()}</b>.</div>', unsafe_allow_html=True)
    st.download_button("Scarica la tabella degli scenari (CSV)", tab_s.to_csv(sep=";", decimal=",").encode("utf-8"),
                       f"sensibilita_{codice}_{chiave}.csv", "text/csv")

# ---------------------------------------------------------------------------
# 6. Impresa e dati
# ---------------------------------------------------------------------------
with schede[6]:
    st.subheader(IMPRESA["nome"])
    st.write(f"**Settore:** {IMPRESA['settore']}  \n**Sedi:** {IMPRESA['sede']}")
    st.write("**Articoli analizzati e ipotesi di approvvigionamento** (dati generati, coerenti con il contesto):")
    tabella(pd.DataFrame([{
        "Codice": a["codice"], "Articolo": a["nome"], "Unità": a["unita"], "Andamento": a["andamento"],
        "Descrizione": a["descrizione"], "Costo unitario (€)": a["costo_unitario"],
        "Costo ordine (€)": a["costo_ordine"], "Lead time (mesi)": a["lead_time"],
        "Livello servizio": f"{a['livello_servizio']:.0%}"} for a in ARTICOLI]),
        indice=False)
    dati = pd.concat([RIS[c][0] for c in ART], axis=1)
    dati.index = dati.index.strftime("%Y-%m")
    dati.index.name = "mese"
    st.write("**Serie storiche della domanda (scenari correnti)**")
    tabella(dati, altezza=300)
    st.download_button("Scarica i dati (CSV)", dati.to_csv().encode("utf-8"), "domanda_scenario.csv", "text/csv")
