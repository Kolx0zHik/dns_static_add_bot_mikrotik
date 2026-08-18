from __future__ import annotations

from app.services.mikrotik import MikroTikDnsService
from app.services.ssh import SshClient, SshCommandResult


class FakeSshClient(SshClient):
    def __init__(self, existing_domains: set[str]) -> None:
        self.existing_domains = existing_domains
        self.commands: list[str] = []

    def execute(self, command: str) -> SshCommandResult:
        self.commands.append(command)
        if "print count-only" in command:
            domain = command.split('name="', maxsplit=1)[1].split('"', maxsplit=1)[0]
            count = "1" if domain in self.existing_domains else "0"
            return SshCommandResult(stdout=count, stderr="", exit_status=0)
        return SshCommandResult(stdout="", stderr="", exit_status=0)


def test_add_fwd_records_adds_new_and_skips_existing_domains() -> None:
    ssh_client = FakeSshClient({"existing.example.com"})
    service = MikroTikDnsService("office", ssh_client)

    result = service.add_fwd_records(
        ("new.example.com", "existing.example.com", "second.example.com"),
    )

    assert result.added == ("new.example.com", "second.example.com")
    assert result.already_existed == ("existing.example.com",)
    add_commands = [command for command in ssh_client.commands if "/ip dns static add" in command]
    assert len(add_commands) == 2
    assert 'name="new.example.com"' in add_commands[0]
    assert 'name="second.example.com"' in add_commands[1]
