from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DnsStaticRecord:
    """DNS static FWD record requested by a Telegram user."""

    domain: str
    forward_to: str = "CloudFlare"
    ttl: str = "1d"
    address_list: str = "to-VPN"
    match_subdomain: bool = True


@dataclass(frozen=True, slots=True)
class AddDnsRecordsResult:
    """Result of adding multiple DNS static FWD records."""

    added: tuple[str, ...]
    already_existed: tuple[str, ...]
