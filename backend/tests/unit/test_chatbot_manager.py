"""Unit tests for chatbotManager.py."""

import os

import pandas as pd
import pytest
from ml_logic.chatbotManager import Chatbot
from ml_logic.config import ChatbotConfig
from ml_logic.text_utils import clean_scraped_text, dataframe_to_text


def test_chatbot_config_defaults():
    """Test ChatbotConfig initializes with correct default values."""
    config = ChatbotConfig()

    assert config.temperature == 0.1
    assert config.top_p == 0.9
    assert config.presence_penalty == 0.2
    assert config.frequency_penalty == 0.2
    assert config.max_tokens == 512


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
    """Test the dataframe_to_text function with expected columns."""
    # Create a test DataFrame with all possible fields
    data = {
        "scheme": ["Test Scheme 1", "Test Scheme 2"],
        "agency": ["Agency 1", "Agency 2"],
        "llm_description": ["Desc 1", "Desc 2"],
        "link": ["http://test1.com", "http://test2.com"],
        "phone": ["123-456", "789-012"],
        "address": ["Address 1", "Address 2"],
        "eligibility": ["Eligible 1", "Eligible 2"],
        "email": ["email1@test.com", "email2@test.com"],
        "what_it_gives": ["Benefit 1", "Benefit 2"],
        "how_to_apply": ["Apply 1", "Apply 2"],
        "service_area": ["Area 1", "Area 2"],
    }
    df = pd.DataFrame(data)

    text = dataframe_to_text(df)

    # Verify key fields appear in the output
    assert "Scheme Name: Test Scheme 1" in text
    assert "Agency: Agency 1" in text
    assert "Description: Desc 1" in text
    assert "Link: http://test1.com" in text
    assert "Phone: 123-456" in text
    assert "Address: Address 1" in text
    assert "Eligibility: Eligible 1" in text
    assert "Email: email1@test.com" in text
    assert "How to Apply: Apply 1" in text
    assert "What it Gives: Benefit 1" in text
    assert "Service Area: Area 1" in text

    # Check both rows are included
    assert "Scheme Name: Test Scheme 2" in text
    assert "Agency: Agency 2" in text


def test_chatbot_calls_init_chat_model_with_env(mocker):
    # Patch init_chat_model where Chatbot actually uses it
    mock_init = mocker.patch("ml_logic.chatbotManager.init_chat_model", return_value=mocker.MagicMock())

    # Set env var
    mocker.patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment"}, clear=True)

    from ml_logic.chatbotManager import Chatbot, ChatbotConfig

    # Reset singleton state
    Chatbot._instance = None
    Chatbot.initialised = False

    # Assign a mock firebase manager (required by initialise)
    mock_firebase = mocker.MagicMock()
    Chatbot.firebase_manager = mock_firebase

    # Call initialise -> triggers init_chat_model
    Chatbot.initialise()

    # Assert init_chat_model was called
    mock_init.assert_called_once_with(
        "azure_openai:gpt-4.1-mini",
        azure_deployment="test-deployment",
        **ChatbotConfig().__dict__,
    )


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
    mocker.patch("ml_logic.chatbotManager.init_chat_model", return_value=mocker.MagicMock())

    chatbot1 = Chatbot(mock_firebase)
    chatbot2 = Chatbot(mock_firebase)

    # Verify singleton pattern
    assert chatbot1 is chatbot2
    assert Chatbot._instance is not None


def test_chatbot_error_handling(mock_firebase_manager, mocker):
    """Test chatbot error handling when graph.invoke fails."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock graph.invoke to raise an exception
    mocker.patch.object(chatbot.graph, "invoke", side_effect=Exception("Graph execution failed"))

    # Call chatbot
    response = chatbot.chatbot(
        top_schemes_text="test schemes",
        input_text="test input",
        session_id="test-session",
        query_text="test query",
    )

    # Verify error response
    assert response["response"] is False
    assert response["message"] == "No response from the chatbot."


def test_replay_cached_tokens():
    """Test the _replay_cached_tokens static method."""

    # Mock saved_updates structure
    class MockMessage:
        def __init__(self, content):
            self.content = content

    saved_updates = {"chatbot": {"messages": [MockMessage("Hello world\nThis is a test")]}}

    # Test the static method
    tokens = list(Chatbot._replay_cached_tokens(saved_updates))

    # Verify tokens are properly split
    token_string = "".join(tokens)
    assert "Hello world" in token_string
    assert "This is a test" in token_string


def test_create_configurable(mock_firebase_manager):
    """Test the _create_configurable method."""
    chatbot = Chatbot(mock_firebase_manager)
    config = chatbot._create_configurable("test-session-123")

    expected = {"configurable": {"thread_id": "test-session-123"}}
    assert config == expected
