import configparser
import logging
from unittest.mock import patch, MagicMock
import pytest
from main import load_config, main
from repl import Repl
from session import Session

def test_load_config():
    """
    Happy Path test for load_config.
    Verifies that the configuration is loaded and contains the DEFAULT section.
    """
    config = load_config()
    assert isinstance(config, configparser.ConfigParser)
    assert "DEFAULT" in config

def test_main_initialization():
    """
    Happy Path test for main initialization.
    Verifies that main initializes Session and Repl and calls run.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}

    with patch('main.load_config', return_value=mock_config), \
         patch('main.setup_logging'), \
         patch('main.Session') as MockSession, \
         patch('main.Repl') as MockRepl:

        main()

        MockSession.assert_called_once()
        MockRepl.assert_called_once()
        MockRepl.return_value.run.assert_called_once()

def test_repl_commands(capsys):
    """
    Test REPL commands (/version, /help, /exit).
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /version
    repl.handle_input("/version")
    captured = capsys.readouterr()
    assert "bchat version 0.1.0" in captured.out

    # Test /help
    repl.handle_input("/help")
    captured = capsys.readouterr()
    assert "Available commands:" in captured.out
    assert "/version" in captured.out

    # Test /exit
    with pytest.raises(SystemExit):
        repl.handle_input("/exit")

def test_repl_prompt_handling(capsys, caplog):
    """
    Test REPL prompt handling (sending request to OpenAI).
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "system_instruction": "You are a helpful assistant."
    }

    # Mock OpenAI client in the session
    with patch('session.OpenAI') as MockOpenAI:
        session = Session(mock_config)

        # Setup mock response
        mock_instance = MockOpenAI.return_value
        mock_response = mock_instance.chat.completions.create.return_value
        mock_response.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'AI Response'})})]
        mock_response.usage = type('obj', (object,), {'total_tokens': 10})

        # Re-initialize session to pick up the mock client
        session = Session(mock_config)
        # Manually set the client because the patch in Session.__init__ might be tricky with the way we're testing
        session.client = MockOpenAI.return_value

        repl = Repl(session)

        # Set log level
        caplog.set_level(logging.DEBUG)

        # Send a prompt
        repl.handle_input("Hello AI")

        captured = capsys.readouterr()

        # Verify output
        assert "Sending request to OpenAI..." in captured.out
        assert "AI Response" in captured.out

def test_startup_logging(caplog):
    """
    Test that model and temperature are logged at startup.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "temperature": "0.8"
    }

    with patch('main.load_config', return_value=mock_config), \
         patch('main.setup_logging'), \
         patch('main.Session') as MockSession, \
         patch('main.Repl') as MockRepl:
        
        # Setup mock session attributes
        mock_session_instance = MockSession.return_value
        mock_session_instance.model = "gpt-4o"
        mock_session_instance.temperature = 0.8
        
        # Set capture level to INFO
        caplog.set_level(logging.INFO)
        
        main()
        
        assert "Session initialized with model: gpt-4o, temperature: 0.8" in caplog.text

def test_session_history():
    """
    Test that session history is maintained and respects max_history.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "max_history": "2",
        "system_instruction": "System"
    }
    
    session = Session(mock_config)
    
    # Add messages
    session.add_message("user", "msg1")
    session.add_message("assistant", "resp1")
    session.add_message("user", "msg2")
    
    # Check history length (should be 2 because max_history is 2)
    assert len(session.history) == 2
    assert session.history[0]["content"] == "resp1"
    assert session.history[1]["content"] == "msg2"
    
    # Check full messages (should include system instruction + 2 history messages)
    messages = session.get_messages()
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "resp1"
    assert messages[2]["content"] == "msg2"
