"""
Generatore delle serie storiche di domanda.

Modello per ogni mese t (t = 0..N-1, m = mese dell'anno):

    base_t   = livello + trend * t
    stag_t   = 1 + stagionalita * profilo[m]          (modello moltiplicativo)
    domanda  = base_t * stag_t * (1 + cv_rumore * e_t)   con e_t ~ N(0, 1)
             + eventuale lotto B2B (articoli irregolari)

I numeri casuali sono generati con un seme fisso: modificando un solo
parametro (es. la variabilita') cambia solo l'effetto di quel parametro,
mentre la componente casuale resta la stessa. Questo rende i confronti
tra scenari leggibili.
"""
import numpy as np
import pandas as pd

from config import ARTICOLI, DATA_INIZIO, N_MESI


def genera_serie(art, k_variabilita=1.0, k_trend=1.0, k_stagionalita=1.0,
                 n_mesi=N_MESI, data_inizio=DATA_INIZIO, trend=None):
    """Restituisce una pd.Series mensile di domanda per l'articolo `art`.

    I tre moltiplicatori permettono di costruire scenari:
      k_variabilita  scala la componente casuale (rumore e lotti)
      k_trend        scala la pendenza del trend
      k_stagionalita scala l'ampiezza della stagionalita'
    Se `trend` e' indicato, sostituisce la pendenza (pezzi/mese) dell'articolo.
    """
    rng = np.random.default_rng(art["seed"])
    date = pd.date_range(data_inizio, periods=n_mesi, freq="MS")
    t = np.arange(n_mesi)

    # estrazioni casuali fatte sempre nello stesso ordine (stesso seme)
    e = rng.standard_normal(n_mesi)
    u_lotto = rng.random(n_mesi)
    dim_lotto = rng.lognormal(mean=0.0, sigma=0.5, size=n_mesi)

    pendenza = art["trend"] * k_trend if trend is None else trend
    base = np.clip(art["livello"] + pendenza * t, 0, None)
    if art["livello"] == 0 and pendenza > 0:      # articoli intermittenti: il trend fa crescere i lotti
        base = pendenza * t
    if art["profilo"] is not None:
        profilo = np.array(art["profilo"])[date.month - 1]
        stag = np.clip(1 + art["stagionalita"] * k_stagionalita * profilo, 0, None)
    else:
        stag = np.ones(n_mesi)

    domanda = base * stag * (1 + art["cv_rumore"] * k_variabilita * e)

    if art["prob_lotto"] > 0:
        # ordini B2B: in alcuni mesi arriva un lotto di dimensione variabile.
        # La variabilita' agisce sulla dispersione della dimensione del lotto.
        lotti = np.where(u_lotto < art["prob_lotto"],
                         art["lotto_medio"] * dim_lotto ** k_variabilita, 0.0)
        domanda = domanda + lotti

    domanda = np.clip(np.round(domanda), 0, None)
    return pd.Series(domanda, index=date, name=art["codice"])


def genera_tutte(**kwargs):
    """DataFrame con una colonna per articolo."""
    return pd.concat([genera_serie(a, **kwargs) for a in ARTICOLI], axis=1)


if __name__ == "__main__":
    import os
    df = genera_tutte()
    out = os.path.join(os.path.dirname(__file__), "..", "data", "domanda_storica.csv")
    df.index.name = "mese"
    df.to_csv(out)
    print(f"Salvato {out}")
    print(df.describe().round(1))
