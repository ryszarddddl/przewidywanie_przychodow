Przewidywanie przychodów: FastAPI + Streamlit + ML (SHAP)

Aplikacja oparta na modelu uczenia maszynowego (zestaw danych z Kaggle), która przewiduje wynagrodzenie na podstawie cech wejściowych. Projekt wykorzystuje FastAPI do serwowania prognoz oraz SHAP do wyjaśnialności modelu.


🚀 Technologie

    FastAPI: Wysokowydajny framework webowy.
    Slowapi: Mechanizm rate-limitingu, chroniący API przed nadmierną liczbą zapytań.
    SHAP: Interpretacja wyników modelu (wyjaśnienie, które cechy wpłynęły na wysokość płacy).
    Python Logging: Zarządzanie poziomami logowania (DEBUG, INFO, ERROR).


🛠️ Instalacja i Uruchomienie
1. Pobranie projektu (Clone)
Najpierw sklonuj repozytorium na swój komputer:
```
git clone https://github.com
cd przewidywanie_przychodow
```
Używaj kodu z rozwagą.
1. Budowanie obrazu Docker
Zainstaluj Docker Desktop: https://docs.docker.com/desktop/
Następnie zbuduj obraz, który zainstaluje wszystkie zależności (Python, PyCaret, SHAP, FastAPI):
bash
```
docker build -t przewidywanie_plac .
```

3. Uruchomienie (Złota zasada portów)
Uruchomienie: Otwórz Docker Desktop, wejdź w zakładkę Images i kliknij Run przy estymator_maratonu. W ustawieniach (Optional settings) wpisz port (np. 8501). Adres do aplikacji znajdziesz w zakładce Containers. W razie problemów zapytaj Gordona (AI wbudowane w Docker Desktop).
Aby aplikacja była dostępna w sieci lokalnej (np. na tablecie), musimy wystawić porty kontenera na zewnątrz:
```
docker run -d -p 8000:8000 -p 8501:8501 --name salary_app przewidywanie_plac
```
Używaj kodu z rozwagą.

    Ważne:

        Lokalnie: Otwórz http://localhost:8501
        Z tabletu/innego PC: Otwórz http://<IP_TWOJEGO_KOMPUTERA>:8501

4. Instalacja manualna.
   Pobierz Pythona (zalecana wersja 3.11): https://www.python.org/downloads/ W konsoli zainstaluj wymagane biblioteki:
```
pip install --upgrade pip
pip install -r requirements.txt
```

6. Uruchamianie manualne:
   Można użyć pliku start.bat lub
   ```
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
🔍 Architektura i Konfiguracja
Dlaczego localhost nie działał?
Wewnątrz kontenera aplikacja widzi tylko siebie. Aby Streamlit mógł pogadać z FastAPI, musi znać Twój adres IP w sieci domowej.

    Nie używaj adresu IP Dockera (np. 172.17.0.2).
    Użyj adresu IP swojego hosta (np. 192.168.1.15) lub nazwy serwisu w docker-compose.

Monitorowanie i Logi
Folder logs znajdziesz w głównym katalogu projektu:

przewidywanie_przychodow/ ├── logs/ │ ├── api/ │ │ └── api_debug_YYYY-MM-DD_HH-MM.log │ └── frontend/ │ └── ui_debug_YYYY-MM-DD.log ├── api/ ├── ui/ └── ...

Aplikacja loguje zdarzenia (FastAPI & Slowapi) na różnych poziomach. Możesz je śledzić na żywo:
bash

docker logs -f przewidywanie_plac

# Logi FastAPI (port 8000)
docker logs <CONTAINER_ID> | Select-String "Predykcja:"

# Lub obejrzyj plik logu bezpośrednio z kontenera
docker exec <CONTAINER_ID> cat /app/logs/api/api_debug_*.log

# Logi Streamlit (port 8501)
docker exec <CONTAINER_ID> cat /app/logs/frontend/ui_debug_*.log
# Logi FastAPI (port 8000)
docker logs <CONTAINER_ID> | Select-String "Predykcja:"

# Lub obejrzyj plik logu bezpośrednio z kontenera
docker exec <CONTAINER_ID> cat /app/logs/api/api_debug_*.log

# Logi Streamlit (port 8501)
docker exec <CONTAINER_ID> cat /app/logs/frontend/ui_debug_*.log





Używaj kodu z rozwagą.
Domyślny poziom logowania to INFO. Jeśli chcesz debugować połączenia, zmień poziom w zmiennych środowiskowych przy starcie (-e LOG_LEVEL=DEBUG).
Poziom logów aplikacji można ustawić w pliku env za pomocą parametru LOG_LEVEL. Wyrózniamy 3 poziomy logowania (INFO, WARNING, ERROR)
Można też ustawić url api serwera w parametrze API_URL
