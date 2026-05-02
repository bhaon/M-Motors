#!/bin/sh
set -e
SSL_DIR=/etc/nginx/ssl
mkdir -p "$SSL_DIR"
if [ ! -s "$SSL_DIR/cert.pem" ] || [ ! -s "$SSL_DIR/key.pem" ]; then
  echo "nginx: génération d'un certificat TLS auto-signé (${SSL_CERT_CN:-localhost})…"
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
    -keyout "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" \
    -subj "/CN=${SSL_CERT_CN:-localhost}/O=M-Motors"
fi
exec nginx -g "daemon off;"
