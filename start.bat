 @echo off
TITLE Projekt Przewidywanie Plac - Start

:: 1. Ustawienie ścieżki do skryptu aktywacji Condy (standardowa lokalizacja)
:: Jeśli Twoja Anaconda jest w innym miejscu, podmień ścieżkę poniżej!
set CONDA_PATH=C:\Users\%USERNAME%\miniconda3\Scripts\activate.bat

:: 2. Uruchomienie FastAPI w nowym oknie (Anaconda Prompt + Środowisko)
echo Uruchamianie FastAPI...
start "FastAPI Server" cmd /k "call %CONDA_PATH% od_zera_do_ai_v2 && uvicorn api.main:app --reload --port 8000 --log-level error"

:: 3. Odczekanie chwili na start API
timeout /t 5

:: 4. Uruchomienie Streamlita w nowym oknie (Anaconda Prompt + Środowisko)
echo Uruchamianie Streamlit...
start "Streamlit Frontend" cmd /k "call %CONDA_PATH% od_zera_do_ai_v2 && streamlit run ui/aplikacja.py"

echo Gotowe! Oba serwery startuja w osobnych oknach.
