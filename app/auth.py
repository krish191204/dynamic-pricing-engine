"""Email accounts stored in Postgres. Passwords are hashed. The database password stays in .env."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
COOKIE = "session"
SESSION_DAYS = 14
MIN_PASSWORD = 8
MAX_PASSWORD = 200
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SCHEMA = """
create table if not exists public.app_users (
  id bigint generated always as identity primary key,
  email text not null,
  password_hash text not null,
  created_at timestamptz not null default now(),
  constraint app_users_email_key unique (email),
  constraint app_users_email_lowercase check (email = lower(email))
);
alter table public.app_users enable row level security;
revoke all on table public.app_users from public;
"""


class AuthError(Exception):
    """A message that is safe to show on the sign-in page."""


def load_env() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_hex, digest_hex = stored.split("$")
        count = int(rounds)
        if algo != "pbkdf2_sha256" or not 1 <= count <= 400_000:
            return False
        got = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), count)
        return hmac.compare_digest(got, bytes.fromhex(digest_hex))
    except (TypeError, ValueError):
        return False


def _secret() -> bytes:
    secret = os.environ.get("SESSION_SECRET", "")
    if len(secret) < 16:
        raise AuthError("Sign-in is not configured.")
    return secret.encode()


def sign_session(user_id: int) -> str:
    exp = int(time.time()) + SESSION_DAYS * 24 * 3600
    payload = f"{user_id}.{exp}".encode()
    sig = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()
    return f"{payload.decode()}.{sig}"


def read_session(token: str | None) -> int | None:
    if not token:
        return None
    try:
        user_id, exp, sig = token.split(".")
        payload = f"{user_id}.{exp}".encode()
        expected = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(exp) < time.time():
            return None
        return int(user_id)
    except (AuthError, TypeError, ValueError):
        return None


def _require_config() -> None:
    if not os.environ.get("DATABASE_PASSWORD") or not os.environ.get("DATABASE_HOST"):
        raise AuthError("Sign-in storage is not configured.")
    _secret()


def connect():
    _require_config()
    try:
        return psycopg.connect(
            host=os.environ["DATABASE_HOST"],
            port=int(os.environ.get("DATABASE_PORT", "5432")),
            dbname=os.environ.get("DATABASE_NAME", "postgres"),
            user=os.environ.get("DATABASE_USER", "postgres"),
            password=os.environ["DATABASE_PASSWORD"],
            sslmode="require",
            connect_timeout=10,
        )
    except psycopg.Error as exc:
        raise AuthError("Sign-in storage is unavailable.") from exc


def ensure_schema() -> None:
    with connect() as conn:
        conn.execute(SCHEMA)
        conn.execute(
            """
            do $$
            declare
              role_name text;
            begin
              foreach role_name in array array['anon', 'authenticated', 'service_role']
              loop
                if exists (select 1 from pg_roles where rolname = role_name) then
                  execute format('revoke all on table public.app_users from %I', role_name);
                  execute format('revoke all on sequence public.app_users_id_seq from %I', role_name);
                end if;
              end loop;
            end $$;
            """
        )
        conn.commit()


def _email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise AuthError("Enter a valid email.")
    return email


def _password(value: str, *, creating: bool) -> str:
    if not value or not value.strip():
        raise AuthError("Enter an email and a password.")
    if len(value) > MAX_PASSWORD:
        raise AuthError("That password is too long.")
    if creating and len(value) < MIN_PASSWORD:
        raise AuthError("Use at least 8 characters.")
    return value


def create_account(email: str, password: str) -> int:
    if not email.strip() or not password:
        raise AuthError("Enter an email and a password.")
    email = _email(email)
    password = _password(password, creating=True)
    stored = hash_password(password)
    try:
        with connect() as conn:
            row = conn.execute(
                "insert into public.app_users (email, password_hash) values (%s, %s) returning id",
                (email, stored),
            ).fetchone()
            conn.commit()
    except psycopg.errors.UniqueViolation as exc:
        raise AuthError("An account with that email already exists.") from exc
    except AuthError:
        raise
    except psycopg.Error as exc:
        raise AuthError("Sign-in storage is unavailable.") from exc
    return int(row[0])


def authenticate(email: str, password: str) -> int:
    if not email.strip() or not password:
        raise AuthError("Enter an email and a password.")
    email = _email(email)
    _password(password, creating=False)
    try:
        with connect() as conn:
            row = conn.execute(
                "select id, password_hash from public.app_users where email = %s",
                (email,),
            ).fetchone()
    except AuthError:
        raise
    except psycopg.Error as exc:
        raise AuthError("Sign-in storage is unavailable.") from exc
    if row is None or not verify_password(password, row[1]):
        raise AuthError("Email or password is wrong.")
    return int(row[0])


def email_for(user_id: int) -> str | None:
    try:
        with connect() as conn:
            row = conn.execute(
                "select email from public.app_users where id = %s",
                (user_id,),
            ).fetchone()
    except (AuthError, psycopg.Error):
        return None
    return None if row is None else str(row[0])


load_env()
