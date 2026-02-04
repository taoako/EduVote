import re

# Intentionally lightweight and user-friendly. We validate on submit, not while typing.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    """Return True if email looks like a valid address.

    Used when the field is required.
    """
    value = (email or "").strip()
    if not value:
        return False
    return bool(_EMAIL_RE.match(value))


def is_valid_optional_email(email: str) -> bool:
    """Return True if email is empty or looks like a valid address."""
    value = (email or "").strip()
    if not value:
        return True
    return bool(_EMAIL_RE.match(value))
