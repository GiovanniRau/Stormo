"""
Configurazione del caso aziendale e dei parametri di base.

Per cambiare impresa o articoli basta modificare questo file:
il resto del programma legge tutto da qui.
"""

NOME_APP = "STORMO"
VERSIONE = "2.0"
DATA_VERSIONE = "19/11/2026"

# --------------------------------------------------------------------------
# Impresa analizzata
# --------------------------------------------------------------------------
IMPRESA = {
    "nome": "Leonardo S.p.A. - Divisione Aeronautica",
    "settore": "Aerospazio e difesa: velivoli militari da combattimento, addestramento e trasporto, supporto logistico e manutenzione",
    "sede": "Leonardo S.p.A., Roma; Divisione Aeronautica: Torino-Caselle, Cameri (NO), Venegono Superiore (VA) e altri siti",
}

# --------------------------------------------------------------------------
# Orizzonte temporale
# --------------------------------------------------------------------------
DATA_INIZIO = "2022-11-01"   # primo mese della serie storica
N_MESI = 48                  # 4 anni di storico mensile (nov 2022 - ott 2026)
MESI_TEST = 12               # ultimi 12 mesi usati per misurare l'accuratezza
ORIZZONTE = 12               # mesi di previsione futura (nov 2026 - ott 2027)

# --------------------------------------------------------------------------
# Profilo stagionale (indici mensili, gen-dic) dell'articolo stagionale.
# Il fluido antighiaccio si usa per sbrinare i velivoli prima del decollo:
# consumo concentrato tra novembre e marzo, quasi nullo d'estate.
# --------------------------------------------------------------------------
PROFILO_INVERNALE = [1.20, 1.00, 0.40, -0.60, -0.90, -0.95,
                     -0.95, -0.95, -0.80, -0.30, 0.60, 1.25]

# --------------------------------------------------------------------------
# Articoli.  Ogni articolo ha:
#  - parametri del generatore di domanda (livello, trend, stagionalita', rumore, lotti)
#  - parametri di approvvigionamento (lead time, costi, livello di servizio)
# Unita': pezzi/mese, euro, mesi.  Costi e quantita' sono ipotesi plausibili
# (i dati reali della Difesa non sono pubblici).
# --------------------------------------------------------------------------
ARTICOLI = [
    {
        "codice": "EJ200-FLT",
        "nome": "Filtro olio motore EJ200 (Eurofighter)",
        "andamento": "Stazionario",
        "descrizione": "Sostituito a intervalli programmati di ore di funzionamento: consumo regolare legato a una flotta stabile.",
        "unita": "pezzi",
        "livello": 140, "trend": 0.0, "stagionalita": 0.0, "profilo": None,
        "cv_rumore": 0.08, "prob_lotto": 0.0, "lotto_medio": 0,
        "costo_unitario": 850.0, "costo_ordine": 600.0, "tasso_mantenimento": 0.20,
        "lead_time": 1.5, "dev_lead_time": 0.0, "livello_servizio": 0.95,
        "fattore_capacita": 1.20, "seed": 11,
    },
    {
        "codice": "F35-KIT",
        "unita": "kit",
        "nome": "Kit componenti manutenzione F-35 (hub di Cameri)",
        "andamento": "Trend crescente",
        "descrizione": "Ricambi per l'attivita' di manutenzione F-35, in crescita con l'aumento delle flotte europee.",
        "livello": 30, "trend": 2.2, "stagionalita": 0.0, "profilo": None,
        "cv_rumore": 0.06, "prob_lotto": 0.0, "lotto_medio": 0,
        "costo_unitario": 18000.0, "costo_ordine": 1500.0, "tasso_mantenimento": 0.20,
        "lead_time": 4.0, "dev_lead_time": 0.0, "livello_servizio": 0.95,
        "fattore_capacita": 1.20, "seed": 22,
    },
    {
        "codice": "DEICE",
        "nome": "Fluido antighiaccio per velivoli (fusto 200 L)",
        "andamento": "Stagionale",
        "descrizione": "Usato per sbrinare i velivoli prima del decollo: consumo concentrato nei mesi invernali.",
        "unita": "fusti",
        "livello": 80, "trend": 0.2, "stagionalita": 1.0, "profilo": PROFILO_INVERNALE,
        "cv_rumore": 0.08, "prob_lotto": 0.0, "lotto_medio": 0,
        "costo_unitario": 1100.0, "costo_ordine": 400.0, "tasso_mantenimento": 0.20,
        "lead_time": 1.0, "dev_lead_time": 0.0, "livello_servizio": 0.95,
        "fattore_capacita": 1.30, "seed": 33,
    },
    {
        "codice": "EF-AVI",
        "unita": "moduli",
        "nome": "Modulo avionico rotabile Eurofighter",
        "andamento": "Irregolare",
        "descrizione": "Componente sostituito solo in caso di guasto: richieste rare, a gruppi e difficili da prevedere.",
        "livello": 0, "trend": 0.0, "stagionalita": 0.0, "profilo": None,
        "cv_rumore": 0.0, "prob_lotto": 0.35, "lotto_medio": 5,
        "costo_unitario": 45000.0, "costo_ordine": 2000.0, "tasso_mantenimento": 0.20,
        "lead_time": 6.0, "dev_lead_time": 0.0, "livello_servizio": 0.95,
        "fattore_capacita": 1.20, "seed": 44,
    },
]
