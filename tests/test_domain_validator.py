import pytest

from app.services.exceptions import ValidationError
from app.validators.domain import normalize_and_validate_domain, normalize_and_validate_domains


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


def test_normalize_and_validate_domains_accepts_domains_one_per_line() -> None:
    assert normalize_and_validate_domains(
        " Example.COM \n\nsub.example.com\r\nthird.example.com",
    ) == (
        "example.com",
        "sub.example.com",
        "third.example.com",
    )


def test_normalize_and_validate_domains_reports_invalid_line() -> None:
    with pytest.raises(ValidationError, match=r"^Строка 3: Введите домен без протокола\.$"):
        normalize_and_validate_domains("example.com\n\nhttps://invalid.example.com")


def test_normalize_and_validate_domains_rejects_normalized_duplicate() -> None:
    with pytest.raises(
        ValidationError,
        match=r"^Строка 2: домен example\.com указан повторно\.$",
    ):
        normalize_and_validate_domains("Example.com\nexample.COM")


def test_normalize_and_validate_domains_rejects_empty_list() -> None:
    with pytest.raises(ValidationError, match="Введите хотя бы одно доменное имя"):
        normalize_and_validate_domains("\n  \n")
