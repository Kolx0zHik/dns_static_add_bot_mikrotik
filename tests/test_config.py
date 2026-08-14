from __future__ import annotations

from app.config import load_settings


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
