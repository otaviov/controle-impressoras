from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable

log = logging.getLogger(__name__)

_MISSING: Any = object()


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any, float]] = {}

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is not None:
            ts, value, ttl = entry
            if time.monotonic() - ts < ttl:
                return value
            del self._store[key]
        return _MISSING

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._store[key] = (time.monotonic(), value, ttl)

    def invalidate_prefix(self, prefix: str) -> None:
        pfx = prefix + ":"
        to_remove = [k for k in self._store if k.startswith(pfx)]
        for k in to_remove:
            del self._store[k]

    def clear(self) -> None:
        self._store.clear()


_global_cache = TTLCache()


def invalidate(namespace: str) -> None:
    _global_cache.invalidate_prefix(namespace)


def invalidate_all() -> None:
    _global_cache.clear()


def cached(ttl: int = 30, namespace: str = "") -> Callable[..., Any]:
    def decorator(fn: Callable[..., Any]) -> Any:
        ns = namespace or fn.__name__

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts: list[str] = [ns, fn.__name__]
            for a in args[1:]:
                key_parts.append(repr(a))
            for k in sorted(kwargs):
                key_parts.append(f"{k}={kwargs[k]!r}")
            cache_key = ":".join(key_parts)
            result = _global_cache.get(cache_key)
            if result is not _MISSING:
                return result
            result = fn(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl=ttl)
            return result

        def _invalidate() -> None:
            invalidate(ns)

        wrapper.invalidate = _invalidate
        return wrapper

    return decorator
