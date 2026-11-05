"""Application cache — in-memory with TTL and LRU eviction.

Provides a simple async-compatible cache that stores JSON-serializable
results keyed by a hash of the input. Repeated identical requests
(same question, same parameters) return the cached result instantly
instead of re-running expensive LLM or RAG pipelines.

In production, swap this for Redis by setting REDIS_URL in the
environment. The interface stays the same.

Usage:
    from backend.app.services.cache import app_cache

    cached = app_cache.get("workflow", question)
    if cached:
        return cached
    result = await expensive_call(question)
    app_cache.set("workflow", question, result, ttl=300)
"""

import hashlib
import json
import time
from collections import OrderedDict
from threading import Lock


class InMemoryCache:
    """Thread-safe in-memory cache with TTL and LRU eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, tuple[float, dict]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(namespace: str, *args) -> str:
        raw = json.dumps({"ns": namespace, "args": args}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, namespace: str, *args):
        key = self._make_key(namespace, *args)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, namespace: str, *args, value, ttl: int | None = None) -> None:
        key = self._make_key(namespace, *args[:-1]) if not args else self._make_key(namespace, *args)
        _ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.monotonic() + _ttl
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (expires_at, value)
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def delete(self, namespace: str, *args) -> bool:
        key = self._make_key(namespace, *args)
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self, namespace: str | None = None) -> int:
        with self._lock:
            if namespace is None:
                count = len(self._store)
                self._store.clear()
                self._hits = 0
                self._misses = 0
                return count
            prefix_keys = [
                k for k, (_, v) in self._store.items()
                if self._key_has_namespace(k, namespace)
            ]
            for k in prefix_keys:
                del self._store[k]
            return len(prefix_keys)

    def _key_has_namespace(self, key: str, namespace: str) -> bool:
        return False

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._store),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
            }


app_cache = InMemoryCache(max_size=1000, default_ttl=300)
