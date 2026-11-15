"""In-memory session store with optimistic versioning (docs/simulation/state-machine.md).

- One process, one dictionary. Sessions do not survive a restart and are not shared
  between processes or machines: run the API with a single worker.
- Every mutation names the version it expects. A mismatch is rejected (409), so two
  clients can never silently overwrite each other.
- Mutations of one session are serialised by a per-session lock. The new state is
  computed from the old one by pure functions and swapped in only on success, so a
  failed event leaves the stored session untouched.
- Idle sessions expire after `ttl_seconds`; the oldest idle session is evicted when
  `max_sessions` is reached.
"""

from __future__ import annotations

import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from aidos.simulation.session import InvariantBreachError, SessionState

T = TypeVar("T")


class SessionNotFoundError(LookupError):
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(
            f"No simulation session '{session_id}'. It may have expired or the engine restarted."
        )


class VersionConflictError(Exception):
    def __init__(self, expected: int, current: int):
        self.expected, self.current = expected, current
        super().__init__(
            f"The session changed since you loaded it (you sent version {expected}, it is now "
            f"{current}). Reload and try again."
        )


@dataclass
class _Entry:
    session: SessionState
    lock: threading.Lock
    touched: float


class SessionStore:
    def __init__(
        self,
        ttl_seconds: float = 2 * 60 * 60,
        max_sessions: int = 200,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._entries: dict[str, _Entry] = {}
        self._guard = threading.Lock()
        self._ttl, self._max, self._clock = ttl_seconds, max_sessions, clock

    @staticmethod
    def new_id() -> str:
        return f"sim-{secrets.token_hex(6)}"

    def _expire(self) -> None:
        now = self._clock()
        for sid in [s for s, e in self._entries.items() if now - e.touched > self._ttl]:
            del self._entries[sid]

    def add(self, session: SessionState) -> SessionState:
        with self._guard:
            self._expire()
            while len(self._entries) >= self._max:
                oldest = min(self._entries, key=lambda s: self._entries[s].touched)
                del self._entries[oldest]
            self._entries[session.session_id] = _Entry(session, threading.Lock(), self._clock())
        return session

    def _entry(self, session_id: str) -> _Entry:
        with self._guard:
            self._expire()
            entry = self._entries.get(session_id)
            if entry is None:
                raise SessionNotFoundError(session_id)
            entry.touched = self._clock()
            return entry

    def get(self, session_id: str) -> SessionState:
        return self._entry(session_id).session

    def mutate(
        self,
        session_id: str,
        expected_version: int,
        change: Callable[[SessionState], SessionState],
    ) -> SessionState:
        """Apply `change` atomically if the stored version is `expected_version`."""
        entry = self._entry(session_id)
        with entry.lock:
            current = entry.session
            if current.version != expected_version:
                raise VersionConflictError(expected_version, current.version)
            try:
                updated = change(current)
            except InvariantBreachError as breach:
                self._commit(session_id, entry, breach.session)  # record ERROR, not the event
                raise
            return self._commit(session_id, entry, updated)

    def _commit(self, session_id: str, entry: _Entry, session: SessionState) -> SessionState:
        """Store the new state, unless the session expired or was evicted meanwhile."""
        with self._guard:
            if self._entries.get(session_id) is not entry:
                raise SessionNotFoundError(session_id)
            entry.session = session
            entry.touched = self._clock()
        return session

    def __len__(self) -> int:
        with self._guard:
            self._expire()
            return len(self._entries)
