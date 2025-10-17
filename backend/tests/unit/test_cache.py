import datetime
import hashlib
from unittest.mock import patch

import pytest
from langgraph.cache.base import Namespace
from ml_logic.cache import InMemoryCacheWithMaxsize, generate_cache_key
from ml_logic.states import ChatbotState


def test_generate_cache_key_consistency():
    """Cache key should be deterministic for the same state."""
    state = ChatbotState(
        query_text="test query", top_schemes_text="test schemes", messages=[type("Msg", (), {"content": "hello"})()]
    )
    key1 = generate_cache_key(state)
    key2 = generate_cache_key(state)

    assert key1 == key2
    assert key1 == hashlib.sha256(b"test query:test schemes:hello").hexdigest()


def test_generate_cache_key_changes_with_input():
    """Cache key should change if state changes."""
    state1 = ChatbotState(
        query_text="q1", top_schemes_text="schemes", messages=[type("Msg", (), {"content": "msg1"})()]
    )
    state2 = ChatbotState(
        query_text="q2", top_schemes_text="schemes", messages=[type("Msg", (), {"content": "msg1"})()]
    )
    assert generate_cache_key(state1) != generate_cache_key(state2)


def test_generate_cache_key_messages_empty_or_nonlist():
    # messages = empty list
    state = ChatbotState(query_text="q", top_schemes_text="s", messages=[])
    key = generate_cache_key(state)
    assert key

    # messages = single object
    msg = type("Msg", (), {"content": "hello"})()
    state2 = ChatbotState(query_text="q", top_schemes_text="s", messages=msg)
    key2 = generate_cache_key(state2)
    assert key2


def test_cache_set_and_get_respects_ttl():
    """Test that cache respects TTL (expiration) correctly."""
    cache = InMemoryCacheWithMaxsize()

    ns = Namespace("namespace")
    state = (ns, "key")

    # Fixed "now" for deterministic tests
    fixed_now = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)

    # Subclass datetime to override now()
    class FixedDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    with patch("ml_logic.cache.datetime.datetime", FixedDateTime):
        # Set cache with TTL = 10 seconds
        cache.set({state: ("value", 10)})

        # Immediately retrievable
        result = cache.get([state])
        assert state in result

        # Move time forward beyond TTL
        FixedDateTime.now = classmethod(lambda cls, tz=None: fixed_now + datetime.timedelta(seconds=11))
        result_after_expiry = cache.get([state])
        assert state not in result_after_expiry


def test_cache_maxsize_eviction():
    cache = InMemoryCacheWithMaxsize(maxsize=2)
    ns = ("namespace",)

    # Add three items; maxsize = 2 → first one should be evicted
    cache.set({(ns, "key1"): ("v1", None), (ns, "key2"): ("v2", None), (ns, "key3"): ("v3", None)})

    # Only the last 2 should remain
    remaining_keys = list(cache._cache[ns].keys())
    assert "key1" not in remaining_keys
    assert set(remaining_keys) == {"key2", "key3"}


def test_cache_get_empty_keys_and_missing_entries():
    cache = InMemoryCacheWithMaxsize()
    ns = ("ns",)
    # empty keys
    assert cache.get([]) == {}

    # namespace missing
    state = (ns, "key")
    assert cache.get([state]) == {}

    # namespace exists but key missing
    cache._cache[ns] = {}
    assert cache.get([state]) == {}


def test_cache_set_with_no_ttl():
    cache = InMemoryCacheWithMaxsize()
    state = ("ns", "key")
    cache.set({state: ("value", None)})

    ns_obj = state[0]
    assert state[1] in cache._cache[ns_obj]
    # expiry should be None
    _, _, expiry = cache._cache[ns_obj][state[1]]
    assert expiry is None
