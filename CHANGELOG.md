# Registro delle versioni

## 2.0 – 19/11/2026
- Metodi previsionali ridotti a cinque, gli stessi indicati dalla traccia: media mobile semplice, media mobile
  ponderata, attenuazione esponenziale, regressione lineare del trend, metodo moltiplicativo stagionale
  (rimosso il metodo di Croston).
- Corretto l'allineamento a sinistra delle colonne di testo nelle tabelle.

## 1.9 – 19/11/2026
- Pulsante **Torna alla home** nella barra laterale: riporta alla pagina di benvenuto mantenendo le impostazioni.
- Il pulsante per riaprire la barra laterale è stato spostato sotto il tricolore, dove resta sempre visibile.

## 1.8 – 19/11/2026
- Selettore degli articoli ridisegnato: schede sempre visibili con nome completo, codice e andamento della
  domanda, al posto del menu a tendina.
- Nuovo carattere tipografico della barra laterale: IBM Plex Sans, incorporato nel programma.

## 1.7 – 19/11/2026
- Nuova scheda **Analisi di sensibilità**: confronto simultaneo di più scenari variando un parametro alla volta
  (lead time, livello di servizio, variabilità della domanda, picco stagionale), con grafico della composizione
  delle scorte, andamento del costo annuo, tabella degli scenari, sintesi automatica ed esportazione CSV.
- **Tema notturno** selezionabile con l'interruttore sole/luna in basso a destra.
- Tabelle ridisegnate per seguire il tema chiaro e notturno.

## 1.6 – 19/11/2026
- Il programma prende il nome **STORMO**.
- Nuova pagina di benvenuto: presentazione del programma in quattro punti, dati generali dell'impresa e
  pulsante di accesso alla dashboard.
- Animazione di transizione: il velivolo attraversa lo schermo e scopre la dashboard.
- Aggiornato il riferimento organizzativo: Divisione Aeronautica di Leonardo (costituita a maggio 2025
  dall'unione di Velivoli e Aerostrutture).

## 1.5 – 19/11/2026
- Nuova sagoma in filigrana: caccia ad ala a delta con alette anteriori, sfumatura blu e linee di dettaglio,
  più stilizzata e coerente con la veste grafica.

## 1.4 – 19/11/2026
- Nuova scheda **Panoramica** con i quattro ricambi a colpo d'occhio e semaforo di criticità (basato sul WAPE).
- Grafici riprogettati per la leggibilità: riquadro "Come leggere il grafico", linea "Oggi", fascia di
  incertezza sulla previsione, barre dell'accuratezza ordinate, scorte con percentuali, confronto scenari
  con un riquadro per articolo.
- Scorta anticipata calcolata sul ciclo annuale (l'accumulo prima dei picchi stagionali è ora visibile).
- Numeri e mesi in formato italiano.

## 1.3 – 19/11/2026
- Articoli aggiornati: filtro olio motore EJ200 (stazionario) e fluido antighiaccio (stagionale invernale)
  al posto del pneumatico M-346 e del kit ispezione M-346.
- Cursori di scenario in unità reali (%, unità al mese, mesi) e scenario indipendente per ciascun articolo.
- Pulsante "Ripristina caso base".

## 1.2 – 19/11/2026
- Nuova veste grafica: tema blu, tricolore d'angolo, sagoma del velivolo in filigrana.
- Rimosse le emoji dall'interfaccia.

## 1.1 – 19/11/2026
- Aggiunto il file di avvio `AVVIA_DASHBOARD.bat` per Windows.

## 1.0 – 19/11/2026
- Prima versione: generatore delle serie storiche, sei metodi previsionali con valutazione dell'errore,
  calcolo delle scorte cicliche, di sicurezza, pipeline e anticipate, dashboard Streamlit con scenari.
