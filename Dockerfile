# FastAPI + Nginx application image. PostgreSQL runs in mux-db.
FROM python:3.10-slim

ARG DEBIAN_MIRROR=mirrors.ustc.edu.cn
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN sed -i "s/deb.debian.org/${DEBIAN_MIRROR}/g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i "s/deb.debian.org/${DEBIAN_MIRROR}/g" /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        nginx \
        openssl \
        postgresql-client \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./
# The deployment script builds the Vue SPA locally before Docker starts.
COPY client/dist/ /var/www/html/
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/mux.conf
COPY docker-entrypoint.sh /usr/local/bin/mux-entrypoint

RUN rm -f /etc/nginx/sites-enabled/default \
    # The image runs as appuser, so the shell entrypoint must be readable as
    # well as executable by that user (macOS source modes can otherwise yield
    # 711 after `chmod +x`).
    && chmod 755 /usr/local/bin/mux-entrypoint \
    && chmod 644 /etc/supervisor/conf.d/mux.conf /etc/nginx/conf.d/default.conf \
    && sed -i 's|^[[:space:]]*pid .*;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf \
    && mkdir -p /app/uploads /backups /var/log/supervisor /var/log/nginx /var/lib/nginx /var/cache/nginx \
    && useradd --system --uid 10001 --create-home appuser \
    && chown -R appuser:appuser /app /backups /var/log/supervisor /var/log/nginx /var/lib/nginx /var/cache/nginx /var/www/html

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/ >/dev/null \
        && curl --fail --silent http://127.0.0.1:8080/ >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/mux-entrypoint"]
