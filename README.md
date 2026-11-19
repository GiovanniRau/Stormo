# STORMO

*Piattaforma di analisi predittiva per l'ottimizzazione delle scorte nel supporto logistico aeronautico*

Project Work PW 24 – Mini-dashboard Python per la previsione della domanda e la pianificazione delle scorte.

**Versione 2.0** – vedi [CHANGELOG.md](CHANGELOG.md) per lo storico delle modifiche.

Caso di studio: **Leonardo S.p.A. – Divisione Aeronautica** (costituita nel maggio 2025 dall'unione delle divisioni Velivoli e Aerostrutture), magazzino ricambi per il supporto logistico
di velivoli militari (Eurofighter, F-35).

Articoli analizzati: filtro olio motore EJ200 (stazionario), kit di manutenzione F-35 dell'hub di Cameri
(trend crescente), fluido antighiaccio per velivoli (stagionale), modulo avionico rotabile Eurofighter
(intermittente).

## Cosa fa l'applicazione
- si apre con una pagina di benvenuto che presenta il programma e l'impresa;
- genera le serie storiche mensili della domanda (nov 2022 – ott 2026) di **4 articoli** con andamenti diversi:
  stazionario, trend crescente, stagionale, irregolare/intermittente;
- applica e confronta **5 metodi previsionali**: media mobile semplice, media mobile ponderata,
  attenuazione esponenziale, regressione lineare del trend, metodo moltiplicativo stagionale;
- ne misura l'accuratezza sugli ultimi 12 mesi (ME, MAE, RMSE, MAPE, WAPE) e sceglie il metodo migliore per ogni articolo;
- usa la previsione per dimensionare le **scorte cicliche, di sicurezza, pipeline e anticipate**, il lotto economico e il punto di riordino;
- permette di modificare, in unità reali e per ciascun articolo, **variabilità, trend, picco stagionale, lead time
  e livello di servizio** e di confrontare scenario e caso base;
- offre una **panoramica** con semaforo di criticità (basato sull'errore di previsione WAPE);
- include un'**analisi di sensibilità** che confronta più scenari insieme, con tabella esportabile;
- dispone di tema chiaro e notturno.

## Struttura
```
app.py                    dashboard Streamlit
src/config.py             impresa, articoli e parametri (modificabili)
assets/                   sagoma del velivolo, tricolore e carattere IBM Plex Sans (licenza SIL OFL 1.1)
.streamlit/config.toml    tema grafico
src/generatore.py         generatore delle serie storiche
src/previsione.py         metodi previsionali e indicatori di errore
src/scorte.py             calcolo delle quattro tipologie di scorte
data/domanda_storica.csv  serie storiche del caso base
screenshot/               immagini della dashboard
```

## Esecuzione
Su Windows: doppio clic su `AVVIA_DASHBOARD.bat` (installa le librerie e apre la dashboard nel browser).

Da riga di comando:
```bash
pip install -r requirements.txt
streamlit run app.py
```
Per rigenerare il file CSV del caso base: `python src/generatore.py`.

## Nota sui dati
I dati di domanda sono **generati** con un modello parametrico (livello, trend, stagionalità, rumore, ordini a lotti)
coerente con il contesto dell'impresa, come consentito dalla traccia: i dati reali sui ricambi militari non sono pubblici.
