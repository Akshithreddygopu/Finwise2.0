# FinWise: Sprint 2

Personal finance tracking for individuals aged 15 and over. Manual entry only.
Sprint 2 adds budgets, savings goals, transaction filters and editing, custom
income categories, profile editing, email verification, password reset, data
export, account deletion, migrations and security hardening.

No AI features, SDKs or endpoints are part of Sprint 2.

## Stack

- Python 3.12, Flask 3, Flask-SQLAlchemy 3, Flask-Login, Flask-WTF (CSRF)
- Flask-Limiter, bcrypt, Flask-Migrate (Alembic), Jinja2
- Bootstrap 5.3.3 and Chart.js from CDN
- SQLite for local development; PostgreSQL-compatible models (no SQLite-only SQL)

Money is stored as integer paise in `BigInteger` columns. All money arithmetic
lives in `app/calculations.py` or `app/services/*`; templates and JavaScript only
display values produced by Python.

## Run locally

    python -m venv .venv
    .venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt

    # Create or upgrade the database schema.
    python -m flask --app run db upgrade

    python run.py                     # http://127.0.0.1:5000

The first application start seeds the 26 predefined categories once. Local
development uses `instance/finwise.db`.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `FINWISE_ENV` | `development` | `development`, `test` or `production` |
| `FINWISE_SECRET_KEY` | `dev-only-change-me` | Session/CSRF signing key; must be set in production |
| `FINWISE_DATABASE_URL` | `sqlite:///finwise.db` | SQLAlchemy database URI |
| `FINWISE_HTTPS` | `0` | `1` enables secure session cookies and HSTS |
| `FINWISE_RATELIMIT_STORAGE_URI` | `memory://` | Use Redis or another shared store for multi-process deployments |
| `FINWISE_AUTO_CREATE` | on in dev/test, off in production | Create tables at startup instead of running migrations |
| `FINWISE_SMTP_HOST` | empty | Production SMTP relay host; required for email delivery |
| `FINWISE_SMTP_PORT` | `587` | SMTP relay port |
| `FINWISE_SMTP_USERNAME` | empty | SMTP username, if required |
| `FINWISE_SMTP_PASSWORD` | empty | SMTP password, if required |
| `FINWISE_SMTP_FROM` | empty | From address for verification emails |
| `FINWISE_SMTP_USE_TLS` | `1` | Start TLS before SMTP authentication |
| `FINWISE_SMS_WEBHOOK_URL` | empty | JSON webhook URL for SMS delivery |
| `FINWISE_SMS_WEBHOOK_TOKEN` | empty | Optional bearer token for the SMS webhook |
| `FINWISE_AUDIT_RETENTION_DAYS` | `30` | De-identified audit retention, clamped to 30-50 days |

Production configuration must set a strong `FINWISE_SECRET_KEY`, `FINWISE_HTTPS=1`,
a real database URL, and must leave `FINWISE_AUTO_CREATE=0`. The default in-memory
rate-limit store is acceptable for the agreed single-process deployment; use a
shared store only if the app is later scaled across processes. Run
`flask --app run db upgrade` during deployment.

### Migrations

The committed migrations are:

- `migrations/versions/7b3a93274329_sprint_2_schema.py` — Sprint 2 schema
- `migrations/versions/2314b1c6d1c2_separate_password_reset_codes.py` — separate
  password-reset code table

    python -m flask --app run db upgrade
    python -m flask --app run db migrate -m "describe the change"   # after model edits
    python -m flask --app run db upgrade

### Importing an existing Sprint 1 database

Sprint 1 created its schema with `db.create_all()` and had no `alembic_version`
row, so an existing Sprint 1 database cannot be upgraded by Alembic in place.
The old local database was preserved as `instance/finwise-sprint1.db.bak` and
imported into the fresh Sprint 2 database with:

    python -m flask --app run import-sprint1-db instance/finwise-sprint1.db.bak

The importer copies users, custom categories, consents, transactions, budgets,
goals and audit rows, remaps primary keys, and skips old OTP hashes. Import only
into an empty database; the command refuses to run when users already exist.
Legacy accounts that never verified their email are imported as
`pending_verification` and must complete the new email verification step before
login. They are never marked as email-verified by the importer.

Back up any data you need before replacing a Sprint 1 database.

## Verification codes and delivery

- **Development:** codes and notices are printed to the server console with a
  `[FinWise DEVELOPMENT ONLY]` prefix. Never use this mode for public traffic.
- **Tests:** a list sink captures codes; nothing is printed.
- **Production:** email uses an SMTP relay and SMS uses a generic JSON webhook.
  Configure the `FINWISE_SMTP_*` and `FINWISE_SMS_WEBHOOK_*` settings above.
  Delivery fails closed when the required channel is not configured: registration
  and password reset return HTTP 503 with a friendly "not configured" message, and
  no code is printed or exposed.

Registration is two-step: verify email first, then verify the mobile number
(adults) or the parent/guardian mobile (users aged 15 to 17). A user cannot log in
until both steps are complete.

## What Sprint 2 covers

- **Budgets (FR-10, BR-06, AT-06):** one monthly budget per user, expressed in
  paise. Spending above budget is allowed and shown as a warning; the true
  percentage is displayed while the visual bar is capped at 100%. Months use the
  IST calendar.
- **Savings goals (FR-11, FR-19, BR-07, CR-03, AT-07):** target and saved amounts,
  optional target date, integer floor progress, target-reached state, once-only
  milestone messages, and a text equivalent for the jar visual. Goals are
  owner-scoped and follow the CR-03 guardrails.
- **Transactions (FR-04, FR-06, FR-08, BR-02, BR-10, AT-10):** filters by date
  range (inclusive), kind and category; 25 per page with clamped page bounds; edit
  and delete; totals and dashboards update after changes.
- **Custom income categories (FR-05, BR-08, BR-09):** user-private custom income
  categories, case-insensitive duplicate checks, predefined-name collision checks,
  length validation, and deletion blocked while transactions still use the category.
- **Profile (FR-03):** users can change their full name. Email, mobile, date of
  birth and parent details remain read-only; mobile numbers are masked.
- **Email verification (section 3F):** mandatory email OTP before mobile/parent OTP.
- **Password reset (FR-20, CR-04):** email or verified-mobile channel, parent mobile
  for minors, 15-minute expiry, single use, five-attempt lock, earlier codes
  invalidated, and identical responses for known and unknown emails.
- **Data export (FR-18):** password re-authentication required. JSON contains the
  profile, custom categories, transactions, budgets, goals and consent records;
  CSV contains transactions only. Parent mobile is not exported for minors.
  Limited to 3 exports per hour.
- **Account deletion (FR-18):** password plus exact `DELETE` confirmation, 3
  attempts per hour. Deletes transactions, budgets, goals, custom categories, OTP
  codes, password-reset codes and consents, then the user. Audit rows are retained
  but detached from the identity.
- **Security:** CSRF on every change, login and OTP rate limits, HMAC-hashed OTP
  codes, session invalidation after password reset or deletion, security headers
  and CSP, `no-store` on financial pages, generic error pages, and SQLite foreign
  keys enabled.

## Sprint 1 behaviour changes

- Registration now requires **email verification before** mobile or parent OTP.
  Sprint 1 tests were updated to complete the email step while keeping their
  original acceptance intents.
- Password reset now uses its own `password_reset_codes` table with purposes
  `password_reset` and `password_reset_parent`. Signup/contact verification stays
  in `otp_codes`. Both paths reuse the same HMAC, expiry, rate-limit and lockout
  rules, but reset activity is separate for reporting and audit.
- Sprint 1 accounts imported with `import-sprint1-db` are not auto-verified. A
  login attempt with the correct password resumes verification by sending the
  next required code.
- `User.session_version` invalidates old sessions after a password reset. There is
  no automatic idle timeout (CR-04 decision); sessions end on logout, password
  reset, or account deletion.
- Money columns are now `BigInteger` to avoid 32-bit integer overflow.
- New models: `Budget`, `SavingsGoal`, `AuditLog` and `PasswordResetCode`.

## Security and privacy notes

- Every user-data query filters by the signed-in user. Another user's record,
  budget, goal or custom category returns 404.
- OTP codes are six digits, HMAC-hashed at rest, expire after 10 minutes for
  signup and 15 minutes for reset, and lock after five wrong attempts.
- Password reset and deletion apply the same response to unknown accounts where
  applicable, avoiding account enumeration.
- All changes use POST with CSRF. Login, registration, OTP verification, password
  reset, export and deletion are rate-limited.
- The 500 page never shows a stack trace, and server logs avoid request values and
  SQL parameters that might contain secrets.
- De-identified audit rows are purged after 30-50 days, configurable with
  `FINWISE_AUDIT_RETENTION_DAYS` and enforced within that range. A long-running
  process checks at most once per hour.

## Known limitations

- Production email and SMS require operator-supplied SMTP and webhook settings;
  delivery fails closed until both are configured.
- Rate limiting defaults to in-memory storage and is not shared across processes.
  The owner confirmed a shared store is not required for this deployment.
- Audit logs are retained after account deletion in de-identified form, then
  purged after the configured 30-50 day window.
- Budgets are monthly only, and there is no rollover or multi-currency support.
- The export is a download, not an asynchronous job; large accounts may take time.
- No AI insights, chatbot, reports or forecasting exist yet (planned later).

## Tests

    python -m pytest -q

Current result: **110 passed** (100 test functions plus parametrised cases). The
suite covers:

| Area | File |
|---|---|
| Calculations, money formatting, budgets and goals | `tests/test_calculations.py` |
| Registration, login, age check, parent OTP | `tests/test_auth.py` |
| Email-first verification | `tests/test_email_verification.py` |
| Transactions, filters, pagination, edit/delete, cross-user 404s | `tests/test_records.py` |
| Budgets, IST month boundaries, over-budget display | `tests/test_budget.py` |
| Savings goals, milestones, visual text equivalent | `tests/test_goals.py` |
| Custom income categories | `tests/test_categories.py` |
| Profile editing and masking | `tests/test_profile.py` |
| Password reset, expiry, single use, lockout, session invalidation | `tests/test_password_reset.py` |
| JSON/CSV export and export limits | `tests/test_export.py` |
| Account deletion and data removal | `tests/test_account_deletion.py` |
| SMTP email and SMS webhook routing/fail-closed behaviour | `tests/test_notifiers.py` |
| Audit retention purge | `tests/test_audit_retention.py` |
| Sprint 1 database import and remapping | `tests/test_legacy_import.py` |
| CSRF, headers, rate limits, fail-closed delivery, foreign keys | `tests/test_security.py` |

Acceptance-test coverage includes AT-01, AT-02 (extended to all owned entities),
AT-03, AT-04, AT-06, AT-07, AT-10, AT-11 and AT-12.

## Project layout

    app/
      __init__.py          app factory, request ID, session guard, headers, errors
      calculations.py      integer-paise arithmetic and display helpers
      cli.py               import-sprint1-db command
      extensions.py        db, login, CSRF, limiter, migrate, rate-limit keys
      models.py            User, consent, OTP, reset code, category, transaction,
                           budget, goal, audit
      notifiers.py         console, test list, SMTP + SMS webhook production
      otp.py               HMAC hashing, expiry, attempt limits
      timeutils.py         IST calendar helpers
      blueprints/          auth, records, budgets, goals, categories, profile, account
      services/            accounts, records, budgets, goals, categories, exports,
                           deletion, audit, legacy import
      templates/           Jinja pages, partials and error pages
      static/              app.css and app.js (delete confirmation only)
    migrations/            Alembic environment and both Sprint 2 migrations
    tests/                 pytest suite and fixtures
    config.py              environment-aware configuration
    run.py                 local entry point
