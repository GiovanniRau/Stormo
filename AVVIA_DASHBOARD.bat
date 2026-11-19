@echo off
title STORMO - Previsione della domanda e scorte
cd /d "%~dp0"

set PY=
where py >nul 2>nul && set PY=py
if "%PY%"=="" where python >nul 2>nul && set PY=python
if "%PY%"=="" (
    echo.
    echo  ERRORE: Python non risulta installato.
    echo  Scaricalo da https://www.python.org/downloads/
    echo  e durante l'installazione spunta "Add python.exe to PATH".
    echo.
    pause
    exit /b
)

echo.
echo  [1/2] Controllo librerie (la prima volta puo' richiedere 1-2 minuti)...
%PY% -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  ERRORE durante l'installazione delle librerie. Fai uno screenshot di questa finestra.
    pause
    exit /b
)

echo.
echo  [2/2] Avvio della dashboard: si aprira' il browser.
echo  Per chiudere la dashboard chiudi questa finestra.
echo.
%PY% -m streamlit run app.py --server.headless false
pause
