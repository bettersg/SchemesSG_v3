import hashlib
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from integrations.embeddings_manager import (
    EMBEDDING_MAX_RETRIES,
    EMBEDDING_REQUEST_TIMEOUT_SECONDS,
    EmbeddingsConfig,
    EmbeddingsManager,
)


TOKENIZER_CACHE_KEY = "9b5ad71b2ce5302211f9c61530b329a4922fc6a4"
TOKENIZER_SHA256 = "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7"
TOKENIZER_ASSET = Path(__file__).parents[2] / "functions" / "assets" / "tiktoken" / TOKENIZER_CACHE_KEY


@pytest.fixture(autouse=True)
def isolated_tokenizer_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("DATA_GYM_CACHE_DIR", raising=False)


def initialize(mocker):
    mocker.patch("integrations.embeddings_manager.AzureOpenAIEmbeddings")
    return EmbeddingsManager(embedding_config=EmbeddingsConfig(
        endpoint="https://example.openai.azure.com",
        api_key="test-key",
        api_version="2024-12-01-preview",
        deployment_name="text-embedding-3-large",
    ))


def test_embedding_client_bounds_request_time_and_retries(mocker):
    client = mocker.patch("integrations.embeddings_manager.AzureOpenAIEmbeddings")
    config = EmbeddingsConfig(
        endpoint="https://example.openai.azure.com",
        api_key="test-key",
        api_version="2024-12-01-preview",
        deployment_name="text-embedding-3-large",
    )

    EmbeddingsManager(embedding_config=config)

    client.assert_called_once_with(
        azure_endpoint=config.endpoint,
        api_key=config.api_key,
        api_version=config.api_version,
        model=config.deployment_name,
        dimensions=config.dimensions,
        request_timeout=EMBEDDING_REQUEST_TIMEOUT_SECONDS,
        max_retries=EMBEDDING_MAX_RETRIES,
    )


def test_packaged_tokenizer_seeds_empty_cache(mocker):
    initialize(mocker)
    cached = Path(os.environ["TIKTOKEN_CACHE_DIR"]) / TOKENIZER_CACHE_KEY
    assert hashlib.sha256(cached.read_bytes()).hexdigest() == TOKENIZER_SHA256


def test_cached_tokenizer_works_offline_in_fresh_process():
    script = """
from unittest.mock import patch
from integrations.embeddings_manager import EmbeddingsConfig, EmbeddingsManager
with patch('integrations.embeddings_manager.AzureOpenAIEmbeddings'):
    EmbeddingsManager(embedding_config=EmbeddingsConfig(
        endpoint='https://example.openai.azure.com', api_key='test-key',
        api_version='2024-12-01-preview', deployment_name='text-embedding-3-large'))
import tiktoken.load
def reject_download(*args, **kwargs):
    raise AssertionError('Tokenizer attempted a network download')
tiktoken.load.read_file = reject_download
encoding = tiktoken.encoding_for_model('text-embedding-3-large')
assert encoding.name == 'cl100k_base'
for text in ['financial assistance for families', '家庭援助', 'a ' * 10000]:
    assert encoding.decode(encoding.encode(text)) == text
"""
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[2] / "functions")}
    result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("corrupt", [False, True])
def test_cache_preserves_valid_data_and_repairs_corruption(mocker, corrupt):
    cached = Path(os.environ["TIKTOKEN_CACHE_DIR"]) / TOKENIZER_CACHE_KEY
    cached.parent.mkdir()
    cached.write_bytes(b"invalid" if corrupt else TOKENIZER_ASSET.read_bytes())
    modified = cached.stat().st_mtime_ns
    initialize(mocker)
    assert hashlib.sha256(cached.read_bytes()).hexdigest() == TOKENIZER_SHA256
    if not corrupt:
        assert cached.stat().st_mtime_ns == modified


def test_data_gym_cache_override_is_respected(mocker, monkeypatch, tmp_path):
    monkeypatch.delenv("TIKTOKEN_CACHE_DIR")
    cache = tmp_path / "custom-cache"
    monkeypatch.setenv("DATA_GYM_CACHE_DIR", str(cache))
    initialize(mocker)
    assert (cache / TOKENIZER_CACHE_KEY).read_bytes() == TOKENIZER_ASSET.read_bytes()


def test_explicitly_disabled_cache_is_respected(mocker, monkeypatch):
    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", "")
    initialize(mocker)
    assert not Path(TOKENIZER_CACHE_KEY).exists()


def test_default_cache_location_is_seeded(mocker, monkeypatch, tmp_path):
    monkeypatch.delenv("TIKTOKEN_CACHE_DIR")
    mocker.patch("integrations.embeddings_manager.gettempdir", return_value=str(tmp_path))
    initialize(mocker)
    assert (tmp_path / "data-gym-cache" / TOKENIZER_CACHE_KEY).read_bytes() == TOKENIZER_ASSET.read_bytes()


@pytest.mark.parametrize("missing", [False, True])
def test_broken_packaged_asset_fails_before_client_creation(mocker, tmp_path, missing):
    asset = tmp_path / "broken-asset"
    if not missing:
        asset.write_bytes(b"invalid")
    mocker.patch("integrations.embeddings_manager.TOKENIZER_ASSET", asset)
    client = mocker.patch("integrations.embeddings_manager.AzureOpenAIEmbeddings")
    config = EmbeddingsConfig('https://example.openai.azure.com', 'test-key', '2024-12-01-preview', 'text-embedding-3-large')
    with pytest.raises(FileNotFoundError if missing else ValueError):
        EmbeddingsManager(embedding_config=config)
    client.assert_not_called()


def test_concurrent_initialization_leaves_complete_cache(mocker):
    mocker.patch("integrations.embeddings_manager.AzureOpenAIEmbeddings")
    config = EmbeddingsConfig('https://example.openai.azure.com', 'test-key', '2024-12-01-preview', 'text-embedding-3-large')
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _: EmbeddingsManager(embedding_config=config), range(8)))
    cache = Path(os.environ["TIKTOKEN_CACHE_DIR"])
    assert [path.name for path in cache.iterdir()] == [TOKENIZER_CACHE_KEY]
    assert hashlib.sha256((cache / TOKENIZER_CACHE_KEY).read_bytes()).hexdigest() == TOKENIZER_SHA256
