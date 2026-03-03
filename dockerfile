# Wybieramy stabilną bazę Pythona
FROM python:3.10-slim

# Instalujemy niezbędne biblioteki systemowe (wymagane przez niektóre paczki ML)
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiujemy wymagania i instalujemy (cache'owanie warstw)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy całą resztę kodu
COPY . .

# FastAPI działa na 8000, Streamlit na 8501
EXPOSE 8000
EXPOSE 8501

# Skrypt startowy
RUN echo '#!/bin/bash\nuvicorn api.main:app --host 0.0.0.0 --port 8000 &\nstreamlit run ui/aplikacja.py --server.port 8501 --server.address 0.0.0.0\nwait' > /app/start.sh && chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]
