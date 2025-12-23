import os
import tempfile
import configparser
from session import Session


def test_session_context_loader_initialization():
    """Test that Session initializes ContextLoader."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "context_max_size": "10000"
    }

    session = Session(mock_config)

    assert session.context_loader is not None
    assert session.context_loader.max_size == 10000


def test_get_messages_includes_file_context():
    """Test that get_messages includes file context in system prompt."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("def hello():\n    return 'world'")

        mock_config = configparser.ConfigParser()
        mock_config["DEFAULT"] = {
            "api_key": "test-key",
            "system_instruction": "You are a helpful assistant."
        }

        session = Session(mock_config)
        session.context_loader.add_file(test_file)

        messages = session.get_messages()

        # First message should be system message
        assert messages[0]["role"] == "system"
        system_content = messages[0]["content"]

        # Should include original system instruction
        assert "You are a helpful assistant." in system_content

        # Should include file context
        assert "## Loaded File Context" in system_content
        assert "### File:" in system_content
        assert test_file in system_content
        assert "def hello():" in system_content


def test_get_messages_without_file_context():
    """Test that get_messages works without file context."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "system_instruction": "You are a helpful assistant."
    }

    session = Session(mock_config)
    messages = session.get_messages()

    # First message should be system message
    assert messages[0]["role"] == "system"
    system_content = messages[0]["content"]

    # Should only include system instruction, no file context
    assert system_content == "You are a helpful assistant."
    assert "## Loaded File Context" not in system_content
