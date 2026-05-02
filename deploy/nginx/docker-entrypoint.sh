#!/bin/sh
set -e
SSL_DIR=/etc/nginx/ssl
mkdir -p "$SSL_DIR"
if [ ! -s "$SSL_DIR/cert.pem" ] || [ ! -s "$SSL_DIR/key.pem" ]; then
  CN="${SSL_CERT_CN:-localhost}"
  echo "nginx: génération d'un certificat TLS auto-signé (CN=$CN)…"
  # SAN requis par les navigateurs pour une IP ou un nom d’hôte (éviter erreur NET::ERR_CERT_COMMON_NAME_INVALID)
  if echo "$CN" | grep -qE '^[0-9]{1,3}(\.[0-9]{1,3}){3}$'; then
    SAN="subjectAltName=IP:${CN}"
  else
    SAN="subjectAltName=DNS:${CN}"
  fi
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" \
    -subj "/CN=${CN}/O=M-Motors" \
    -addext "$SAN"
fi
exec nginx -g "daemon off;"
