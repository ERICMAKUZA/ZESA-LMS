"""Short-lived, single-use handoffs from the portal to Moodle."""

from __future__ import annotations

import hashlib
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache

from apps.enrollments.models import Enrollment, EnrollmentStatus

CODE_PREFIX = "moodle-sso:code:"
USED_PREFIX = "moodle-sso:used:"


class MoodleSsoNotConfigured(Exception):
    """Raised when the portal has not been given its Moodle SSO secret."""


def _code_digest(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _cache_key(prefix: str, code: str) -> str:
    return f"{prefix}{_code_digest(code)}"


def _active_course_ids(user) -> list[int]:
    return list(
        Enrollment.objects.filter(
            application__applicant=user,
            status=EnrollmentStatus.ENROLLED,
            is_suspended=False,
        )
        .exclude(moodle_course_id=0)
        .order_by("moodle_course_id")
        .values_list("moodle_course_id", flat=True)
        .distinct()
    )


def issue_moodle_sso_code(user) -> str:
    """Store the authenticated learner's Moodle identity outside the browser."""
    if not settings.MOODLE_SSO_SHARED_SECRET or not settings.MOODLE_BASE_URL:
        raise MoodleSsoNotConfigured

    moodle_email = user.zntc_email or user.email
    payload = {
        "user": {
            "email": moodle_email,
            "username": moodle_email.split("@", maxsplit=1)[0],
            "firstname": user.first_name,
            "lastname": user.last_name,
        },
        "course_ids": _active_course_ids(user),
    }
    ttl = settings.MOODLE_SSO_CODE_TTL_SECONDS

    # Cache.add guarantees a collision cannot overwrite another learner's code.
    for _ in range(3):
        code = secrets.token_urlsafe(32)
        if cache.add(_cache_key(CODE_PREFIX, code), payload, timeout=ttl):
            return code

    raise RuntimeError("Unable to create a Moodle sign-on code.")


def build_moodle_sso_url(code: str) -> str:
    query = urlencode({"code": code})
    return f"{settings.MOODLE_BASE_URL.rstrip('/')}/auth/zesa/sso.php?{query}"


def consume_moodle_sso_code(code: str) -> dict | None:
    """Return a code payload once only, preventing replay of a browser URL."""
    if not isinstance(code, str) or len(code) < 40 or len(code) > 128:
        return None

    ttl = settings.MOODLE_SSO_CODE_TTL_SECONDS
    code_key = _cache_key(CODE_PREFIX, code)
    used_key = _cache_key(USED_PREFIX, code)

    # The first consumer wins; all concurrent or repeated requests are rejected.
    if not cache.add(used_key, "1", timeout=ttl):
        return None

    payload = cache.get(code_key)
    if payload is None:
        return None

    cache.delete(code_key)
    return payload
