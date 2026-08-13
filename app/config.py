from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    bot_token: str
    allowed_users: frozenset[int]
    mikrotik_host: str
    mikrotik_port: int
    mikrotik_user: str
    mikrotik_password: str
    ssh_timeout: float = 10.0


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Environment variable {name} is required")
    return value.strip()


def _parse_allowed_users(raw_value: str) -> frozenset[int]:
    users: set[int] = set()
    for raw_user_id in raw_value.split(","):
        user_id = raw_user_id.strip()
        if user_id == "":
            continue
        try:
            users.add(int(user_id))
        except ValueError as exc:
            raise ValueError("ALLOWED_USERS must contain comma-separated integers") from exc

    if not users:
        raise ValueError("ALLOWED_USERS must contain at least one Telegram user ID")

    return frozenset(users)


def load_settings() -> Settings:
    """Load validated settings from environment variables."""

    return Settings(
        bot_token=_get_required_env("BOT_TOKEN"),
        allowed_users=_parse_allowed_users(_get_required_env("ALLOWED_USERS")),
        mikrotik_host=_get_required_env("MIKROTIK_HOST"),
        mikrotik_port=int(os.getenv("MIKROTIK_PORT", "22")),
        mikrotik_user=_get_required_env("MIKROTIK_USER"),
        mikrotik_password=_get_required_env("MIKROTIK_PASSWORD"),
        ssh_timeout=float(os.getenv("SSH_TIMEOUT", "10")),
    )
