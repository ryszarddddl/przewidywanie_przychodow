import streamlit as st
import requests
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from logging.handlers import RotatingFileHandler

# 1. Dynamiczne dodanie root projektu, aby import z api.config zadziałał
# Wyjście z folderu 'frontend' do głównego katalogu projektu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from api.config import settings

# --- 2. KONFIGURACJA LOGOWANIA UI ---
# Korzystamy z nowej struktury: logs/frontend/
UI_LOG_DIR = PROJECT_ROOT / "logs" / "frontend"
UI_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Nazwa pliku logu
ui_log_file = UI_LOG_DIR / f"ui_debug_{datetime.now().strftime('%Y-%m-%d')}.log"

# Konfiguracja loggera
ui_logger = logging.getLogger("streamlit_app")
ui_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


if not ui_logger.handlers:
    # RotatingFileHandler zapobiegnie "napuchnięciu" pliku logu do gigantycznych rozmiarów
    handler = RotatingFileHandler(
        str(ui_log_file), 
        maxBytes=5*1024*1024, # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    formatter = logging.Formatter('%(asctime)s - UI - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    ui_logger.addHandler(handler)
    # Opcjonalnie: logi na konsolę terminala
    ui_logger.addHandler(logging.StreamHandler())

# Zapobiegamy dublowaniu handlerów przy odświeżaniu strony Streamlit
if not ui_logger.handlers:
    file_handler = logging.FileHandler(ui_log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - UI_LOG - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    ui_logger.addHandler(file_handler)

import requests
import streamlit as st

# Zmieniamy nazwę na v3, aby całkowicie odciąć się od starego cache'u
@st.cache_data(ttl=3600)
def get_usd_course_v5():
    # 1. NBP (z Twoją celową literówką do testów)
    try:
        url = "https://aapi.nbp.pl/api/exchangerates/rates/a/usd/"
        res = requests.get(url, params={'format': 'json'}, timeout=5)
        ui_logger.info(f"NBP zwrócił kurs: {res.json()['rates'][0]['mid']} PLN/USD")
        return float(res.json()['rates'][0]['mid'])
    except Exception as e:
        ui_logger.warning(f"NBP zawiódł: {str(e)}")

    # 2. FRANKFURTER (Zapasowy 1)
    try:
        url = "https://api.frankfurter.app/latest" # KLUCZOWE: /latest
        res = requests.get(url, params={"from": "USD", "to": "PLN"}, timeout=5)
        # Struktura: {"rates": {"PLN": 3.58}}
        ui_logger.info(f"Frankfurter zwrócił kurs {res.json()['rates']['PLN']} PLN/USD")
        return float(res.json()['rates']['PLN'])
    except Exception as e:
        ui_logger.warning(f"Frankfurter zawiódł: {str(e)}")

    # 3. OPEN ER (Zapasowy 2)
    try:
        url = "https://open.er-api.com/v6/latest/USD" # KLUCZOWE: /v6/latest/USD
        res = requests.get(url, timeout=5)
        # Struktura: {"rates": {"PLN": 3.5792}}
        ui_logger.info(f"Open ER zwrócił kurs: {res.json()['rates']['PLN']} PLN/USD")
        return float(res.json()['rates']['PLN'])
    except Exception as e:
        ui_logger.warning(f"Open ER zawiódł: {str(e)}")

    return 4.05 # Ostateczny fallback

st.set_page_config(layout="wide", page_title="Salary Predictor Pro")

# --- LEWA STRONA (MENU) ---
with st.sidebar:
    st.header("⚙️ Parametry wejściowe")
    with st.form("salary_form"):
        # --- PODSTAWOWE (Widoczne od razu) ---
        age = st.slider("Wiek", 18, 65, 30)
        gender = st.radio("Płeć", ["Male", "Female"], horizontal=True, index=0)
        levels_map = {
            "Junior / Entry Level": 1,
            "Specialist / Associate": 2,
            "Senior / Team Lead": 3,
            "Manager / Director": 4,
            "Executive / Vice President": 5
        } 
        
        edu_map = {
            "Podstawowe / Średnie": 1,
            "Studium / Policealne": 2,
            "Licencjat / Inżynier": 3,
            "Magister": 4,
            "Doktorat": 5
        }

        travel_map = {
            'Non-Travel': 0,
            'Travel_Rarely': 1,       
            'Travel_Frequently': 2    
        }
        selected_edu = st.selectbox("Wykształcenie", list(edu_map.keys()), index=2) # domyślnie Licencjat
        education = edu_map[selected_edu]

        # --- ZAAWANSOWANE (Ukryte w rozwijanej sekcji) ---
        with st.expander("➕ Opcje dodatkowe"):
            department = st.selectbox("Dział", ["Sales", "Research & Development", "Human Resources"])
            job_role = st.selectbox("Rola", ["Manager", "Sales Executive", "Developer", "Researcher"])
            overtime = st.radio("Nadgodziny", ["Yes", "No"], horizontal=True, index=1)
            selected_label = st.selectbox("Poziom stanowiska", list(levels_map.keys()))
            job_level = levels_map[selected_label]
            selected_ltravel = st.selectbox("Częstość wyjazdów służbowych", list(travel_map.keys()))
            BusinessTravel = levels_map[selected_label]
            edu_field = st.selectbox(
                "Kierunek studiów", 
                ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"],
                index=0 # Domyślnie Life Sciences
            )
                
            # Stan cywilny
            marital_status = st.radio(
                "Stan cywilny", 
                ["Single", "Married", "Divorced"], 
                index=0, # Domyślnie Married
                horizontal=True
            )
            total_years = st.selectbox("Ilość lat pracy", [1, 2, 3, 4, 5, 10, 15, 20, 30])
            

        st.divider()
        submit_button = st.form_submit_button("🚀 Oblicz sugerowaną pensję", use_container_width=True)

# --- PRAWA STRONA ---
st.title("💰 System Przewidywania Wynagrodzeń")
st.markdown("---")

if submit_button:
    with st.spinner('Trwa obliczanie...'):
        try:
            # PRZYGOTOWANIE DANYCH
            payload = {
                "Age": age,
                'Gender': gender,
                "Department": department,
                "JobRole": job_role,
                "BusinessTravel": BusinessTravel, 
                "EducationField": edu_field,
                "Education": education,
                "MaritalStatus": marital_status,
                "JobLevel": job_level,
                "OverTime": overtime,
                "TotalWorkingYears": total_years
            }
            
            # LOGOWANIE WYSYŁKI
            ui_logger.info(f"WYSYŁKA DO API: {payload}")
            response = requests.post(f"{settings.API_URL}/predict", json=payload)
            
            # LOGOWANIE ODPOWIEDZI
            ui_logger.info(f"STATUS API: {response.status_code}")
            ui_logger.info(f"ODPOWIEDŹ API: {response.text}")

            if response.status_code == 429:
                st.error("⚠️ Zwolnij! Przekroczono limit zapytań. Odczekaj minutę.")
                ui_logger.warning("Użytkownik uderzył w Rate Limit API.")
            elif response.status_code == 200:
                result = response.json()
                salary_usd = result['salary_prediction']
                explanations = result["explanation"]
                salary_usd_annual = salary_usd * 12
                
                usd_rate = get_usd_course_v5()
                salary_pln = salary_usd * usd_rate
                salary_pln_annual = salary_pln * 12
                
                # --- POPRAWIONA SEKCJA WYNIKÓW W STREAMLIT ---

                st.balloons()
                st.subheader("📊 Wynik analizy płacowej")

                # Tworzymy ładne sformatowane ciągi znaków (separator tysięcy to spacja)
                formatted_usd = f"{salary_usd:,.2f}".replace(",", " ").replace(".", ",")
                formatted_pln = f"{salary_pln:,.2f}".replace(",", " ").replace(".", ",")
                formatted_usd_annual = f"{salary_usd_annual:,.2f}".replace(",", " ").replace(".", ",")
                formatted_pln_annual = f"{salary_pln_annual:,.2f}".replace(",", " ").replace(".", ",")

                # Stylizacja za pomocą kolumn i kontenerów
                res_col1, res_col2 = st.columns(2)

                with res_col1:
                    st.markdown(
                        f"""
                        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid #2e7d32;">
                            <p style="margin:0; color:#555; font-size:14px; font-weight:bold;">ESTYMACJA MIESIĘCZNA (USD)</p>
                            <h2 style="margin:0; color:#1a1a1a;">$ {formatted_usd} </h2>
                        </div>
                        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid #2e7d32;">
                            <p style="margin:0; color:#555; font-size:14px; font-weight:bold;">ESTYMACJA ROCZNA (USD)</p>
                            <h2 style="margin:0; color:#1a1a1a;">$ {formatted_usd_annual}</h2>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                with res_col2:
                    # Używamy standardowego metric, ale z ładniejszym formatowaniem PLN
                    st.metric(
                        label="PRZELICZENIE MIESIĘCZNE (PLN)", 
                        value=f"{formatted_pln} zł", 
                        #delta=f"Kurs: {usd_rate:.4f} PLN/USD",
                        #delta_color="off" # Wyłącza kolorowanie strzałki przy kursie
                    )
                    
                    st.metric(
                        label="PRZELICZENIE ROCZNE (PLN)", 
                        value=f"{formatted_pln_annual} zł ", 
                        delta=f"Kurs: {usd_rate:.4f} PLN/USD",
                        delta_color="off" # Wyłącza kolorowanie strzałki przy kursie
                    )

              
                st.divider()

                # Dodatkowa sekcja czytelności dla bardzo wysokich kwot
                if salary_pln > 50000:
                    st.warning("⚠️ Uwaga: Wygenerowana kwota jest powyżej średniej rynkowej dla standardowych ról. Sprawdź parametry JobLevel.")

                if salary_usd_annual > 50000:
                    st.success('Twoje wynagrodzenie jest powyżej 50 000 USD rocznie!', icon="🥳")
                else:
                    st.warning('Twoje wynagrodzenie jest poniżej 50 000 USD rocznie', icon="😔")

                st.success("Analiza zakończona pomyślnie.")
                # Tutaj możesz dodać wykresy lub dodatkowe info (np. z Notebooka)
                st.subheader("💡 Interpretacja wyniku")
                st.write(f"Dla pracownika w wieku {age} lat na poziomie {job_level}, model przewiduje stabilne dopasowanie do siatki płac.")
                st.write("### 🧠 Analiza Twojej wyceny")

                # Sekcja 1: Stałe trendy (stare wyjaśnienie)
                with st.expander("ℹ️ Jak model ogólnie ocenia płace?"):
                    st.info("""
                    Model opiera swoje decyzje głównie na trzech kluczowych filarach:
                    1. **Poziom stanowiska** – stanowi fundament bazy płacowej.
                    2. **Staż pracy** – uwzględnia premię za Twoje doświadczenie.
                    3. **Nadgodziny** – odzwierciedla dodatek za dyspozycyjność.
                    """)

                # Sekcja 2: Dynamiczne wyniki z SHAP (nowa funkcjonalność)
                st.write("#### 🎯 Co najbardziej wpłynęło na **Twój** wynik?")

                TRANSLATIONS = {
                    "OverTime": "Nadgodziny",
                    "PerformanceRating": "Ocena wydajności",
                    "JobSatisfaction": "Satysfakcja z pracy",
                    "JobLevel": "Poziom stanowiska",
                    "TotalWorkingYears": "Staż pracy (lata)",
                    "Age": "Wiek",
                    "BusinessTravel": "Podróże służbowe",
                    "DailyRate": "Stawka dzienna",
                    "MonthlyIncome": "Miesięczny dochód",
                    "YearsAtCompany": "Lata w obecnej firmie"
                }

                SUGGESTIONS = {
                    "OverTime": "Ogranicz nadgodziny na rzecz podnoszenia kwalifikacji – w Twoim profilu korelują one z niższymi szczeblami płac.",
                    "PerformanceRating": "Porozmawiaj z przełożonym o konkretnych celach, które pozwolą Ci podnieść roczną ocenę wydajności.",
                    "JobSatisfaction": "Zadbaj o work-life balance lub zmień projekt – wyższa satysfakcja statystycznie sprzyja awansom.",
                    "JobLevel": "Przygotuj się do rekrutacji wewnętrznej na wyższy szczebel (Level Up).",
                    "Education": "Rozważ zdobycie dodatkowych certyfikatów lub ukończenie studiów kierunkowych w Twojej branży.",
                    "TotalWorkingYears": "Buduj cierpliwie staż pracy – Twój profil zyskuje na wartości wraz z każdym rokiem doświadczenia."
                }

                for item in explanations:
                    raw_feature = item["feature"]
                    # Tłumaczenie nazwy (jeśli nie ma w słowniku, zostaje oryginał)
                    display_name = TRANSLATIONS.get(raw_feature, raw_feature)
                    
                    # Przeliczenie wpływu na PLN
                    impact = item["impact"] 
                    impact_pln = impact * usd_rate
                    
                    icon = "⬆️" if item["direction"] == "up" else "⬇️"
                    color = "green" if item["direction"] == "up" else "red"
                    
                    # Wyświetlenie sformatowanej linii
                    st.markdown(
                        f"{icon} **{display_name}**: "
                        f":{color}[{impact:+,.2f} USD]"
                        f" w przeliczeniu na PLN  "
                        f":{color}[{impact_pln:+,.2f} zł]"
                    )
                # --- Sekcja Sugestii ---
                st.write("---")
                st.write("### 🚀 Twoja ścieżka wzrostu")

                for item in explanations:
                    feature_name = item["feature"]
                    direction = item["direction"]
                        
                    # 1. Specyficzna logika dla Nadgodzin
                    if feature_name == "OverTime":
                        # Podpowiadaj ograniczenie TYLKO jeśli użytkownik faktycznie ma nadgodziny
                        # i mają one negatywny wpływ
                        if direction == "down" and payload.get("OverTime") in ["Yes", 1, True]:
                            st.markdown(f"**Nadgodziny**: {SUGGESTIONS['OverTime']}")
                        continue # Przejdź do następnej cechy

                    # 2. Logika dla JobLevel (jeśli jest niski)
                    if feature_name == "JobLevel" and direction == "down":
                        st.markdown(f"**Poziom stanowiska**: Twój obecny poziom mocno ogranicza widełki. Celuj w awans na Level 2+, aby odblokować wyższe mnożniki.")
                        continue

                    # 3. Standardowa logika dla reszty cech ujemnych
                    if direction == "down":
                        display_name = TRANSLATIONS.get(feature_name, feature_name)
                        advice = SUGGESTIONS.get(feature_name, "Dalszy rozwój w tym obszarze podniesie Twoją wycenę.")
                        st.markdown(f"**{display_name}**: {advice}")                    
            else:
                st.error(f"Błąd API ({response.status_code})")
                st.warning(response.text)

        except Exception as e:
            ui_logger.error(f"BŁĄD KRYTYCZNY UI: {str(e)}", exc_info=True)
            st.error(f"Błąd: {str(e)}")
else:
    st.info("👈 Użyj panelu po lewej stronie.")
