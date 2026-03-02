import os
import json
import logging
import zipfile
import pandas as pd
import shap
from pathlib import Path
from datetime import datetime
from typing import Any

# Uciszanie bibliotek przed ich głównym importem
logging.getLogger('pycaret').setLevel(logging.CRITICAL)
logging.getLogger('matplotlib').setLevel(logging.ERROR)
os.environ['PYCARET_CUSTOM_LOGGING'] = 'True'

from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from pycaret.regression import load_model, predict_model
from logging.handlers import TimedRotatingFileHandler

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import konfiguracji
from api.config import settings

# --- 1. KONFIGURACJA LOGOWANIA ---
LOG_DIR = settings.LOG_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)

def namer(name): return name + ".zip"
def rotator(source, dest):
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as f:
        f.write(source, os.path.basename(source))
    os.remove(source)

current_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_filepath = LOG_DIR / f"api_debug_{current_time_str}.log"

handler = TimedRotatingFileHandler(
    filename=str(log_filepath), when="midnight", interval=1, backupCount=7, encoding='utf-8'
)
handler.rotator = rotator
handler.namer = namer

logger = logging.getLogger("api_logger")
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

# --- 2. INICJALIZACJA I ZASOBY ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title=settings.API_TITLE)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

model = None
explainer = None
DEFAULTS = {}

def load_resources():
    global model, DEFAULTS, explainer
    
    # A. JSON Defaults
    if settings.DEFAULTS_JSON_PATH.exists():
        with open(settings.DEFAULTS_JSON_PATH, 'r', encoding='utf-8') as f:
            DEFAULTS = json.load(f)

    # B. Model & SHAP Explainer
    model_path = Path(settings.MODEL_NAME).with_suffix('.pkl')
    if model_path.exists():
        try:
            model = load_model(settings.MODEL_NAME, verbose=False)
            # Inicjalizacja SHAP (wyciągamy sam model z Pipeline PyCareta)
            # steps[-1][1] to ostatni element potoku (algorytm)
            explainer = shap.Explainer(model.steps[-1][1])
            logger.info(f"Model i SHAP załadowane pomyślnie.")
        except Exception as e:
            logger.error(f"Błąd ładowania modelu: {e}")

load_resources()

# --- 3. POMOCNICZE PRZETWARZANIE ---
def preprocess_data(df: pd.DataFrame):
    df_copy = df.copy() # Pracujemy na kopii, aby nie mutować oryginału
    if 'OverTime' in df_copy.columns:
        ot_map = {'Yes': 1, 'No': 0, True: 1, False: 0, '1': 1, '0': 0}
        df_copy['OverTime'] = df_copy['OverTime'].map(ot_map).fillna(0)
    
    travel_map = {'Non-Travel': 0, 'Travel_Rarely': 1, 'Travel_Frequently': 2}
    if 'BusinessTravel' in df_copy.columns:
        df_copy['BusinessTravel'] = df_copy['BusinessTravel'].apply(
            lambda x: travel_map.get(x, x) if isinstance(x, str) else x
        )
    return df_copy

# --- 4. ENDPOINTY ---

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(request: Request, data: dict):
    if model is None:
        raise HTTPException(status_code=503, detail="Model ML nie jest dostępny.")

    try:
        # Budowa payloadu z domyślnymi wartościami
        input_data = DEFAULTS.copy()
        for key, value in data.items():
            # Dopasowanie kluczy bez względu na wielkość liter
            matched_key = next((k for k in input_data if k.lower() == key.lower()), key)
            input_data[matched_key] = value

        # Przygotowanie DataFrame (NAPRAWA BŁĘDU UnboundLocalError)
        raw_df = pd.DataFrame([input_data])
        processed_df = preprocess_data(raw_df)

        # Dopasowanie kolumn do modelu
        expected_cols = model.feature_names_in_
        final_df = processed_df.reindex(columns=expected_cols, fill_value=0)

        # 1. Predykcja
        predictions = predict_model(model, data=final_df, verbose=False)
        salary = float(predictions.iloc[0, -1])

        # 2. Wyjaśnienie SHAP
        explanation = []
        if explainer:
            # Transformacja danych przed SHAP (pomiń ostatni krok - sam model)
            transformed_data = model[:-1].transform(final_df)
            shap_values = explainer(transformed_data)
            
            # Tworzymy listę wpływów
            feat_impacts = dict(zip(expected_cols, shap_values.values[0])) # [0] dla pierwszego wiersza
            
            # Sortowanie po sile wpływu (top 3)
            top_features = sorted(feat_impacts.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
            
            explanation = [
                {"feature": str(f), "impact": round(float(v), 2), "direction": "up" if v > 0 else "down"}
                for f, v in top_features
            ]

        # --- DODANE LOGOWANIE WYJAŚNIEŃ ---
        logger.info(f"Predykcja: {salary:.2f} USD | Top factors: {explanation}")
        
        return {
            "salary_prediction": round(salary, 2),
            "explanation": explanation
        }

    except Exception as e:
        logger.error(f"Błąd predykcji: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Błąd serwera.")

@app.get("/")
async def root():
    return {"status": "Online", "model_loaded": model is not None}