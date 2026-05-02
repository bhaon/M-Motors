#!/bin/sh
# Démarre uvicorn en TLS sur :8000 ; génère un certificat auto-signé partagé (volume /certs) pour nginx et Node.
set -e
CERT_DIR=/certs
mkdir -p "$CERT_DIR"
if [ ! -s "$CERT_DIR/server.pem" ] || [ ! -s "$CERT_DIR/server-key.pem" ]; then
  echo "backend: génération du certificat TLS interne (SAN backend)…"
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$CERT_DIR/server-key.pem" -out "$CERT_DIR/server.pem" \
    -subj "/CN=backend/O=M-Motors" \
    -addext "subjectAltName=DNS:backend,DNS:mmotors-backend,DNS:localhost,IP:127.0.0.1"
  chmod 644 "$CERT_DIR/server.pem"
  chmod 640 "$CERT_DIR/server-key.pem"
  chown fastapi:fastapi "$CERT_DIR/server.pem" "$CERT_DIR/server-key.pem" 2>/dev/null || true
fi
exec runuser -u fastapi -- /usr/local/bin/uvicorn app.main:application \
  --host 0.0.0.0 --port 8000 \
  --ssl-certfile "$CERT_DIR/server.pem" \
  --ssl-keyfile "$CERT_DIR/server-key.pem"
