"""Security audit trail. Records who did what, never secrets."""

import threading


class AuditLog:
    def __init__(self) -> None:
        self._events: list = []
        self._lock = threading.Lock()

    def record(self, event: str, **fields) -> None:
        with self._lock:
            self._events.append((event, dict(fields)))

    def events(self) -> list:
        with self._lock:
            return list(self._events)
