from __future__ import annotations

import logging
from dataclasses import dataclass

import paramiko

from app.models.router import RouterConfig
from app.services.exceptions import (
    SshAuthenticationError,
    SshCommandError,
    SshConnectionError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SshCommandResult:
    """Result of a command executed over SSH."""

    stdout: str
    stderr: str
    exit_status: int


class SshClient:
    """Centralized SSH client for MikroTik RouterOS commands."""

    def __init__(self, router: RouterConfig) -> None:
        self._router = router

    def execute(self, command: str) -> SshCommandResult:
        """Execute a command and return stdout, stderr, and exit status."""

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            logger.info(
                "Connecting to MikroTik router_id=%s host=%s",
                self._router.id,
                self._router.host,
            )
            client.connect(
                hostname=self._router.host,
                port=self._router.port,
                username=self._router.user,
                password=self._router.password,
                timeout=self._router.ssh_timeout,
                banner_timeout=self._router.ssh_timeout,
                auth_timeout=self._router.ssh_timeout,
                look_for_keys=False,
                allow_agent=False,
            )

            logger.info("Executing RouterOS command router_id=%s", self._router.id)
            _stdin, stdout, stderr = client.exec_command(
                command,
                timeout=self._router.ssh_timeout,
            )
            exit_status = stdout.channel.recv_exit_status()
            result = SshCommandResult(
                stdout=stdout.read().decode("utf-8", errors="replace").strip(),
                stderr=stderr.read().decode("utf-8", errors="replace").strip(),
                exit_status=exit_status,
            )

            if result.exit_status != 0:
                logger.error(
                    "RouterOS command failed router_id=%s exit_status=%s stderr=%s",
                    self._router.id,
                    result.exit_status,
                    result.stderr,
                )
                raise SshCommandError()

            return result
        except paramiko.AuthenticationException as exc:
            logger.exception("MikroTik SSH authentication failed router_id=%s", self._router.id)
            raise SshAuthenticationError() from exc
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            logger.exception("MikroTik SSH connection failed router_id=%s", self._router.id)
            raise SshConnectionError() from exc
        finally:
            client.close()
