from __future__ import annotations

from app.models.dns import DnsStaticRecord


def _quote(value: str) -> str:
    escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped_value}"'


def build_find_dns_static_record_command(domain: str) -> str:
    """Build a RouterOS command that checks whether a DNS static record exists."""

    return f"/ip dns static print count-only where name={_quote(domain)} type=FWD"


def build_add_dns_static_record_command(record: DnsStaticRecord) -> str:
    """Build a RouterOS command that adds a DNS static FWD record."""

    match_subdomain = "yes" if record.match_subdomain else "no"
    return (
        "/ip dns static add "
        f"name={_quote(record.domain)} "
        "type=FWD "
        f"forward-to={_quote(record.forward_to)} "
        f"ttl={_quote(record.ttl)} "
        f"match-subdomain={match_subdomain} "
        f"address-list={_quote(record.address_list)}"
    )
