# Reverse-proxy HTTPS : frontend Next.js + API & docs FastAPI
FROM nginx:1.27-alpine

RUN apk add --no-cache openssl curl

RUN rm -f /etc/nginx/conf.d/default.conf
COPY default.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -k -fsS "https://127.0.0.1/api/health" -o /dev/null || exit 1

EXPOSE 80 443

ENTRYPOINT ["/docker-entrypoint.sh"]
