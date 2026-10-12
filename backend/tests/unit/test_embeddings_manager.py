from integrations.embeddings_manager import (
    EMBEDDING_MAX_RETRIES,
    EMBEDDING_REQUEST_TIMEOUT_SECONDS,
    EmbeddingsConfig,
    EmbeddingsManager,
)


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
