"""Per address request limits.

Abuse control rather than DDoS protection. A distributed flood arrives from
thousands of addresses, each one under the limit, and this answers every one of
them politely. `LIMITS.md` says so in those words.

The counting lives in `storage.ratelimit` and knows nothing about HTTP. What is
here is who the caller is, which header may be believed, and what a refusal
looks like on the wire.
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import sqlite3
import tempfile
import time
from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from catholic_bible.storage.ratelimit import Counter

Network = ipaddress.IPv4Network | ipaddress.IPv6Network

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

log = logging.getLogger("catholic_bible.ratelimit")

# One prune per this many counted requests on a bucket. Keyed off the count the
# store just returned rather than off a random number, so a test can reach it.
PRUNE_EVERY = 250

UNATTRIBUTABLE = "unknown"

TRUE = frozenset({"1", "true", "yes", "on"})
FALSE = frozenset({"0", "false", "no", "off"})


def trusted_set(value: str) -> frozenset[Network]:
    """Parse the trusted proxy setting, which takes addresses and ranges.

    A range matters because a compose network renumbers, so a bare address
    would need editing every time the bridge moves.
    """
    entries = [entry.strip() for entry in value.split(",") if entry.strip()]
    parsed: set[Network] = set()
    for entry in entries:
        try:
            parsed.add(ipaddress.ip_network(entry, strict=False))
        except ValueError as bad:
            raise ValueError(f"not an address or range: {entry}") from bad
    return frozenset(parsed)


def _trusted(address: str, trusted: frozenset[Network]) -> bool:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(parsed in network for network in trusted)


def resolve(
    peer: str | None, forwarded: str | None, trusted: frozenset[Network]
) -> str:
    """The address to count against.

    `X-Forwarded-For` is attacker controlled. Reading it from an untrusted peer
    hands a fresh bucket to anyone who sends a random value per request, which
    limits the honest caller and nobody else. So it is read only when the
    connection itself came from a proxy that was configured as trustworthy.

    Within the header, each hop appends, so the left end is the client's own
    claim and the right end is what the nearest proxy observed. The answer is
    the rightmost entry that is not itself a trusted hop.

    An entry that is not an address stops the walk and the peer is used. Anything
    a trusted proxy appended is a real address, so garbage on the right means
    nothing vouched for what sits to the left of it, and stepping over it to
    reach a value the client supplied is the spoofing hole coming back.
    """
    if peer is None:
        return UNATTRIBUTABLE
    if not forwarded or not _trusted(peer, trusted):
        return peer

    for entry in reversed([hop.strip() for hop in forwarded.split(",")]):
        try:
            ipaddress.ip_address(entry)
        except ValueError:
            return peer
        if not _trusted(entry, trusted):
            return entry
    return peer


def _positive(environ: Mapping[str, str], name: str, fallback: int) -> int:
    raw = environ.get(name)
    if raw is None:
        return fallback
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} cannot be negative, got {value}")
    return value


def _flag(environ: Mapping[str, str], name: str, fallback: bool) -> bool:
    raw = environ.get(name)
    if raw is None:
        return fallback
    lowered = raw.strip().lower()
    if lowered in TRUE:
        return True
    if lowered in FALSE:
        return False
    raise ValueError(f"{name} is not a yes or a no, got {raw!r}")


@dataclass(frozen=True)
class Settings:
    """Read once at startup. A typo fails there rather than at the first hit."""

    per_minute: int = 60
    per_hour: int = 1000
    enabled: bool = True
    trusted: frozenset[Network] = frozenset()
    db_path: Path = Path(tempfile.gettempdir()) / "catholic-bible-ratelimit.db"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if environ is None else environ
        default = cls()
        return cls(
            per_minute=_positive(source, "RATE_LIMIT_PER_MINUTE", default.per_minute),
            per_hour=_positive(source, "RATE_LIMIT_PER_HOUR", default.per_hour),
            enabled=_flag(source, "RATE_LIMIT_ENABLED", default.enabled),
            trusted=trusted_set(source.get("RATE_LIMIT_TRUSTED_PROXIES", "")),
            db_path=Path(source.get("RATE_LIMIT_DB", default.db_path)),
        )

    def windows(self) -> tuple[tuple[int, int], ...]:
        """The windows that are switched on, as seconds and allowance."""
        candidates = ((60, self.per_minute), (3600, self.per_hour))
        return tuple((window, limit) for window, limit in candidates if limit > 0)


@dataclass
class State:
    """What the limiter wants `/health` to be able to say about it.

    Shared rather than global, so a test builds its own and the running app has
    exactly one.
    """

    degraded: str | None = field(default=None)


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    limit: int
    remaining: int
    reset: int
    message: str = ""


class RateLimiter:
    """Per address limits, in front of everything.

    Raw ASGI rather than `BaseHTTPMiddleware`. The wrapper measured a repeatable
    330 microseconds against a counter that costs 15.5, which is the wrapper
    costing twenty times the work it wraps. `docs/qa/` carries the run.
    """

    def __init__(
        self,
        app: ASGIApp,
        settings: Settings | None = None,
        state: State | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.app = app
        self.settings = Settings.from_env() if settings is None else settings
        self.state = State() if state is None else state
        self.clock = clock
        self._counter: Counter | None = None

    def _store(self) -> Counter:
        if self._counter is None:
            self._counter = Counter(self.settings.db_path)
            self.state.degraded = None
        return self._counter

    def _fail_open(self, error: Exception) -> None:
        """Serve the request and make the reason visible.

        The posture before this middleware existed was unlimited, so serving is
        a return to it rather than a new hole. Being quiet about it is the hole,
        which is why `/health` reads this and why the log fires once.
        """
        reason = f"{self.settings.db_path}: {error}"
        if self.state.degraded != reason:
            log.error("rate limiting is off, the store is unusable. %s", reason)
        self.state.degraded = reason

    def check(self, address: str) -> Verdict | None:
        """Count this request against every window. `None` means unmeasured."""
        now = int(self.clock())
        try:
            counter = self._store()
            counted = [
                (window, limit, counter.hit(address, window, now))
                for window, limit in self.settings.windows()
            ]
            for window, _, count in counted:
                if count % PRUNE_EVERY == 0:
                    counter.prune(window, now)
        except (sqlite3.Error, OSError) as unusable:
            self._fail_open(unusable)
            return None

        spent = [
            (window, limit, count) for window, limit, count in counted if count > limit
        ]
        if spent:
            window, limit, _ = max(spent, key=lambda each: each[0])
            return Verdict(
                allowed=False,
                limit=limit,
                remaining=0,
                reset=counter.reset_in(window, now),
                message=f"{limit} requests per {window} seconds",
            )

        window, limit, count = min(
            counted, key=lambda each: each[1] - each[2], default=(60, 0, 0)
        )
        return Verdict(
            allowed=True,
            limit=limit,
            remaining=max(limit - count, 0),
            reset=counter.reset_in(window, now),
        )

    def close(self) -> None:
        if self._counter is not None:
            self._counter.close()
            self._counter = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            # Returns when the application shuts down, which is the only moment
            # this process has to hand the connection back.
            try:
                await self.app(scope, receive, send)
            finally:
                self.close()
            return

        if scope["type"] != "http" or not self.settings.enabled:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        peer = None if client is None else str(client[0])
        address = resolve(peer, _forwarded(scope), self.settings.trusted)

        if _loopback(address):
            await self.app(scope, receive, send)
            return

        verdict = self.check(address)
        if verdict is None:
            await self.app(scope, receive, send)
            return
        if not verdict.allowed:
            await _refuse(verdict, send)
            return

        await self.app(scope, receive, _with_headers(send, verdict))


def _forwarded(scope: Scope) -> str | None:
    headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
    for name, value in headers:
        if name == b"x-forwarded-for":
            return value.decode("latin-1")
    return None


def _loopback(address: str) -> bool:
    """The container health check is the service asking itself if it is alive."""
    try:
        return ipaddress.ip_address(address).is_loopback
    except ValueError:
        return False


def _headers(verdict: Verdict) -> list[tuple[bytes, bytes]]:
    return [
        (b"ratelimit-limit", str(verdict.limit).encode()),
        (b"ratelimit-remaining", str(verdict.remaining).encode()),
        (b"ratelimit-reset", str(verdict.reset).encode()),
    ]


def _with_headers(send: Send, verdict: Verdict) -> Send:
    async def wrapped(message: Message) -> None:
        if message["type"] == "http.response.start":
            message["headers"] = list(message.get("headers", [])) + _headers(verdict)
        await send(message)

    return wrapped


async def _refuse(verdict: Verdict, send: Send) -> None:
    """A 429 in the one error shape this API publishes.

    Built here rather than raised, because an ASGI middleware sits outside the
    application and its exception handlers never see what happens up here.
    """
    from catholic_bible.api.errors import Problem, Reason  # noqa: PLC0415

    problem = Problem(reason=Reason.RATE_LIMITED, message=verdict.message)
    body = json.dumps({"detail": problem.model_dump()}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"retry-after", str(verdict.reset).encode()),
                *_headers(verdict),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
