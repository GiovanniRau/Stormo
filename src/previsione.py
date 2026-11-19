"""
Metodi previsionali e indicatori di errore.

Metodi implementati:
  1. Media mobile semplice (SMA)
  2. Media mobile ponderata (WMA)
  3. Attenuazione (livellamento) esponenziale semplice (SES)
  4. Proiezione del trend con regressione lineare (REG)
  5. Metodo moltiplicativo stagionale (decomposizione classica: trend x indici stagionali)

Valutazione: "rolling origin" a un passo. Per ogni mese del periodo di test
il metodo usa solo i dati disponibili fino al mese precedente (come accadrebbe
nella realta'), si confronta la previsione con la domanda effettiva e si
calcolano gli errori. Tutti i metodi sono quindi valutati nelle stesse condizioni.
"""
import numpy as np
import pandas as pd

NOMI_METODI = {
    "SMA": "Media mobile semplice",
    "WMA": "Media mobile ponderata",
    "SES": "Attenuazione esponenziale",
    "REG": "Regressione lineare (trend)",
    "STAG": "Moltiplicativo stagionale",
}

NOMI_BREVI = {"SMA": "Media mobile", "WMA": "Media ponderata", "SES": "Esponenziale",
              "REG": "Regressione", "STAG": "Stagionale"}


# --------------------------------------------------------------------------
# Previsioni a h passi a partire da uno storico y (array numpy)
# --------------------------------------------------------------------------
def prev_sma(y, h, n=3):
    return np.repeat(np.mean(y[-n:]), h)


def prev_wma(y, h, n=3):
    pesi = np.arange(1, n + 1, dtype=float)          # 1, 2, ..., n (piu' peso ai mesi recenti)
    return np.repeat(np.dot(y[-n:], pesi) / pesi.sum(), h)


def prev_ses(y, h, alpha=0.3):
    livello = y[0]
    for v in y[1:]:
        livello = alpha * v + (1 - alpha) * livello
    return np.repeat(livello, h)


def _retta(y):
    t = np.arange(len(y))
    b, a = np.polyfit(t, y, 1)                       # pendenza, intercetta
    return a, b


def prev_reg(y, h):
    a, b = _retta(y)
    t_fut = np.arange(len(y), len(y) + h)
    return a + b * t_fut


def indici_stagionali(y, mesi, periodo=12):
    """Indici stagionali moltiplicativi con il metodo dei rapporti alla media mobile centrata.
    `mesi` = mese dell'anno (1..12) di ogni osservazione."""
    s = pd.Series(y, dtype=float)
    mm = s.rolling(periodo, center=True).mean().rolling(2).mean().shift(-1)   # MM centrata 2x12
    rapporti = s / mm
    df = pd.DataFrame({"mese": mesi, "r": rapporti}).dropna()
    idx = df.groupby("mese")["r"].mean().reindex(range(1, periodo + 1)).fillna(1.0)
    return idx / idx.mean()                          # normalizzati: media = 1


def prev_stag(y, h, mesi, mesi_fut):
    if len(y) < 24:                                  # servono almeno 2 anni
        return prev_reg(y, h)
    idx = indici_stagionali(y, mesi).clip(lower=0.05)   # evita divisioni per zero
    destag = y / idx.loc[mesi].values
    a, b = _retta(destag)
    t_fut = np.arange(len(y), len(y) + h)
    f = (a + b * t_fut) * idx.loc[mesi_fut].values
    return f if np.all(np.isfinite(f)) else prev_reg(y, h)


def prevedi(metodo, y, h, mesi=None, mesi_fut=None, n=3, alpha=0.3):
    if metodo == "SMA":
        return prev_sma(y, h, n)
    if metodo == "WMA":
        return prev_wma(y, h, n)
    if metodo == "SES":
        return prev_ses(y, h, alpha)
    if metodo == "REG":
        return prev_reg(y, h)
    if metodo == "STAG":
        return prev_stag(y, h, mesi, mesi_fut)
    raise ValueError(metodo)


# --------------------------------------------------------------------------
# Valutazione
# --------------------------------------------------------------------------
def backtest(serie, metodo, mesi_test=12, **par):
    """Previsioni a un passo sugli ultimi `mesi_test` mesi (rolling origin)."""
    y = serie.values.astype(float)
    mesi = serie.index.month.values
    n = len(y)
    prev = []
    for t in range(n - mesi_test, n):
        f = prevedi(metodo, y[:t], 1, mesi[:t], mesi[t:t + 1], **par)
        prev.append(max(f[0], 0.0))
    return pd.Series(prev, index=serie.index[n - mesi_test:], name=metodo)


def indicatori_errore(effettivo, previsto):
    e = np.asarray(effettivo, float) - np.asarray(previsto, float)
    a = np.asarray(effettivo, float)
    nz = a > 0
    return {
        "ME (bias)": e.mean(),
        "MAE": np.abs(e).mean(),
        "RMSE": np.sqrt((e ** 2).mean()),
        "MAPE %": (np.abs(e[nz]) / a[nz]).mean() * 100 if nz.any() else np.nan,
        "WAPE %": np.abs(e).sum() / a.sum() * 100 if a.sum() > 0 else np.nan,
    }


def confronta_metodi(serie, mesi_test=12, criterio="RMSE", n=3, alpha=0.3):
    """Tabella degli errori di tutti i metodi + metodo migliore secondo `criterio`."""
    righe, prev_test = [], {}
    eff = serie.iloc[-mesi_test:]
    for m in NOMI_METODI:
        par = {"n": n} if m in ("SMA", "WMA") else {"alpha": alpha} if m == "SES" else {}
        p = backtest(serie, m, mesi_test, **par)
        prev_test[m] = p
        righe.append({"Metodo": NOMI_METODI[m], "Codice": m, **indicatori_errore(eff, p)})
    tab = pd.DataFrame(righe).set_index("Codice")
    migliore = tab[criterio].abs().idxmin()
    return tab, migliore, pd.DataFrame(prev_test)


def previsione_futura(serie, metodo, orizzonte=12, n=3, alpha=0.3):
    """Previsione dei prossimi `orizzonte` mesi usando tutto lo storico."""
    y = serie.values.astype(float)
    date_fut = pd.date_range(serie.index[-1] + pd.offsets.MonthBegin(1), periods=orizzonte, freq="MS")
    f = prevedi(metodo, y, orizzonte, serie.index.month.values, date_fut.month.values, n=n, alpha=alpha)
    return pd.Series(np.clip(f, 0, None), index=date_fut, name="Previsione")
