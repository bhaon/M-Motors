# ──────────────────────────────────────────────
#  M-Motors — FastAPI Backend
#  Build : docker build -t mmotors-api .
# ──────────────────────────────────────────────

FROM python:3.12-slim

WORKDIR /app

# System deps (psycopg2 needs libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY . .

# Non-root user
RUN adduser --system --uid 1001 fastapi
USER fastapi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
