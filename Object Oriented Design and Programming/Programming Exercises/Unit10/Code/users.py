"""User Management module: registration, authentication and sessions."""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from .database import Database
from .audit import AuditLog
from .errors import (AuthenticationError, DuplicateEmailError, NotFoundError, TooManyAttemptsError,
                     ValidationError)
from .security import require_role


class Role(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}$")
_COMMON_PASSWORDS = {"password123", "letmein12345", "qwerty123456", "admin1234567"}
SESSION_TTL_SECONDS = 1800
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW_SECONDS = 300


class PasswordRule:
    """Strategy interface: return a violation message, or None when the password passes."""

    def check(self, password: str) -> Optional[str]:
        raise NotImplementedError


class LengthRule(PasswordRule):
    def __init__(self, minimum: int = 10, maximum: int = 128) -> None:
        self._min, self._max = minimum, maximum

    def check(self, password: str) -> Optional[str]:
        if len(password) < self._min:
            return f"Password must be at least {self._min} characters long"
        if len(password) > self._max:
            return f"Password must be at most {self._max} characters long"
        return None


class CharacterMixRule(PasswordRule):
    def check(self, password: str) -> Optional[str]:
        if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
            return "Password must contain at least one letter and one digit"
        return None


class CommonPasswordRule(PasswordRule):
    def __init__(self, blocked: Optional[set] = None) -> None:
        self._blocked = {b.lower() for b in (blocked if blocked is not None else _COMMON_PASSWORDS)}

    def check(self, password: str) -> Optional[str]:
        return "That password is too common" if password.lower() in self._blocked else None


class PasswordPolicy:
    """Runs every rule and reports all violations together."""

    def __init__(self, rules: list) -> None:
        self._rules = rules

    @classmethod
    def default(cls) -> "PasswordPolicy":
        return cls([LengthRule(), CharacterMixRule(), CommonPasswordRule()])

    def validate(self, password: object) -> None:
        if not isinstance(password, str):
            raise ValidationError(["Password must be text"])
        violations = [v for v in (rule.check(password) for rule in self._rules) if v]
        if violations:
            raise ValidationError(violations)


@dataclass(frozen=True)
class User:
    id: int
    email: str
    role: Role
    created_at: float


class PasswordHasher:
    """Salted scrypt. The cost parameter n is injectable so tests can run quickly."""

    def __init__(self, n: int = 2 ** 14) -> None:
        self._n = n

    def hash(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=self._n, r=8, p=1, dklen=32)
        return f"scrypt${self._n}${salt.hex()}${digest.hex()}"

    def verify(self, password: str, stored: str) -> bool:
        try:
            _, n, salt_hex, digest_hex = stored.split("$")
            digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                                    n=int(n), r=8, p=1, dklen=32)
        except (ValueError, TypeError, AttributeError):
            return False
        return hmac.compare_digest(digest, bytes.fromhex(digest_hex))


class SqliteUserRepository:
    """Data access layer. Every query is parameterised, so input is never part of the SQL text."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, email: str, password_hash: str, role: Role, created_at: float) -> User:
        try:
            with self._db.transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                    (email, password_hash, role.value, created_at))
        except sqlite3.IntegrityError:
            raise DuplicateEmailError("An account with that email already exists") from None
        return User(cursor.lastrowid, email, role, created_at)

    def find_by_email(self, email: str) -> Optional[tuple]:
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return (self._to_user(row), row["password_hash"]) if row else None

    def get(self, user_id: int) -> Optional[User]:
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._to_user(row) if row else None

    def get_with_hash(self, user_id: int) -> Optional[tuple]:
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return (self._to_user(row), row["password_hash"]) if row else None

    def update_password_hash(self, user_id: int, password_hash: str) -> None:
        with self._db.transaction() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))

    def update_role(self, user_id: int, role: Role) -> bool:
        with self._db.transaction() as conn:
            cursor = conn.execute("UPDATE users SET role = ? WHERE id = ?", (role.value, user_id))
        return cursor.rowcount == 1

    @staticmethod
    def _to_user(row) -> User:
        return User(row["id"], row["email"], Role(row["role"]), row["created_at"])


class SessionManager:
    """Issues opaque random tokens. Only a SHA-256 digest of each token is kept server side."""

    def __init__(self, clock: Callable[[], float], ttl: int = SESSION_TTL_SECONDS) -> None:
        self._clock = clock
        self._ttl = ttl
        self._sessions: dict = {}
        self._lock = threading.Lock()

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def create(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[self._digest(token)] = (user_id, self._clock() + self._ttl)
        return token

    def resolve(self, token: object) -> int:
        if not isinstance(token, str) or not token:
            raise AuthenticationError("Invalid or expired session")
        key = self._digest(token)
        with self._lock:
            entry = self._sessions.get(key)
            if entry is None or entry[1] <= self._clock():
                self._sessions.pop(key, None)
                raise AuthenticationError("Invalid or expired session")
            return entry[0]

    def revoke(self, token: object) -> None:
        if isinstance(token, str):
            with self._lock:
                self._sessions.pop(self._digest(token), None)

    def revoke_all_for_user(self, user_id: int) -> None:
        with self._lock:
            for key in [k for k, (uid, _) in self._sessions.items() if uid == user_id]:
                del self._sessions[key]


class LoginThrottle:
    """Counts recent failures per (client, email) so one client cannot lock out everyone."""

    def __init__(self, clock: Callable[[], float], max_failures: int = MAX_FAILED_LOGINS,
                 window: int = LOCKOUT_WINDOW_SECONDS) -> None:
        self._clock = clock
        self._max = max_failures
        self._window = window
        self._failures: dict = {}
        self._lock = threading.Lock()

    def _recent(self, key: tuple) -> list:
        cutoff = self._clock() - self._window
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def check(self, key: tuple) -> None:
        with self._lock:
            if len(self._recent(key)) >= self._max:
                raise TooManyAttemptsError("Too many failed attempts, try again later")

    def record_failure(self, key: tuple) -> None:
        with self._lock:
            self._recent(key)
            self._failures.setdefault(key, []).append(self._clock())

    def reset(self, key: tuple) -> None:
        with self._lock:
            self._failures.pop(key, None)


class UserService:
    def __init__(self, repo: SqliteUserRepository, hasher: PasswordHasher,
                 clock: Callable[[], float] = time.time, audit: Optional[AuditLog] = None,
                 policy: Optional[PasswordPolicy] = None) -> None:
        self._repo = repo
        self._policy = policy or PasswordPolicy.default()
        self._hasher = hasher
        self._clock = clock
        self._audit = audit or AuditLog()
        self._sessions = SessionManager(clock)
        self._throttle = LoginThrottle(clock)
        # Verified against when the account does not exist, so response time does not reveal it.
        self._dummy_hash = hasher.hash("not-a-real-password-1")

    def register(self, email: str, password: str) -> User:
        return self._create(email, password, Role.STUDENT)

    def bootstrap_admin(self, email: str, password: str) -> User:
        """Creates the first administrator. Called by deployment code, never exposed to users."""
        return self._create(email, password, Role.ADMIN)

    def _create(self, email: str, password: str, role: Role) -> User:
        email = self._normalise_email(email)
        self._policy.validate(password)
        user = self._repo.add(email, self._hasher.hash(password), role, self._clock())
        self._audit.record("user_registered", user_id=user.id, role=role.value)
        return user

    def authenticate(self, email: object, password: object, client_id: str = "unknown") -> str:
        key = (str(client_id), str(email).strip().lower()[:254])
        try:
            self._throttle.check(key)  # checked first, so a locked out client costs no hashing work
        except TooManyAttemptsError:
            self._audit.record("login_locked_out", client_id=str(client_id), email=key[1])
            raise
        found = None
        try:
            if isinstance(password, str):
                found = self._repo.find_by_email(self._normalise_email(email))
        except ValidationError:
            found = None
        stored = found[1] if found else self._dummy_hash
        password_ok = isinstance(password, str) and self._hasher.verify(password, stored)
        if not (found and password_ok):
            self._throttle.record_failure(key)
            self._audit.record("login_failed", client_id=str(client_id), email=key[1])
            raise AuthenticationError("Invalid email or password")
        self._throttle.reset(key)
        return self._sessions.create(found[0].id)

    def user_for_token(self, token: object) -> User:
        user = self._repo.get(self._sessions.resolve(token))
        if user is None:
            raise AuthenticationError("Invalid or expired session")
        return user

    def logout(self, token: object) -> None:
        self._sessions.revoke(token)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        found = self._repo.get_with_hash(user_id)
        if not found or not isinstance(current_password, str) \
                or not self._hasher.verify(current_password, found[1]):
            raise AuthenticationError("Invalid email or password")
        self._policy.validate(new_password)
        self._repo.update_password_hash(user_id, self._hasher.hash(new_password))
        self._sessions.revoke_all_for_user(user_id)  # old sessions may belong to an attacker
        self._audit.record("password_changed", user_id=user_id)

    def set_role(self, actor: User, user_id: int, role: Role) -> User:
        require_role(actor, Role.ADMIN)
        if not isinstance(role, Role):
            raise ValidationError("Invalid role")
        if not self._repo.update_role(user_id, role):
            raise NotFoundError("User not found")
        self._audit.record("role_changed", actor_id=actor.id, user_id=user_id, role=role.value)
        return self._repo.get(user_id)

    @staticmethod
    def _normalise_email(email: str) -> str:
        if not isinstance(email, str):
            raise ValidationError("Invalid email address")
        email = email.strip().lower()
        if not _EMAIL_RE.match(email):
            raise ValidationError("Invalid email address")
        return email
