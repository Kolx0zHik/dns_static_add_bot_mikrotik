# Telegram-бот для управления MikroTik

Бот добавляет DNS Static записи типа FWD на MikroTik через SSH. На текущем этапе реализованы главное inline-меню, сценарий `/add` с проверкой домена, подтверждением через Inline Keyboard и защитой по списку разрешенных Telegram ID.

## Запуск

1. Скопируйте `.env.example` в `.env`.
2. Заполните токен бота, разрешенные Telegram ID и SSH-параметры MikroTik.
3. Запустите:

```bash
docker compose up -d
```

По умолчанию `docker-compose.yml` использует опубликованный образ:

```text
ghcr.io/kolx0zhik/dns_static_add_bot_mikrotik:latest
```

Для локальной сборки используйте dev-compose:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

## Переменные окружения

- `BOT_TOKEN` - токен Telegram-бота.
- `ALLOWED_USERS` - разрешенные Telegram ID через запятую.
- `MIKROTIK_HOST` - адрес MikroTik.
- `MIKROTIK_PORT` - SSH-порт, по умолчанию `22`.
- `MIKROTIK_USER` - SSH-пользователь.
- `MIKROTIK_PASSWORD` - SSH-пароль.
- `SSH_TIMEOUT` - таймаут SSH-операций в секундах.

## Разработка

```bash
pip install -e ".[dev]"
black --check .
ruff check .
pytest
```

## CI/CD

При push в ветку `main` workflow `.github/workflows/docker-image.yml` запускает Black,
Ruff и pytest, затем собирает Docker-образ и публикует его в GitHub Container Registry:

```text
ghcr.io/kolx0zhik/dns_static_add_bot_mikrotik:latest
```

Также публикуется immutable-тег вида `sha-<commit>`.

GitHub Container Registry при первой публикации обычно создает package с приватной
visibility. После первого успешного workflow нужно один раз открыть package settings
на GitHub и переключить visibility в `Public`; следующие публикации этого же образа
останутся доступны публично.
