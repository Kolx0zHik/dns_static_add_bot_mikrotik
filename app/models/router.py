from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouterConfig:
    """MikroTik connection and access settings."""

    id: str
    name: str
    host: str
    port: int
    user: str
    password: str
    allowed_users: frozenset[int]
    ssh_timeout: float = 10.0

