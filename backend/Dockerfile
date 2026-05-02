# ──────────────────────────────────────────────
#  M-Motors — FastAPI Backend
#  Build : docker build -t mmotors-api .
#  TLS interne : certificat dans /certs (volume partagé avec frontend / nginx).
# ──────────────────────────────────────────────

FROM python:3.12-slim

WORKDIR /app

# System deps (psycopg2 + TLS interne)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc openssl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY . .

RUN adduser --system --uid 1001 fastapi

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import ssl,urllib.request; c=ssl.create_default_context(); c.load_verify_locations('/certs/server.pem'); urllib.request.urlopen('https://127.0.0.1:8000/api/health', context=c)"

ENTRYPOINT ["/docker-entrypoint.sh"]
