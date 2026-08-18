# Telegram-бот для управления MikroTik

Бот добавляет DNS Static записи типа FWD на MikroTik через SSH. Поддерживает несколько роутеров, разграничение доступа по Telegram ID для каждого MikroTik, главное inline-меню, сценарий `/add` с проверкой списка доменов и обязательным подтверждением.

## Запуск

1. Скопируйте `.env.example` в `.env`.
2. Заполните токен бота, список MikroTik и SSH-параметры.
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
- `SSH_TIMEOUT` - общий таймаут SSH-операций в секундах.
- `MIKROTIK_ROUTERS` - ID роутеров через запятую, например `office,home`.
- `MIKROTIK_<ID>_NAME` - понятное имя роутера в меню.
- `MIKROTIK_<ID>_HOST` - адрес MikroTik.
- `MIKROTIK_<ID>_PORT` - SSH-порт, по умолчанию `22`.
- `MIKROTIK_<ID>_USER` - SSH-пользователь.
- `MIKROTIK_<ID>_PASSWORD` - SSH-пароль.
- `MIKROTIK_<ID>_ALLOWED_USERS` - Telegram ID пользователей, которым доступен этот MikroTik.
- `ALLOWED_USERS` - опциональный общий список Telegram ID. Если для роутера не задан `MIKROTIK_<ID>_ALLOWED_USERS`, используется этот список.

Пример для двух MikroTik:

```env
BOT_TOKEN=123456:token
SSH_TIMEOUT=10

MIKROTIK_ROUTERS=office,home

MIKROTIK_OFFICE_NAME=Office MikroTik
MIKROTIK_OFFICE_HOST=192.0.2.10
MIKROTIK_OFFICE_PORT=22
MIKROTIK_OFFICE_USER=admin
MIKROTIK_OFFICE_PASSWORD=secret
MIKROTIK_OFFICE_ALLOWED_USERS=11111111,22222222

MIKROTIK_HOME_NAME=Home MikroTik
MIKROTIK_HOME_HOST=192.0.2.20
MIKROTIK_HOME_PORT=22
MIKROTIK_HOME_USER=admin
MIKROTIK_HOME_PASSWORD=secret
MIKROTIK_HOME_ALLOWED_USERS=22222222
```

Если нужен один MikroTik, можно оставить старый формат без `MIKROTIK_ROUTERS`:

```env
BOT_TOKEN=123456:token
ALLOWED_USERS=11111111,22222222
MIKROTIK_NAME=MikroTik
MIKROTIK_HOST=192.0.2.10
MIKROTIK_PORT=22
MIKROTIK_USER=admin
MIKROTIK_PASSWORD=secret
SSH_TIMEOUT=10
```

## Интерфейс

После `/start` бот показывает только те MikroTik, к которым у пользователя есть доступ. Если доступен один роутер, бот сразу открывает меню действий. Если доступно несколько, пользователь сначала выбирает роутер. Для добавления DNS FWD записей нужно отправить одним сообщением один или несколько доменов, каждый с новой строки, и подтвердить весь список. Уже существующие записи бот пропустит и покажет их отдельно в результате.

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
