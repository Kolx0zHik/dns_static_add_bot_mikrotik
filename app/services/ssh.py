from __future__ import annotations

import logging
from dataclasses import dataclass

import paramiko

from app.config import Settings
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

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def execute(self, command: str) -> SshCommandResult:
        """Execute a command and return stdout, stderr, and exit status."""

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            logger.info("Connecting to MikroTik host=%s", self._settings.mikrotik_host)
            client.connect(
                hostname=self._settings.mikrotik_host,
                port=self._settings.mikrotik_port,
                username=self._settings.mikrotik_user,
                password=self._settings.mikrotik_password,
                timeout=self._settings.ssh_timeout,
                banner_timeout=self._settings.ssh_timeout,
                auth_timeout=self._settings.ssh_timeout,
                look_for_keys=False,
                allow_agent=False,
            )

            logger.info("Executing RouterOS command")
            _stdin, stdout, stderr = client.exec_command(
                command,
                timeout=self._settings.ssh_timeout,
            )
            exit_status = stdout.channel.recv_exit_status()
            result = SshCommandResult(
                stdout=stdout.read().decode("utf-8", errors="replace").strip(),
                stderr=stderr.read().decode("utf-8", errors="replace").strip(),
                exit_status=exit_status,
            )

            if result.exit_status != 0:
                logger.error(
                    "RouterOS command failed exit_status=%s stderr=%s",
                    result.exit_status,
                    result.stderr,
                )
                raise SshCommandError()

            return result
        except paramiko.AuthenticationException as exc:
            logger.exception("MikroTik SSH authentication failed")
            raise SshAuthenticationError() from exc
        except (paramiko.SSHException, OSError, TimeoutError) as exc:
            logger.exception("MikroTik SSH connection failed")
            raise SshConnectionError() from exc
        finally:
            client.close()
