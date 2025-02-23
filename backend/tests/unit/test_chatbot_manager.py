"""Unit tests for chatbotManager.py."""

import pandas as pd
import pytest
from ml_logic.chatbotManager import clean_scraped_text, dataframe_to_text, Config, Chatbot


def test_clean_scraped_text():
    """Test the clean_scraped_text function with various inputs."""
    # Test basic cleaning
    text = "Hello's World! \n This is a test."
    cleaned = clean_scraped_text(text)
    assert "'" not in cleaned
    assert "\n" not in cleaned
    assert "!" not in cleaned

    # Test multiple spaces
    text = "Too    many    spaces"
    cleaned = clean_scraped_text(text)
    assert "    " not in cleaned
    assert cleaned == "Too many spaces"

    # Test special patterns
    text = ":''This should be removed\n: ''This too\n!And this"
    cleaned = clean_scraped_text(text)
    assert ":'" not in cleaned
    assert "!" not in cleaned

    # Test special characters
    text = "Special @#$%^&* characters"
    cleaned = clean_scraped_text(text)
    assert "@" in cleaned  # @ should be preserved
    assert not any(c in cleaned for c in "#$%^&*")


def test_dataframe_to_text():
    """Test the dataframe_to_text function."""
    # Create a test DataFrame
    data = {
        "Scheme": ["Test Scheme 1", "Test Scheme 2"],
        "Agency": ["Agency 1", "Agency 2"],
        "Description": ["Desc 1", "Desc 2"],
        "Link": ["http://test1.com", "http://test2.com"],
        "scraped_text": ["Scraped text 1\nwith newline", "Scraped: ''text 2!"],
    }
    df = pd.DataFrame(data)

    text = dataframe_to_text(df)

    # Verify the format and content
    assert "Scheme Name: Test Scheme 1" in text
    assert "Agency: Agency 1" in text
    assert "Description: Desc 1" in text
    assert "Link: http://test1.com" in text
    assert "Scraped Text from website:" in text
    assert "\n" in text  # Should have newlines between schemes
    assert "''text" not in text  # Should be cleaned
    assert "!" not in text  # Should be cleaned


def test_config_initialization(mocker):
    """Test Config class initialization and environment variable handling."""
    mocker.patch.dict(
        "os.environ",
        {
            "DEPLOYMENT": "test-deployment",
            "ENDPOINT": "test-endpoint",
            "VERSION": "test-version",
            "APIKEY": "test-key",
            "TYPE": "test-type",
            "MODEL": "test-model",
        },
        clear=True,
    )
    mocker.patch("ml_logic.chatbotManager.dotenv_values", return_value={})

    config = Config()
    assert config.deployment == "test-deployment"
    assert config.endpoint == "test-endpoint"
    assert config.version == "test-version"
    assert config.apikey == "test-key"
    assert config.type == "test-type"
    assert config.model == "test-model"

    # Test __getattr__ for non-existent variable
    assert config.nonexistent is None


@pytest.fixture(autouse=True)
def clear_chatbot_instance():
    """Clear Chatbot singleton instance between tests."""
    Chatbot._instance = None
    Chatbot.initialised = False
    yield


def test_chatbot_singleton(mocker):
    """Test Chatbot class singleton pattern."""
    # Mock dependencies to isolate singleton test
    mock_firebase = mocker.MagicMock()
    mocker.patch("ml_logic.chatbotManager.AzureChatOpenAI")
    mocker.patch("ml_logic.chatbotManager.Config")

    # Create first instance
    chatbot1 = Chatbot(mock_firebase)

    # Create second instance
    chatbot2 = Chatbot(mock_firebase)

    # Verify singleton pattern
    assert chatbot1 is chatbot2
    assert Chatbot._instance is not None


def test_generate_cache_key(mocker):
    """Test cache key generation."""
    # Mock dependencies to isolate cache key test
    mock_firebase = mocker.MagicMock()
    mocker.patch("ml_logic.chatbotManager.AzureChatOpenAI")
    mocker.patch("ml_logic.chatbotManager.Config")

    chatbot = Chatbot(mock_firebase)
    query = "test query"
    input_text = "test input"

    key1 = chatbot._generate_cache_key(query, input_text)
    key2 = chatbot._generate_cache_key(query, input_text)

    # Same inputs should generate same key
    assert key1 == key2

    # Different inputs should generate different keys
    different_key = chatbot._generate_cache_key("different query", input_text)
    assert key1 != different_key
