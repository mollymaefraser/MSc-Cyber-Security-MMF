# ShopEase: A Layered Object Oriented Online Shopping System

## Overview

ShopEase needs to handle a growing number of users, products and transactions while staying scalable, maintainable, secure and easy to extend. This design uses a three layer architecture, presentation, business logic and data access, with each layer built from small, focused classes that follow encapsulation, inheritance and polymorphism.

The full working implementation is in Appendix A, and the accompanying test suite is in Appendix B. All 20 tests pass, including a concurrency test in which ten simultaneous buyers compete for the last unit of a product and exactly one succeeds.

## Layered Architecture

Presentation Layer (ShopController)
This is the only layer that a web framework, mobile app or command line front end would talk to. It converts raw requests into calls on the business logic layer and converts exceptions into status codes. It contains no business rules of its own, so the same controller works whether the request came from a browser, a mobile app or an internal script.

Business Logic Layer (AuthService, CatalogueService, OrderService, payment strategies, observers)
This layer holds every rule that matters to the business: password policy, stock checks, pricing, payment method selection and what happens once an order is placed. Each service has one clear responsibility, following the single responsibility principle.

Data Access Layer (Database and the Sqlite repositories)
This layer is the only place that knows SQL exists. Every other layer works with plain Python objects such as User, Product and Order, never with rows or cursors. Swapping SQLite for PostgreSQL later means rewriting this layer only.

The business logic layer depends on the data access layer through repository interfaces, never on a concrete class, so storage can change without touching the rules above it.

## Modular Design with OOP

User Management Module (AuthService, PasswordHasher, SessionStore, LoginThrottle)
Registration and login are handled entirely through AuthService, which depends on three collaborators rather than doing everything itself. PasswordHasher hashes and verifies passwords using scrypt with a random salt, so two identical passwords never produce the same stored value and a stolen database does not hand over usable credentials. SessionStore issues random, time limited tokens rather than putting user identity in anything predictable. LoginThrottle rejects further attempts once a given email and client pairing has failed five times within five minutes, which stops brute force attacks without letting one attacker lock out a legitimate user system wide, since the limit is scoped per client rather than being global.

AuthService.login also compares against a dummy password hash when the email does not exist, so a failed login takes the same amount of time whether or not that email is registered. Without this, an attacker could use response timing alone to work out which email addresses have accounts, before ever guessing a password.

Product Catalogue Module (CatalogueService, ProductRepository)
CatalogueService validates new products, for example rejecting a negative price or an empty name, before anything reaches the database. Searching is paginated with a hard maximum page size, so a request cannot ask the database to return every product at once. The search term itself is escaped against SQL wildcard characters, so a customer searching for a product that happens to contain a percent sign cannot accidentally, or deliberately, widen their own search into matching everything in the catalogue.

Order Processing Module (OrderService, PaymentRegistry, payment strategies)
OrderService prices every line against the current database price, not a price the client claims to have seen, so a tampered request cannot buy a product below its real price. Stock is reserved one product at a time using a single conditional database update per item, described further under scalability below, before any payment is attempted. If payment fails after stock has already been reserved, every reservation made so far is released again, so a failed card does not leave stock permanently locked away from other customers.

## Security Practices

Authentication uses hashed, salted passwords rather than anything reversible, verified in constant time so that comparing a wrong password does not leak information through how long the comparison took. AuthService validates the email and password it receives: an email must match a basic email shape and a password must meet a minimum length and complexity, rather than trusting whatever the presentation layer passes through.

All database queries use parameterised statements. User supplied text is never concatenated directly into SQL, which is what prevents SQL injection, as opposed to filtering for known payloads.

Payment details are never stored beyond the single call that charges them. CardPayment only accepts a card token from a payment provider, never a raw card number, so ShopEase itself never becomes a place where full card numbers are held or could later be stolen from.

## Scalability and Extensibility

Dependency Injection
Every service receives its collaborators through its constructor rather than constructing them itself. OrderService is given a ProductRepository, an OrderRepository, a PaymentRegistry and an OrderSubject, and knows nothing about SQLite, password hashing or how notifications are actually delivered. The single build_application function at the bottom of Appendix A is the only place in the whole system that wires concrete classes together. This means a unit test can give OrderService an in memory fake repository instead of a real database, which is what makes the fast, isolated tests in Appendix B possible in the first place.

Observer Pattern for Notifications
When an order is placed, OrderService does not know or care who is interested. It simply calls OrderSubject.notify with the finished order. EmailNotifier and SalesAnalytics both subscribe to this same event independently. Adding a text message notifier, or an audit log, later means writing one new class and registering it, without changing OrderService at all. One observer failing, for example if sending an email throws an exception, is caught and logged rather than being allowed to fail the customer's actual paid order.

Strategy Pattern for Payments
CardPayment and PayPalPayment both implement the same PaymentMethod interface. OrderService asks PaymentRegistry for whichever method the customer chose and calls it without knowing which concrete class it received. A new payment method, for example a bank transfer option, is added as one new class registered alongside the existing two, with no existing code edited.

Handling Concurrent Stock Updates
The most likely place for a race condition in an online shop is two customers trying to buy the last unit of the same product at once. ProductRepository.reserve_stock performs a single conditional update, reducing stock only if enough stock is still available, in one atomic database statement. There is no separate read followed by a separate write, so there is no gap in time for a second thread to slip into. The test in Appendix B confirms this directly: ten threads attempt to buy the same single remaining item simultaneously, and exactly one succeeds. A future version handling many more concurrent users could move this same pattern from SQLite to a database better suited to high write concurrency, such as PostgreSQL, without changing anything above the data access layer.

## Database Design (Data Access Layer)

Four tables cover the whole system. users holds one row per account with a unique constraint on email, so a duplicate registration is rejected by the database itself, not only by application logic. products holds stock and price as whole numbers, price in pence rather than pounds, so no calculation in the system is ever affected by floating point rounding error. orders and order_items are split apart because one order can contain many items, so an order with several products does not need to repeat the order level details such as the total price on every single line.

Every foreign key, for example an order's user_id, is enforced by the database, and every value that must never be negative, such as stock or a price, is enforced with a check constraint at the schema level. This means an invalid state is rejected even if some future piece of code bypasses the service layer and writes to the database directly, which is a second line of defence behind the validation already done in CatalogueService and OrderService.

## Known Limitations

If placing an order succeeds in taking payment but then fails to save the order record afterwards, for example due to a sudden database failure, the customer has been charged without a stored order. A production system would need either a refund step in that failure path or a more advanced pattern such as an outbox table, so that payment and order creation are never left inconsistent with each other.

## Conclusion

ShopEase meets its five requirements through a few consistent decisions. Scalability and safe concurrent stock handling both come from one atomic database update per reservation. Modularity comes from giving each class one job and connecting classes only through interfaces. Security comes from hashing, parameterised queries and constant time comparison, applied consistently across the user management module rather than bolted onto one function. Extensibility comes from the Strategy and Observer patterns, which both allow new behaviour, a new payment method or a new kind of notification, to be added as a new class rather than as a change to existing, already tested code.


## Appendix A: Implementation (shopease.py)

```python
"""
ShopEase reference implementation: a layered, object-oriented online shopping system.

Layers (top to bottom):
    Presentation    ShopController
    Business logic  AuthService, CatalogueService, OrderService, payment strategies, observers
    Data access     Database and the Sqlite repositories
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterator, Optional

log = logging.getLogger("shopease")


# ======================================================================
# Errors shared by every layer
# ======================================================================
class ShopEaseError(Exception):
    pass


class ValidationError(ShopEaseError):
    pass


class DuplicateEmailError(ValidationError):
    pass


class AuthenticationError(ShopEaseError):
    pass


class TooManyAttemptsError(AuthenticationError):
    pass


class NotFoundError(ShopEaseError):
    pass


class OutOfStockError(ShopEaseError):
    pass


class PaymentError(ShopEaseError):
    pass


# ======================================================================
# Domain model (money is held as whole pence to avoid floating point error)
# ======================================================================
@dataclass(frozen=True)
class User:
    id: int
    email: str
    password_hash: str


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    description: str
    price_pence: int
    stock: int


@dataclass(frozen=True)
class OrderLine:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class OrderItem:
    product_id: int
    quantity: int
    unit_price_pence: int


@dataclass(frozen=True)
class Order:
    id: int
    user_id: int
    items: tuple
    total_pence: int
    status: str
    payment_reference: str


# ======================================================================
# DATA ACCESS LAYER
# ======================================================================
class Database:
    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at    TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        price_pence INTEGER NOT NULL CHECK (price_pence >= 0),
        stock       INTEGER NOT NULL CHECK (stock >= 0)
    );
    CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
    CREATE TABLE IF NOT EXISTS orders (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id           INTEGER NOT NULL REFERENCES users(id),
        total_pence       INTEGER NOT NULL CHECK (total_pence >= 0),
        status            TEXT NOT NULL,
        payment_reference TEXT NOT NULL,
        created_at        TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
    CREATE TABLE IF NOT EXISTS order_items (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id         INTEGER NOT NULL REFERENCES orders(id),
        product_id       INTEGER NOT NULL REFERENCES products(id),
        quantity         INTEGER NOT NULL CHECK (quantity > 0),
        unit_price_pence INTEGER NOT NULL CHECK (unit_price_pence >= 0)
    );
    CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);
    """

    def __init__(self, path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(self._SCHEMA)
        self._lock = threading.RLock()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserRepository(ABC):
    @abstractmethod
    def add(self, email: str, password_hash: str) -> User: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]: ...


class ProductRepository(ABC):
    @abstractmethod
    def add(self, name: str, description: str, price_pence: int, stock: int) -> Product: ...

    @abstractmethod
    def get(self, product_id: int) -> Optional[Product]: ...

    @abstractmethod
    def search(self, term: str, limit: int, offset: int) -> list: ...

    @abstractmethod
    def reserve_stock(self, product_id: int, quantity: int) -> bool: ...

    @abstractmethod
    def release_stock(self, product_id: int, quantity: int) -> None: ...


class OrderRepository(ABC):
    @abstractmethod
    def add(self, user_id: int, items: list, total_pence: int, payment_reference: str) -> Order: ...

    @abstractmethod
    def list_for_user(self, user_id: int) -> list: ...


class SqliteUserRepository(UserRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, email: str, password_hash: str) -> User:
        try:
            with self._db.transaction() as conn:
                cur = conn.execute(
                    "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                    (email, password_hash, _now()),
                )
        except sqlite3.IntegrityError:
            raise DuplicateEmailError("An account with that email already exists") from None
        return User(cur.lastrowid, email, password_hash)

    def _row(self, row) -> Optional[User]:
        return User(row["id"], row["email"], row["password_hash"]) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        with self._db.transaction() as conn:
            return self._row(conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone())

    def get_by_id(self, user_id: int) -> Optional[User]:
        with self._db.transaction() as conn:
            return self._row(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


class SqliteProductRepository(ProductRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _row(row) -> Product:
        return Product(row["id"], row["name"], row["description"], row["price_pence"], row["stock"])

    def add(self, name: str, description: str, price_pence: int, stock: int) -> Product:
        with self._db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO products (name, description, price_pence, stock) VALUES (?, ?, ?, ?)",
                (name, description, price_pence, stock),
            )
        return Product(cur.lastrowid, name, description, price_pence, stock)

    def get(self, product_id: int) -> Optional[Product]:
        with self._db.transaction() as conn:
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return self._row(row) if row else None

    def search(self, term: str, limit: int, offset: int) -> list:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._db.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE name LIKE ? ESCAPE '\\' ORDER BY name LIMIT ? OFFSET ?",
                (f"%{escaped}%", limit, offset),
            ).fetchall()
        return [self._row(r) for r in rows]

    def reserve_stock(self, product_id: int, quantity: int) -> bool:
        with self._db.transaction() as conn:
            cur = conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (quantity, product_id, quantity),
            )
        return cur.rowcount == 1

    def release_stock(self, product_id: int, quantity: int) -> None:
        with self._db.transaction() as conn:
            conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity, product_id))


class SqliteOrderRepository(OrderRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, user_id: int, items: list, total_pence: int, payment_reference: str) -> Order:
        with self._db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO orders (user_id, total_pence, status, payment_reference, created_at) "
                "VALUES (?, ?, 'PAID', ?, ?)",
                (user_id, total_pence, payment_reference, _now()),
            )
            order_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price_pence) "
                "VALUES (?, ?, ?, ?)",
                [(order_id, i.product_id, i.quantity, i.unit_price_pence) for i in items],
            )
        return Order(order_id, user_id, tuple(items), total_pence, "PAID", payment_reference)

    def list_for_user(self, user_id: int) -> list:
        with self._db.transaction() as conn:
            orders = conn.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id", (user_id,)
            ).fetchall()
            result = []
            for o in orders:
                items = conn.execute(
                    "SELECT product_id, quantity, unit_price_pence FROM order_items WHERE order_id = ?",
                    (o["id"],),
                ).fetchall()
                result.append(
                    Order(
                        o["id"], o["user_id"],
                        tuple(OrderItem(i["product_id"], i["quantity"], i["unit_price_pence"]) for i in items),
                        o["total_pence"], o["status"], o["payment_reference"],
                    )
                )
        return result


# ======================================================================
# BUSINESS LOGIC LAYER: user management and security
# ======================================================================
class PasswordHasher:
    _N, _R, _P = 2 ** 14, 8, 1

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode(), salt=salt, n=self._N, r=self._R, p=self._P)
        return f"scrypt${salt.hex()}${digest.hex()}"

    def verify(self, password: str, stored: str) -> bool:
        try:
            _, salt_hex, digest_hex = stored.split("$")
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.scrypt(
                password.encode(), salt=bytes.fromhex(salt_hex), n=self._N, r=self._R, p=self._P
            )
        except ValueError:
            return False
        return hmac.compare_digest(actual, expected)


class SessionStore:
    def __init__(self, clock: Callable[[], float], ttl_seconds: int = 1800) -> None:
        self._clock, self._ttl = clock, ttl_seconds
        self._sessions: dict = {}
        self._lock = threading.Lock()

    def create(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = (user_id, self._clock() + self._ttl)
        return token

    def get(self, token: str) -> Optional[int]:
        with self._lock:
            entry = self._sessions.get(token)
            if entry is None:
                return None
            user_id, expires = entry
            if self._clock() >= expires:
                del self._sessions[token]
                return None
            return user_id

    def revoke(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)


class LoginThrottle:
    def __init__(self, clock: Callable[[], float], max_failures: int = 5, window_seconds: int = 300) -> None:
        self._clock, self._max, self._window = clock, max_failures, window_seconds
        self._failures: dict = {}
        self._lock = threading.Lock()

    def _recent(self, key) -> list:
        cutoff = self._clock() - self._window
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        self._failures[key] = recent
        return recent

    def check(self, key) -> None:
        with self._lock:
            if len(self._recent(key)) >= self._max:
                raise TooManyAttemptsError("Too many failed attempts. Please try again later.")

    def record_failure(self, key) -> None:
        with self._lock:
            self._recent(key).append(self._clock())

    def reset(self, key) -> None:
        with self._lock:
            self._failures.pop(key, None)


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    def __init__(self, users: UserRepository, hasher: PasswordHasher,
                 sessions: SessionStore, throttle: LoginThrottle) -> None:
        self._users, self._hasher, self._sessions, self._throttle = users, hasher, sessions, throttle
        self._dummy_hash = hasher.hash("timing-equaliser-password")

    @staticmethod
    def _normalise(email: str) -> str:
        if not isinstance(email, str) or not _EMAIL.match(email.strip()) or len(email) > 254:
            raise ValidationError("A valid email address is required")
        return email.strip().lower()

    @staticmethod
    def _check_password_policy(password: str) -> None:
        if not isinstance(password, str) or len(password) < 10 or len(password) > 128:
            raise ValidationError("Password must be between 10 and 128 characters")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one letter and one digit")

    def register(self, email: str, password: str) -> User:
        email = self._normalise(email)
        self._check_password_policy(password)
        return self._users.add(email, self._hasher.hash(password))

    def login(self, email: str, password: str, client_id: str) -> str:
        try:
            email = self._normalise(email)
        except ValidationError:
            raise AuthenticationError("Invalid email or password") from None
        key = (email, client_id)
        self._throttle.check(key)
        user = self._users.get_by_email(email)
        stored = user.password_hash if user else self._dummy_hash
        password_ok = self._hasher.verify(password if isinstance(password, str) else "", stored)
        if user is None or not password_ok:
            self._throttle.record_failure(key)
            raise AuthenticationError("Invalid email or password")
        self._throttle.reset(key)
        return self._sessions.create(user.id)

    def user_for_token(self, token: str) -> User:
        user_id = self._sessions.get(token) if isinstance(token, str) else None
        user = self._users.get_by_id(user_id) if user_id is not None else None
        if user is None:
            raise AuthenticationError("Please log in again")
        return user

    def logout(self, token: str) -> None:
        self._sessions.revoke(token)


# ======================================================================
# BUSINESS LOGIC LAYER: product catalogue
# ======================================================================
class CatalogueService:
    MAX_PAGE_SIZE = 50

    def __init__(self, products: ProductRepository) -> None:
        self._products = products

    def add_product(self, name: str, description: str, price_pence: int, stock: int) -> Product:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("A product needs a name")
        if not isinstance(price_pence, int) or price_pence < 0:
            raise ValidationError("Price must be a non-negative whole number of pence")
        if not isinstance(stock, int) or stock < 0:
            raise ValidationError("Stock must be a non-negative whole number")
        return self._products.add(name.strip(), description or "", price_pence, stock)

    def search(self, term: str, page: int = 1, page_size: int = 20) -> list:
        page = max(1, int(page))
        page_size = min(max(1, int(page_size)), self.MAX_PAGE_SIZE)
        return self._products.search(term or "", page_size, (page - 1) * page_size)


# ======================================================================
# BUSINESS LOGIC LAYER: payments (Strategy pattern)
# ======================================================================
class PaymentMethod(ABC):
    name: str

    @abstractmethod
    def charge(self, amount_pence: int, details: dict) -> str: ...


class CardPayment(PaymentMethod):
    name = "card"

    def charge(self, amount_pence: int, details: dict) -> str:
        if not isinstance(details.get("card_token"), str) or not details["card_token"]:
            raise PaymentError("A card token is required")
        return "CARD-" + secrets.token_hex(6)


class PayPalPayment(PaymentMethod):
    name = "paypal"

    def charge(self, amount_pence: int, details: dict) -> str:
        if not isinstance(details.get("paypal_order_id"), str) or not details["paypal_order_id"]:
            raise PaymentError("A PayPal order id is required")
        return "PAYPAL-" + secrets.token_hex(6)


class PaymentRegistry:
    def __init__(self) -> None:
        self._methods: dict = {}

    def register(self, method: PaymentMethod) -> None:
        self._methods[method.name] = method

    def get(self, name: str) -> PaymentMethod:
        try:
            return self._methods[name]
        except (KeyError, TypeError):
            raise ValidationError("Unsupported payment method") from None


# ======================================================================
# BUSINESS LOGIC LAYER: notifications (Observer pattern)
# ======================================================================
@dataclass(frozen=True)
class OrderPlaced:
    order: Order
    user_email: str


class OrderObserver(ABC):
    @abstractmethod
    def update(self, event: OrderPlaced) -> None: ...


class OrderSubject:
    def __init__(self) -> None:
        self._observers: list = []

    def attach(self, observer: OrderObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: OrderObserver) -> None:
        self._observers.remove(observer)

    def notify(self, event: OrderPlaced) -> None:
        for observer in list(self._observers):
            try:
                observer.update(event)
            except Exception:
                log.exception("Observer %s failed", type(observer).__name__)


class EmailNotifier(OrderObserver):
    def __init__(self) -> None:
        self.outbox: list = []

    def update(self, event: OrderPlaced) -> None:
        self.outbox.append((event.user_email, f"Order {event.order.id} confirmed"))


class SalesAnalytics(OrderObserver):
    def __init__(self) -> None:
        self.orders_seen = 0
        self.revenue_pence = 0

    def update(self, event: OrderPlaced) -> None:
        self.orders_seen += 1
        self.revenue_pence += event.order.total_pence


# ======================================================================
# BUSINESS LOGIC LAYER: order processing
# ======================================================================
class OrderService:
    def __init__(self, products: ProductRepository, orders: OrderRepository,
                 payments: PaymentRegistry, subject: OrderSubject) -> None:
        self._products, self._orders = products, orders
        self._payments, self._subject = payments, subject

    def place_order(self, user: User, lines: list, payment_method: str, payment_details: dict) -> Order:
        if not lines:
            raise ValidationError("An order needs at least one item")
        wanted: dict = {}
        for line in lines:
            if line.quantity <= 0:
                raise ValidationError("Quantities must be positive")
            wanted[line.product_id] = wanted.get(line.product_id, 0) + line.quantity

        method = self._payments.get(payment_method)
        priced, total = [], 0
        for product_id, quantity in wanted.items():
            product = self._products.get(product_id)
            if product is None:
                raise NotFoundError("One of the products does not exist")
            priced.append(OrderItem(product_id, quantity, product.price_pence))
            total += quantity * product.price_pence

        reserved: list = []
        try:
            for item in priced:
                if not self._products.reserve_stock(item.product_id, item.quantity):
                    raise OutOfStockError("Insufficient stock for one of the products")
                reserved.append(item)
            reference = method.charge(total, payment_details)
            order = self._orders.add(user.id, priced, total, reference)
        except Exception:
            for item in reserved:
                self._products.release_stock(item.product_id, item.quantity)
            raise
        self._subject.notify(OrderPlaced(order, user.email))
        return order


# ======================================================================
# PRESENTATION LAYER
# ======================================================================
@dataclass(frozen=True)
class Response:
    status: int
    body: dict


class ShopController:
    _STATUS = (
        (TooManyAttemptsError, 429),
        (AuthenticationError, 401),
        (NotFoundError, 404),
        (OutOfStockError, 409),
        (PaymentError, 402),
        (ValidationError, 400),
    )

    def __init__(self, auth: AuthService, catalogue: CatalogueService, orders: OrderService) -> None:
        self._auth, self._catalogue, self._orders = auth, catalogue, orders

    def _run(self, success_status: int, action: Callable[[], dict]) -> Response:
        try:
            return Response(success_status, action())
        except ShopEaseError as exc:
            for error_type, status in self._STATUS:
                if isinstance(exc, error_type):
                    return Response(status, {"error": str(exc)})
            return Response(500, {"error": "Unexpected error"})

    def register(self, email: str, password: str) -> Response:
        return self._run(201, lambda: {"user_id": self._auth.register(email, password).id})

    def login(self, email: str, password: str, client_id: str) -> Response:
        return self._run(200, lambda: {"token": self._auth.login(email, password, client_id)})

    def search(self, query: str, page: int = 1) -> Response:
        def action() -> dict:
            products = self._catalogue.search(query, page)
            return {"products": [
                {"id": p.id, "name": p.name, "price_pence": p.price_pence, "in_stock": p.stock > 0}
                for p in products
            ]}
        return self._run(200, action)

    def checkout(self, token: str, lines: list, payment_method: str, payment_details: dict) -> Response:
        def action() -> dict:
            user = self._auth.user_for_token(token)
            try:
                parsed = [OrderLine(int(l["product_id"]), int(l["quantity"])) for l in lines]
            except (KeyError, TypeError, ValueError):
                raise ValidationError("Each line needs a product_id and a quantity") from None
            order = self._orders.place_order(user, parsed, payment_method, payment_details or {})
            return {"order_id": order.id, "total_pence": order.total_pence,
                    "payment_reference": order.payment_reference}
        return self._run(201, action)


# ======================================================================
# Composition root
# ======================================================================
@dataclass
class Application:
    database: Database
    auth: AuthService
    catalogue: CatalogueService
    orders: OrderService
    payments: PaymentRegistry
    order_subject: OrderSubject
    email_notifier: EmailNotifier
    analytics: SalesAnalytics
    controller: ShopController


def build_application(db_path: str = ":memory:", clock: Callable[[], float] = time.time) -> Application:
    database = Database(db_path)
    users = SqliteUserRepository(database)
    products = SqliteProductRepository(database)
    orders = SqliteOrderRepository(database)

    auth = AuthService(users, PasswordHasher(), SessionStore(clock), LoginThrottle(clock))
    catalogue = CatalogueService(products)

    payments = PaymentRegistry()
    payments.register(CardPayment())
    payments.register(PayPalPayment())

    subject = OrderSubject()
    notifier, analytics = EmailNotifier(), SalesAnalytics()
    subject.attach(notifier)
    subject.attach(analytics)

    order_service = OrderService(products, orders, payments, subject)
    controller = ShopController(auth, catalogue, order_service)
    return Application(database, auth, catalogue, order_service, payments, subject,
                       notifier, analytics, controller)
```

## Appendix B: Test Suite (test_shopease.py)

```python
import threading
import unittest

from shopease import (
    AuthenticationError, DuplicateEmailError, NotFoundError, OrderLine, OrderObserver,
    OutOfStockError, PaymentError, TooManyAttemptsError, ValidationError, build_application,
)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.app = build_application(clock=self.clock)

    def test_register_and_login(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        token = self.app.auth.login("student@example.com", "correcthorse1", "client-a")
        user = self.app.auth.user_for_token(token)
        self.assertEqual(user.email, "student@example.com")

    def test_password_never_stored_in_plain_text(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        with self.app.database.transaction() as conn:
            raw = conn.execute("SELECT password_hash FROM users WHERE email = ?",
                                ("student@example.com",)).fetchone()["password_hash"]
        self.assertNotEqual(raw, "correcthorse1")
        self.assertTrue(raw.startswith("scrypt$"))

    def test_duplicate_email_rejected(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        with self.assertRaises(DuplicateEmailError):
            self.app.auth.register("student@example.com", "anotherpass1")

    def test_weak_password_rejected(self):
        with self.assertRaises(ValidationError):
            self.app.auth.register("weak@example.com", "short1")

    def test_wrong_password_rejected(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        with self.assertRaises(AuthenticationError):
            self.app.auth.login("student@example.com", "wrongpassword1", "client-a")

    def test_rate_limiting_locks_out_after_repeated_failures(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        for _ in range(5):
            with self.assertRaises(AuthenticationError):
                self.app.auth.login("student@example.com", "wrongpassword1", "client-a")
        with self.assertRaises(TooManyAttemptsError):
            self.app.auth.login("student@example.com", "correcthorse1", "client-a")

    def test_rate_limiting_is_scoped_per_client_not_globally(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        for _ in range(5):
            with self.assertRaises(AuthenticationError):
                self.app.auth.login("student@example.com", "wrongpassword1", "client-a")
        # a different client id is not locked out by client-a's failures
        token = self.app.auth.login("student@example.com", "correcthorse1", "client-b")
        self.assertIsInstance(token, str)

    def test_expired_session_is_rejected(self):
        self.app.auth.register("student@example.com", "correcthorse1")
        token = self.app.auth.login("student@example.com", "correcthorse1", "client-a")
        self.clock.now += 3600
        with self.assertRaises(AuthenticationError):
            self.app.auth.user_for_token(token)


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.app = build_application()

    def test_add_and_search_product(self):
        self.app.catalogue.add_product("USB-C Cable", "1 metre braided cable", 799, 50)
        results = self.app.catalogue.search("usb")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "USB-C Cable")

    def test_search_is_not_vulnerable_to_wildcard_injection(self):
        self.app.catalogue.add_product("Widget", "desc", 100, 1)
        self.app.catalogue.add_product("Gadget", "desc", 200, 1)
        # a literal underscore/percent in the search term must not act as a SQL wildcard
        results = self.app.catalogue.search("%")
        self.assertEqual(len(results), 0)

    def test_negative_price_rejected(self):
        with self.assertRaises(ValidationError):
            self.app.catalogue.add_product("Bad", "desc", -1, 1)


class OrderConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.app = build_application()
        self.app.auth.register("student@example.com", "correcthorse1")
        self.token = self.app.auth.login("student@example.com", "correcthorse1", "client-a")
        self.user = self.app.auth.user_for_token(self.token)
        self.product = self.app.catalogue.add_product("Limited Edition Mug", "desc", 1500, 1)

    def test_two_concurrent_buyers_cannot_both_get_the_last_item(self):
        results = []

        def buy():
            try:
                order = self.app.orders.place_order(
                    self.user,
                    [OrderLine(self.product.id, 1)],
                    "card", {"card_token": "tok_123"},
                )
                results.append(("ok", order))
            except OutOfStockError as exc:
                results.append(("out_of_stock", exc))

        threads = [threading.Thread(target=buy) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r[0] == "ok"]
        self.assertEqual(len(successes), 1)
        remaining = self.app.catalogue._products.get(self.product.id)
        self.assertEqual(remaining.stock, 0)

    def test_failed_payment_releases_reserved_stock(self):
        product = self.app.catalogue.add_product("Faulty Payment Item", "desc", 500, 3)
        with self.assertRaises(PaymentError):
            self.app.orders.place_order(self.user, [OrderLine(product.id, 1)], "card", {})
        remaining = self.app.catalogue._products.get(product.id)
        self.assertEqual(remaining.stock, 3)

    def test_unknown_product_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.app.orders.place_order(self.user, [OrderLine(99999, 1)], "card", {"card_token": "t"})


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.app = build_application()
        self.app.auth.register("student@example.com", "correcthorse1")
        self.token = self.app.auth.login("student@example.com", "correcthorse1", "client-a")
        self.user = self.app.auth.user_for_token(self.token)

    def test_email_and_analytics_observers_both_fire(self):
        product = self.app.catalogue.add_product("Notebook", "desc", 300, 10)
        self.app.orders.place_order(self.user, [OrderLine(product.id, 2)], "card", {"card_token": "t"})
        self.assertEqual(len(self.app.email_notifier.outbox), 1)
        self.assertEqual(self.app.analytics.orders_seen, 1)
        self.assertEqual(self.app.analytics.revenue_pence, 600)

    def test_new_observer_can_be_added_without_changing_order_service(self):
        seen = []

        class AuditLog(OrderObserver):
            def update(self, event):
                seen.append(event.order.id)

        self.app.order_subject.attach(AuditLog())
        product = self.app.catalogue.add_product("Pen", "desc", 150, 5)
        self.app.orders.place_order(self.user, [OrderLine(product.id, 1)], "card", {"card_token": "t"})
        self.assertEqual(len(seen), 1)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.app = build_application()

    def test_register_returns_201(self):
        response = self.app.controller.register("student@example.com", "correcthorse1")
        self.assertEqual(response.status, 201)

    def test_register_weak_password_returns_400(self):
        response = self.app.controller.register("student@example.com", "short")
        self.assertEqual(response.status, 400)

    def test_checkout_without_login_returns_401(self):
        response = self.app.controller.checkout("not-a-real-token", [], "card", {})
        self.assertEqual(response.status, 401)

    def test_full_purchase_flow_through_controller(self):
        self.app.controller.register("student@example.com", "correcthorse1")
        login = self.app.controller.login("student@example.com", "correcthorse1", "client-a")
        token = login.body["token"]
        product = self.app.catalogue.add_product("Keyboard", "desc", 4500, 5)
        checkout = self.app.controller.checkout(
            token, [{"product_id": product.id, "quantity": 1}], "card", {"card_token": "tok_1"}
        )
        self.assertEqual(checkout.status, 201)
        self.assertEqual(checkout.body["total_pence"], 4500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

## Appendix C: Test Run

```
....................
----------------------------------------------------------------------
Ran 20 tests in 2.505s

OK
```