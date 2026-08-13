FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/Kolx0zHik/dns_static_add_bot_mikrotik"
LABEL org.opencontainers.image.description="Telegram bot for safe MikroTik DNS Static FWD management"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

CMD ["python", "-m", "app.bot"]
