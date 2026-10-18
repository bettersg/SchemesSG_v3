# Packaged embedding tokenizer

`9b5ad71b2ce5302211f9c61530b329a4922fc6a4` is the public `cl100k_base`
vocabulary used by `text-embedding-3-large`. It is tokenizer data, not scheme
data or a credential. Its filename is tiktoken's SHA-1 of the download URL.

- Source: https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken
- SHA-256: `223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`
- Size: 1,681,126 bytes
- Verified with tiktoken 0.14.0, already installed by the embedding SDK.

`EmbeddingsManager` verifies the asset and atomically seeds tiktoken's writable
cache before creating the embedding client. Existing valid caches are preserved;
`TIKTOKEN_CACHE_DIR` and `DATA_GYM_CACHE_DIR` overrides, including an empty value
that disables caching, retain their normal meaning. Other encodings can still
populate the writable cache. Direct SDK clients in maintenance scripts are
unchanged and do not automatically run this initializer.

Firebase deploys the entire `backend/functions` source directory; keep this
asset inside that directory and out of deployment ignore rules. Local Compose
mounts it with the functions source, so a Dockerfile-only download is unnecessary.

When upgrading the embedding model or SDK, verify its tokenizer mapping and
expected data hash. Download the official file into this directory with the
SDK's expected cache filename, verify its SHA-256, update the initializer's
checksum if needed, and run `tests/unit/test_embeddings_manager.py`. The offline
test uses a fresh process to avoid passing accidentally through tiktoken's
in-memory cache. Cold profiling needs a new container or isolated empty cache;
restarting the same container may preserve its cached vocabulary.
