"""
Dimensionamento delle quattro tipologie di scorte a partire dalle previsioni.

1. Scorta ciclica      = Q*/2, con Q* = lotto economico (EOQ, formula di Wilson)
                         Q* = sqrt(2 * D * S / (h * c))
                         D = domanda annua prevista, S = costo di emissione ordine,
                         c = costo unitario, h = tasso annuo di mantenimento.
2. Scorta di sicurezza = z * sqrt(L * sigma_e^2 + d^2 * sigma_L^2)
                         sigma_e = RMSE del metodo previsionale scelto (incertezza
                         della previsione), L = lead time (mesi), d = domanda media
                         mensile prevista, sigma_L = deviazione standard del lead time,
                         z = quantile della normale per il livello di servizio.
                         Previsioni piu' accurate -> RMSE piu' basso -> meno scorta.
3. Scorta pipeline     = d * L  (merce gia' ordinata e in transito durante il lead time).
4. Scorta anticipata   = merce prodotta/acquistata in anticipo perche' la capacita'
                         mensile C non basta a coprire i picchi previsti.
                         Calcolo a ritroso: A_t = max(0, A_{t+1} + F_{t+1} - C),
                         con C = fattore_capacita * domanda media prevista,
                         considerando l'anno di previsione come un ciclo che si ripete.

Punto di riordino: ROP = d * L + scorta di sicurezza.
"""
from statistics import NormalDist

import numpy as np
import pandas as pd


def scorta_anticipata(previsione, capacita):
    """Scorta anticipata a fine mese in regime stazionario.

    I 12 mesi di previsione sono trattati come un ciclo annuale che si ripete:
    la ricorsione a ritroso viene percorsa due volte, cosi' l'accumulo prima dei
    picchi (es. settembre-ottobre per l'inverno) compare correttamente anche
    quando il picco cade all'inizio dell'orizzonte."""
    f = np.asarray(previsione, float)
    n = len(f)
    if f.sum() > capacita * n:          # capacita' insufficiente anche sull'anno: nessuna soluzione stazionaria
        capacita = f.mean()
    a = np.zeros(2 * n)
    ff = np.concatenate([f, f])
    for t in range(2 * n - 2, -1, -1):
        a[t] = max(0.0, a[t + 1] + ff[t + 1] - capacita)
    return a[:n]


def calcola_scorte(previsione, rmse, art, k_lead_time=1.0, livello_servizio=None, lead_time=None):
    """Restituisce un dizionario con scorte medie, EOQ, ROP e costi annui."""
    f = np.asarray(previsione, float)
    D = f.sum() * 12 / len(f)                      # domanda annua prevista
    d = D / 12                                     # domanda media mensile
    L = art["lead_time"] * k_lead_time if lead_time is None else lead_time
    sL = art["dev_lead_time"] * L / art["lead_time"]
    ls = livello_servizio if livello_servizio is not None else art["livello_servizio"]
    z = NormalDist().inv_cdf(ls)
    c, S, h = art["costo_unitario"], art["costo_ordine"], art["tasso_mantenimento"]

    eoq = np.sqrt(2 * D * S / (h * c)) if D > 0 else 0.0
    ciclica = eoq / 2
    sicurezza = z * np.sqrt(L * rmse ** 2 + d ** 2 * sL ** 2)
    pipeline = d * L
    capacita = art["fattore_capacita"] * d
    profilo_ant = scorta_anticipata(f, capacita)
    anticipata = profilo_ant.mean()

    totale = ciclica + sicurezza + pipeline + anticipata
    costo_mant = totale * c * h
    costo_ordini = (D / eoq) * S if eoq > 0 else 0.0
    return {
        "Domanda annua prevista": D,
        "Domanda media mensile": d,
        "Lead time (mesi)": L,
        "Livello di servizio": ls,
        "z": z,
        "EOQ (lotto economico)": eoq,
        "Punto di riordino": d * L + sicurezza,
        "Scorta ciclica": ciclica,
        "Scorta di sicurezza": sicurezza,
        "Scorta pipeline": pipeline,
        "Scorta anticipata": anticipata,
        "Scorta media totale": totale,
        "Valore scorta media (EUR)": totale * c,
        "Costo annuo mantenimento (EUR)": costo_mant,
        "Costo annuo ordini (EUR)": costo_ordini,
        "Costo annuo totale (EUR)": costo_mant + costo_ordini,
        "Copertura (mesi)": totale / d if d > 0 else np.nan,
        "_profilo_anticipata": pd.Series(profilo_ant, index=getattr(previsione, "index", None)),
        "_capacita": capacita,
    }


TIPI_SCORTA = ["Scorta ciclica", "Scorta di sicurezza", "Scorta pipeline", "Scorta anticipata"]
