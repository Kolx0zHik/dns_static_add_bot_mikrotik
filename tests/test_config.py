from __future__ import annotations

import pytest

from app.config import RouterCatalog, load_settings
from app.models.router import RouterConfig


def _set_common_router_env(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("MIKROTIK_ROUTERS", "office,home")
    monkeypatch.setenv("MIKROTIK_OFFICE_HOST", "192.0.2.10")
    monkeypatch.setenv("MIKROTIK_OFFICE_USER", "admin")
    monkeypatch.setenv("MIKROTIK_OFFICE_PASSWORD", "office-secret")
    monkeypatch.setenv("MIKROTIK_OFFICE_ALLOWED_USERS", "111")
    monkeypatch.setenv("MIKROTIK_HOME_HOST", "192.0.2.20")
    monkeypatch.setenv("MIKROTIK_HOME_USER", "admin")
    monkeypatch.setenv("MIKROTIK_HOME_PASSWORD", "home-secret")
    monkeypatch.setenv("MIKROTIK_HOME_ALLOWED_USERS", "222")


def test_load_settings_supports_multiple_routers(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("MIKROTIK_ROUTERS", "office,home")
    monkeypatch.setenv("MIKROTIK_OFFICE_NAME", "Office")
    monkeypatch.setenv("MIKROTIK_OFFICE_HOST", "192.0.2.10")
    monkeypatch.setenv("MIKROTIK_OFFICE_USER", "admin")
    monkeypatch.setenv("MIKROTIK_OFFICE_PASSWORD", "office-secret")
    monkeypatch.setenv("MIKROTIK_OFFICE_ALLOWED_USERS", "111,222")
    monkeypatch.setenv("MIKROTIK_HOME_NAME", "Home")
    monkeypatch.setenv("MIKROTIK_HOME_HOST", "192.0.2.20")
    monkeypatch.setenv("MIKROTIK_HOME_PORT", "2222")
    monkeypatch.setenv("MIKROTIK_HOME_USER", "admin")
    monkeypatch.setenv("MIKROTIK_HOME_PASSWORD", "home-secret")
    monkeypatch.setenv("MIKROTIK_HOME_ALLOWED_USERS", "222")

    settings = load_settings()

    assert settings.allowed_users == frozenset({111, 222})
    assert [router.id for router in settings.routers] == ["office", "home"]
    assert settings.routers[0].name == "Office"
    assert settings.routers[0].allowed_users == frozenset({111, 222})
    assert settings.routers[1].port == 2222
    assert settings.routers[1].allowed_users == frozenset({222})


def test_load_settings_keeps_single_router_compatibility(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_USERS", "111")
    monkeypatch.setenv("MIKROTIK_HOST", "192.0.2.10")
    monkeypatch.setenv("MIKROTIK_USER", "admin")
    monkeypatch.setenv("MIKROTIK_PASSWORD", "secret")

    settings = load_settings()

    assert settings.allowed_users == frozenset({111})
    assert len(settings.routers) == 1
    assert settings.routers[0].id == "default"
    assert settings.routers[0].host == "192.0.2.10"


@pytest.mark.parametrize(
    ("variable", "value", "message"),
    [
        ("MIKROTIK_ROUTERS", "office,office", "duplicate"),
        ("MIKROTIK_ROUTERS", "office-bad", "only latin"),
        ("MIKROTIK_OFFICE_ALLOWED_USERS", ",", "at least one"),
        ("MIKROTIK_OFFICE_ALLOWED_USERS", "user", "comma-separated integers"),
        ("MIKROTIK_OFFICE_PORT", "0", "between 1 and 65535"),
        ("MIKROTIK_OFFICE_PORT", "ssh", "must be an integer"),
        ("SSH_TIMEOUT", "0", "greater than zero"),
        ("SSH_TIMEOUT", "nan", "finite number"),
    ],
)
def test_load_settings_rejects_invalid_router_configuration(
    monkeypatch,
    variable: str,
    value: str,
    message: str,
) -> None:
    _set_common_router_env(monkeypatch)
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValueError, match=message):
        load_settings()


def test_router_catalog_returns_only_routers_allowed_for_user() -> None:
    routers = (
        RouterConfig(
            id="office",
            name="Office",
            host="192.0.2.10",
            port=22,
            user="admin",
            password="secret",
            allowed_users=frozenset({111}),
        ),
        RouterConfig(
            id="home",
            name="Home",
            host="192.0.2.20",
            port=22,
            user="admin",
            password="secret",
            allowed_users=frozenset({222}),
        ),
    )
    catalog = RouterCatalog(routers)

    assert catalog.get("office") == routers[0]
    assert catalog.get("missing") is None
    assert catalog.accessible_for_user(111) == (routers[0],)
    assert catalog.accessible_for_user(999) == ()
    assert catalog.accessible_for_user(None) == ()
