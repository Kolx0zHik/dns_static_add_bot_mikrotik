from app.models.dns import DnsStaticRecord
from app.services.routeros_commands import (
    build_add_dns_static_record_command,
    build_find_dns_static_record_command,
)


def test_build_find_dns_static_record_command() -> None:
    assert (
        build_find_dns_static_record_command("example.com")
        == '/ip dns static print count-only where name="example.com" type=FWD'
    )


def test_build_add_dns_static_record_command() -> None:
    command = build_add_dns_static_record_command(DnsStaticRecord(domain="example.com"))

    assert command == (
        "/ip dns static add "
        'name="example.com" '
        "type=FWD "
        'forward-to="CloudFlare" '
        'ttl="1d" '
        "match-subdomain=yes "
        'address-list="to-VPN"'
    )
