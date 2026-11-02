import os


def _env_flag(name, default="0"):
    return os.environ.get(name, default) == "1"


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return int(default)


class Config:
    FINWISE_ENV = os.environ.get("FINWISE_ENV", "development")
    SECRET_KEY = os.environ.get("FINWISE_SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get("FINWISE_DATABASE_URL", "sqlite:///finwise.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_flag("FINWISE_HTTPS")
    FINWISE_HTTPS = _env_flag("FINWISE_HTTPS")
    # CR-04 decision: no automatic session timeout. Sessions end on logout,
    # password change (session_version), or account deletion.

    RATELIMIT_STORAGE_URI = os.environ.get("FINWISE_RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_ENABLED = True
    WTF_CSRF_ENABLED = True

    # None selects the environment-aware notifier (console in development,
    # fail-closed in production). Tests set this to a list sink.
    OTP_SINK = None

    # Production email delivery over SMTP.
    SMTP_HOST = os.environ.get("FINWISE_SMTP_HOST", "")
    SMTP_PORT = _env_int("FINWISE_SMTP_PORT", 587)
    SMTP_USERNAME = os.environ.get("FINWISE_SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("FINWISE_SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("FINWISE_SMTP_FROM", "")
    SMTP_USE_TLS = _env_flag("FINWISE_SMTP_USE_TLS", "1")

    # Production SMS delivery through a generic JSON HTTP webhook.
    SMS_WEBHOOK_URL = os.environ.get("FINWISE_SMS_WEBHOOK_URL", "")
    SMS_WEBHOOK_TOKEN = os.environ.get("FINWISE_SMS_WEBHOOK_TOKEN", "")

    # De-identified audit rows are purged after 30 to 50 days.
    AUDIT_RETENTION_DAYS = _env_int("FINWISE_AUDIT_RETENTION_DAYS", 30)

    # Tests and local development create tables automatically. Production
    # defaults to off so deployments run `flask db upgrade` instead.
    AUTO_CREATE_DB = os.environ.get(
        "FINWISE_AUTO_CREATE", "0" if FINWISE_ENV == "production" else "1"
    ) == "1"

    BCRYPT_ROUNDS = 12
    SIGNUP_OTP_TTL_MINUTES = 10
    RESET_OTP_TTL_MINUTES = 15


class TestConfig(Config):
    TESTING = True
    FINWISE_ENV = "test"
    SECRET_KEY = "test-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False
    OTP_SINK = []
    AUTO_CREATE_DB = True


class CsrfTestConfig(TestConfig):
    """CSRF protection enabled, rate limiting disabled."""

    WTF_CSRF_ENABLED = True


class RateLimitTestConfig(TestConfig):
    """Rate limiting enabled, CSRF disabled."""

    RATELIMIT_ENABLED = True


class SecurityTestConfig(TestConfig):
    """Both CSRF and rate limiting enabled."""

    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = True
