"""Custom cache implementation with maxsize enforcement."""

import datetime
import hashlib
from collections import OrderedDict
from typing import Mapping, Sequence

from langgraph.cache.base import FullKey, Namespace, ValueT
from langgraph.cache.memory import InMemoryCache
from langgraph.checkpoint.serde.base import SerializerProtocol
from utils.logging_setup import setup_logging

from .context_manager import RouterAgentState


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


def generate_cache_key(state: RouterAgentState) -> str:
    """Generate a cache key for the given agent state.

    Args:
        state (RouterAgentState): The agent state to generate a cache key for.
        Uses `messages`, `current_results_json`, and `search_history` for cache differentiation.

    Returns:
        str: The generated cache key.
    """
    # Extract the last user message content
    messages = state.get("messages", [])
    message_content = "<empty>"
    if isinstance(messages, list) and len(messages) > 0:
        for message in reversed(messages):
            msg_type = getattr(message, "type", "")
            if msg_type in {"human", "user"}:
                message_content = str(getattr(message, "content", "") or "")
                break
            if isinstance(message, dict) and message.get("type") == "human":
                message_content = str(message.get("content", "") or "")
                break

    # Get current results and search history
    current_results_json = state.get("current_results_json", "")
    search_history = state.get("search_history", [])
    search_history_len = len(search_history) if isinstance(search_history, list) else 0

    combined_text = f"{message_content}:{current_results_json}:{search_history_len}"
    return hashlib.sha256(combined_text.encode()).hexdigest()
