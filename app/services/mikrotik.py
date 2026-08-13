from __future__ import annotations

import logging
import time

from app.models.dns import DnsStaticRecord
from app.services.exceptions import RecordAlreadyExistsError, SshCommandError
from app.services.routeros_commands import (
    build_add_dns_static_record_command,
    build_find_dns_static_record_command,
)
from app.services.ssh import SshClient

logger = logging.getLogger(__name__)


class MikroTikDnsService:
    """Service for MikroTik DNS static operations."""

    def __init__(self, ssh_client: SshClient) -> None:
        self._ssh_client = ssh_client

    def record_exists(self, domain: str) -> bool:
        """Check whether a DNS static FWD record exists."""

        result = self._ssh_client.execute(build_find_dns_static_record_command(domain))
        try:
            return int(result.stdout or "0") > 0
        except ValueError as exc:
            logger.error("Unexpected MikroTik response for DNS record lookup: %s", result.stdout)
            raise SshCommandError() from exc

    def add_fwd_record(self, domain: str) -> None:
        """Add a DNS static FWD record if it does not exist."""

        started_at = time.monotonic()
        logger.info("Checking DNS static record domain=%s", domain)
        if self.record_exists(domain):
            logger.info("DNS static record already exists domain=%s", domain)
            raise RecordAlreadyExistsError()

        logger.info("Adding DNS static FWD record domain=%s", domain)
        self._ssh_client.execute(
            build_add_dns_static_record_command(DnsStaticRecord(domain=domain)),
        )
        logger.info(
            "DNS static FWD record added domain=%s duration=%.3fs",
            domain,
            time.monotonic() - started_at,
        )
