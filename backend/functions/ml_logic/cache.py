"""Custom cache implementation with maxsize enforcement."""

import datetime
import hashlib
from collections import OrderedDict
from typing import Mapping, Sequence

from langgraph.cache.base import FullKey, Namespace, ValueT
from langgraph.cache.memory import InMemoryCache
from langgraph.checkpoint.serde.base import SerializerProtocol
from utils.logging_setup import setup_logging

from .states import ChatbotState

logger = setup_logging()


class InMemoryCacheWithMaxsize(InMemoryCache):
    """Included maxsize enforcement for cache for backwards compatibility."""

    def __init__(self, *, serde: SerializerProtocol | None = None, maxsize: int = 1000):
        super().__init__(serde=serde)
        self.maxsize = maxsize
        self._cache: dict[Namespace, OrderedDict[str, tuple[str, bytes, float | None]]] = {}

    def get(self, keys: Sequence[FullKey]) -> dict[FullKey, ValueT]:
        """Get the cached values for the given keys."""
        with self._lock:
            if not keys:
                return {}
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            values: dict[FullKey, ValueT] = {}
            for ns_tuple, key in keys:
                ns = Namespace(ns_tuple)
                if ns in self._cache and key in self._cache[ns]:
                    enc, val, expiry = self._cache[ns][key]
                    if expiry is None or now < expiry:
                        values[(ns, key)] = self.serde.loads_typed((enc, val))
                        # For backwards compatibility
                        logger.info(f"Cache hit for query combination (key: {key[:8]}...)")
                    else:
                        del self._cache[ns][key]
            return values

    def set(self, keys: Mapping[FullKey, tuple[ValueT, int | None]]) -> None:
        """Set the cached values for the given keys."""
        with self._lock:
            now = datetime.datetime.now(datetime.timezone.utc)
            for (ns, key), (value, ttl) in keys.items():
                if ttl is not None:
                    delta = datetime.timedelta(seconds=ttl)
                    expiry: float | None = (now + delta).timestamp()
                else:
                    expiry = None
                if ns not in self._cache:
                    self._cache[ns] = OrderedDict()
                self._cache[ns][key] = (
                    *self.serde.dumps_typed(value),
                    expiry,
                )
                self._enforce_namespace_maxsize(ns)

    def _enforce_namespace_maxsize(self, ns: Namespace):
        """Enforce maxsize for a specific namespace using LRU"""
        if len(self._cache[ns]) > self.maxsize:
            # Remove oldest items until under maxsize
            while len(self._cache[ns]) > self.maxsize:
                self._cache[ns].popitem(last=False)


def generate_cache_key(state: ChatbotState) -> str:
    """Generate a cache key for the given chatbot state.

    Args:
        state (ChatbotState): The chatbot state to generate a cache key for.
        Requires `top_schemes_text`, `query_text`, and the last user message in `messages`.

    Returns:
        str: The generated cache key.
    """
    query_text = state["query_text"]
    input_text = state["top_schemes_text"]
    if isinstance(state["messages"], list):
        if len(state["messages"]) > 0:
            message_content = state["messages"][-1].content
        else:
            message_content = "<empty>"
    else:
        message_content = state["messages"].content if state["messages"] else ""
    combined_text = f"{query_text}:{input_text}:{message_content}"
    return hashlib.sha256(combined_text.encode()).hexdigest()
