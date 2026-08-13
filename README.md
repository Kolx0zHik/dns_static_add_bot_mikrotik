# Telegram-бот для управления MikroTik

Бот добавляет DNS Static записи типа FWD на MikroTik через SSH. На текущем этапе реализован сценарий `/add` с проверкой домена, подтверждением через Inline Keyboard и защитой по списку разрешенных Telegram ID.

## Запуск

1. Скопируйте `.env.example` в `.env`.
2. Заполните токен бота, разрешенные Telegram ID и SSH-параметры MikroTik.
3. Запустите:

```bash
docker compose up -d
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
