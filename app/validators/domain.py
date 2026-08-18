from __future__ import annotations

import re
from ipaddress import ip_address

from app.services.exceptions import ValidationError

MAX_DOMAIN_LENGTH = 253
MAX_LABEL_LENGTH = 63
MIN_LABEL_COUNT = 2
DOMAIN_PATTERN = re.compile(r"^[a-z0-9.-]+$")
FORBIDDEN_SCHEMES = ("http://", "https://", "ftp://")
FORBIDDEN_CHARS = frozenset("/\\?#&:%@")


def normalize_and_validate_domain(raw_domain: str) -> str:
    """Normalize and validate a DNS name for a MikroTik FWD record."""

    domain = raw_domain.strip().lower()

    if domain == "":
        raise ValidationError("Введите доменное имя.")

    if len(domain) > MAX_DOMAIN_LENGTH:
        raise ValidationError("Доменное имя слишком длинное.")

    if domain.startswith(FORBIDDEN_SCHEMES):
        raise ValidationError("Введите домен без протокола.")

    if any(char in domain for char in FORBIDDEN_CHARS):
        raise ValidationError("Домен содержит недопустимые символы.")

    if domain.startswith("."):
        raise ValidationError("Домен не должен начинаться с точки.")

    if domain.endswith("."):
        raise ValidationError("Домен не должен заканчиваться точкой.")

    if ".." in domain:
        raise ValidationError("Домен не должен содержать две точки подряд.")

    if not DOMAIN_PATTERN.fullmatch(domain):
        raise ValidationError("Разрешены только латинские буквы, цифры, дефис и точки.")

    labels = domain.split(".")
    if len(labels) < MIN_LABEL_COUNT:
        raise ValidationError("Введите полное доменное имя.")

    for label in labels:
        if len(label) > MAX_LABEL_LENGTH:
            raise ValidationError("Одна из частей домена слишком длинная.")
        if label.startswith("-") or label.endswith("-"):
            raise ValidationError("Часть домена не должна начинаться или заканчиваться дефисом.")

    try:
        ip_address(domain)
    except ValueError:
        return domain

    raise ValidationError("IP-адрес нельзя использовать вместо доменного имени.")


def normalize_and_validate_domains(raw_domains: str) -> tuple[str, ...]:
    """Normalize and validate DNS names supplied one per line."""

    domains: list[str] = []
    seen_domains: set[str] = set()
    for line_number, raw_domain in enumerate(raw_domains.splitlines(), start=1):
        if raw_domain.strip() == "":
            continue
        try:
            domain = normalize_and_validate_domain(raw_domain)
        except ValidationError as exc:
            raise ValidationError(f"Строка {line_number}: {exc.user_message}") from exc
        if domain in seen_domains:
            raise ValidationError(f"Строка {line_number}: домен {domain} указан повторно.")
        seen_domains.add(domain)
        domains.append(domain)

    if not domains:
        raise ValidationError("Введите хотя бы одно доменное имя.")

    return tuple(domains)
