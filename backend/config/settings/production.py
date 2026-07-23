from decouple import config

from .base import *  # noqa: F401, F403

SECURE_SSL_REDIRECT = False  # handled by nginx/load balancer

# Default to True (a real deployment should terminate TLS somewhere), but
# make it overridable: with a "Secure" flag set, browsers silently refuse
# to store the session/csrftoken cookie when the site is served over plain
# HTTP (e.g. an internal LAN demo box with no TLS anywhere in the stack),
# which breaks every cookie+CSRF based form post — including admin login —
# with a 403 and no indication why.
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", cast=bool, default=True)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", cast=bool, default=True)

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
