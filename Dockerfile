FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# fonts-liberation — czcionki z polskimi znakami dla generowanych PDF (reportlab)
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN mkdir -p data

EXPOSE 8000

# 1 worker + wątki — bezpieczne dla SQLite (brak międzyprocesowych blokad zapisu)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "120", "app:app"]
