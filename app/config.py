from __future__ import annotations

import os
from dataclasses import dataclass
from math import isfinite
from re import fullmatch

from app.models.router import RouterConfig


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables."""

    bot_token: str
    allowed_users: frozenset[int]
    routers: tuple[RouterConfig, ...]


class RouterCatalog:
    """Catalog of configured MikroTik routers with per-user access checks."""

    def __init__(self, routers: tuple[RouterConfig, ...]) -> None:
        self._routers = {router.id: router for router in routers}

    def get(self, router_id: str) -> RouterConfig | None:
        """Return router by ID, if it exists."""

        return self._routers.get(router_id)

    def accessible_for_user(self, user_id: int | None) -> tuple[RouterConfig, ...]:
        """Return routers available for a Telegram user."""

        if user_id is None:
            return ()
        return tuple(
            router
            for router in self._routers.values()
            if user_id in router.allowed_users
        )


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ValueError(f"Environment variable {name} is required")
    return value.strip()


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _parse_allowed_users(raw_value: str, env_name: str) -> frozenset[int]:
    users: set[int] = set()
    for raw_user_id in raw_value.split(","):
        user_id = raw_user_id.strip()
        if user_id == "":
            continue
        try:
            users.add(int(user_id))
        except ValueError as exc:
            raise ValueError(
                f"{env_name} must contain comma-separated integers",
            ) from exc

    if not users:
        raise ValueError(f"{env_name} must contain at least one Telegram user ID")

    return frozenset(users)


def _parse_global_allowed_users() -> frozenset[int]:
    raw_value = _get_optional_env("ALLOWED_USERS")
    if raw_value is None:
        return frozenset()
    return _parse_allowed_users(raw_value, "ALLOWED_USERS")


def _parse_port(env_name: str, default: str = "22") -> int:
    raw_value = os.getenv(env_name, default).strip()
    try:
        port = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{env_name} must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"{env_name} must be between 1 and 65535")
    return port


def _parse_timeout() -> float:
    raw_value = os.getenv("SSH_TIMEOUT", "10").strip()
    try:
        timeout = float(raw_value)
    except ValueError as exc:
        raise ValueError("SSH_TIMEOUT must be a number") from exc
    if not isfinite(timeout) or timeout <= 0:
        raise ValueError("SSH_TIMEOUT must be a finite number greater than zero")
    return timeout


def _validate_router_id(router_id: str) -> str:
    normalized_id = router_id.strip().lower()
    if fullmatch(r"[a-z0-9_]+", normalized_id) is None:
        raise ValueError(
            "MIKROTIK_ROUTERS must contain IDs with only latin letters, digits, "
            "and underscores",
        )
    return normalized_id


def _router_env_prefix(router_id: str) -> str:
    return f"MIKROTIK_{router_id.upper()}"


def _load_router(router_id: str, default_allowed_users: frozenset[int]) -> RouterConfig:
    prefix = _router_env_prefix(router_id)
    raw_allowed_users = _get_optional_env(f"{prefix}_ALLOWED_USERS")
    allowed_users = (
        _parse_allowed_users(raw_allowed_users, f"{prefix}_ALLOWED_USERS")
        if raw_allowed_users is not None
        else default_allowed_users
    )
    if not allowed_users:
        raise ValueError(f"{prefix}_ALLOWED_USERS or ALLOWED_USERS is required")

    return RouterConfig(
        id=router_id,
        name=_get_optional_env(f"{prefix}_NAME") or router_id,
        host=_get_required_env(f"{prefix}_HOST"),
        port=_parse_port(f"{prefix}_PORT"),
        user=_get_required_env(f"{prefix}_USER"),
        password=_get_required_env(f"{prefix}_PASSWORD"),
        allowed_users=allowed_users,
        ssh_timeout=_parse_timeout(),
    )


def _load_routers(default_allowed_users: frozenset[int]) -> tuple[RouterConfig, ...]:
    raw_router_ids = _get_optional_env("MIKROTIK_ROUTERS")
    if raw_router_ids is None:
        if not default_allowed_users:
            raise ValueError(
                "ALLOWED_USERS is required for single-router configuration",
            )
        return (
            RouterConfig(
                id="default",
                name=_get_optional_env("MIKROTIK_NAME") or "MikroTik",
                host=_get_required_env("MIKROTIK_HOST"),
                port=_parse_port("MIKROTIK_PORT"),
                user=_get_required_env("MIKROTIK_USER"),
                password=_get_required_env("MIKROTIK_PASSWORD"),
                allowed_users=default_allowed_users,
                ssh_timeout=_parse_timeout(),
            ),
        )

    router_ids = tuple(
        _validate_router_id(raw_router_id)
        for raw_router_id in raw_router_ids.split(",")
        if raw_router_id.strip() != ""
    )
    if not router_ids:
        raise ValueError("MIKROTIK_ROUTERS must contain at least one router ID")
    if len(set(router_ids)) != len(router_ids):
        raise ValueError("MIKROTIK_ROUTERS must not contain duplicate router IDs")

    return tuple(
        _load_router(router_id, default_allowed_users) for router_id in router_ids
    )


def load_settings() -> Settings:
    """Load validated settings from environment variables."""

    allowed_users = _parse_global_allowed_users()
    routers = _load_routers(allowed_users)
    return Settings(
        bot_token=_get_required_env("BOT_TOKEN"),
        allowed_users=frozenset().union(*(router.allowed_users for router in routers)),
        routers=routers,
    )
