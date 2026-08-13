import pytest

from app.services.exceptions import ValidationError
from app.validators.domain import normalize_and_validate_domain


@pytest.mark.parametrize(
    ("raw_domain", "expected"),
    [
        ("Example.COM", "example.com"),
        ("  sub.example.com  ", "sub.example.com"),
        ("xn--e1afmkfd.xn--p1ai", "xn--e1afmkfd.xn--p1ai"),
    ],
)
def test_normalize_and_validate_domain_accepts_valid_domains(
    raw_domain: str,
    expected: str,
) -> None:
    assert normalize_and_validate_domain(raw_domain) == expected


@pytest.mark.parametrize(
    "raw_domain",
    [
        "",
        "   ",
        "https://example.com",
        "http://example.com",
        "ftp://example.com",
        "example.com/",
        "example.com/test",
        "192.168.1.1",
        "example..com",
        ".example.com",
        "example.com.",
        "bad_domain.com",
        "-example.com",
        "example-.com",
        "example.com:443",
    ],
)
def test_normalize_and_validate_domain_rejects_invalid_domains(raw_domain: str) -> None:
    with pytest.raises(ValidationError):
        normalize_and_validate_domain(raw_domain)
