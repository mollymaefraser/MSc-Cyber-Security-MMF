# Collaborative Discussion: Refactoring an Insecure Authentication System

**Unit:** Formative Collaborative Discussion (starts and ends in this unit week)
**Note:** Not assessed, informal tutor feedback only.

---

## Task

You are provided with a simple User Authentication System written in Python. The code has several security vulnerabilities.

### Original Code Snippet

```python
class User:
    def __init__(self, username, password):
         self.username = username
         self.password = password


class AuthenticationSystem:
    def __init__(self):
        self.users = []

    def add_user(self, username, password):
        self.users.append(User(username, password))

    def authenticate(self, username, password):
        for user in self.users:
            if user.username == username and user.password == password:
                return True
        return False


# Usage
auth_system = AuthenticationSystem()
auth_system.add_user("admin", "admin123")  # Weak password
auth_system.add_user("user1", "password")  # Weak password

# Simulate an injection attack
malicious_input = "admin' OR '1'='1"

print(auth_system.authenticate(malicious_input, "anything"))
# Output: True (Vulnerable to SQL injection)
```

---

## Discussion Guidelines

- Submit an initial post to the opening discussion tasks.
- Limit all posts to 300 words maximum, to encourage exchange of ideas.
- Contribute at least two follow-up posts engaging with peers.
- Discuss with peers the best refactoring approach and finalise a clean, maintainable version of the code.

---

## 1. Vulnerabilities Identified

- **Plaintext password storage:** `User.password` stores the raw password. A database breach exposes every credential directly, and since people reuse passwords, this often compromises accounts on unrelated systems too.
- **Injection-style logic flaw:** `authenticate()` does a direct string comparison, so it isn't technically SQL-injectable as written (there's no query being built), but it illustrates the *pattern* that causes real SQL injection: if this logic were backed by a database using string-concatenated queries like `f"SELECT * FROM users WHERE username='{username}'"`, the same `admin' OR '1'='1` payload would genuinely bypass authentication. The lesson is the same either way: never trust raw input in an auth check.
- **Weak password policy:** `"admin123"` and `"password"` are accepted with no minimum complexity, length, or common-password checks.
- **No input validation:** empty strings, oversized input, or malformed payloads are accepted without sanitisation.
- **No rate limiting:** `authenticate()` can be called unlimited times, making brute-force and credential-stuffing attacks trivial.

---

## 2. Refactored Code

```python
import re
import time
import bcrypt  # pip install bcrypt


class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash  # never store plaintext


class AuthenticationSystem:
    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 60

    def __init__(self):
        self.users = {}
        self.failed_attempts = {}  # username -> (count, first_attempt_time)

    def _validate_input(self, username, password):
        if not username or not password:
            raise ValueError("Username and password cannot be empty")
        if not re.match(r'^[A-Za-z0-9_]{3,30}$', username):
            raise ValueError("Invalid username format")

    def _enforce_password_policy(self, password):
        if len(password) < 10:
            raise ValueError("Password must be at least 10 characters")
        if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password):
            raise ValueError("Password must contain upper and lower case letters")
        if not re.search(r'\d', password):
            raise ValueError("Password must contain a number")
        common_passwords = {"password", "admin123", "12345678"}
        if password.lower() in common_passwords:
            raise ValueError("Password is too common")

    def add_user(self, username, password):
        self._validate_input(username, password)
        self._enforce_password_policy(password)
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users[username] = User(username, hashed)

    def authenticate(self, username, password):
        self._validate_input(username, password)

        # Rate limiting
        count, first_time = self.failed_attempts.get(username, (0, 0))
        if count >= self.MAX_ATTEMPTS and time.time() - first_time < self.LOCKOUT_SECONDS:
            raise PermissionError("Too many failed attempts. Try again later.")

        user = self.users.get(username)
        if user and bcrypt.checkpw(password.encode(), user.password_hash):
            self.failed_attempts.pop(username, None)
            return True

        # Track failed attempt
        if count == 0 or time.time() - first_time >= self.LOCKOUT_SECONDS:
            self.failed_attempts[username] = (1, time.time())
        else:
            self.failed_attempts[username] = (count + 1, first_time)
        return False


# Usage
auth_system = AuthenticationSystem()
auth_system.add_user("admin", "Str0ngP@ssw0rd!")

# Injection-style payload no longer bypasses anything.
# It's just treated as an (invalid) username and rejected outright.
try:
    auth_system.authenticate("admin' OR '1'='1", "anything")
except ValueError as e:
    print(f"Rejected: {e}")

print(auth_system.authenticate("admin", "Str0ngP@ssw0rd!"))  # True
```

---

## 3. Benefits of the Refactor

- **Hashing (bcrypt):** even if the user store is stolen, passwords aren't directly usable, and bcrypt's built-in salting also defeats precomputed rainbow-table attacks.
- **Input sanitisation:** the injection-style payload is now simply rejected as an invalid username, rather than being interpreted as logic.
- **Password policy enforcement:** rejects weak passwords like `"admin123"` at creation time, reducing the attack surface from the start.
- **Rate limiting:** locks out repeated failed attempts per username, making brute-force attacks impractically slow.

