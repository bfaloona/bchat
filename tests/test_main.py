import asyncio
import configparser
import logging
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import pytest_asyncio
from main import load_config, main, async_main
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

    # Create an async mock for run()
    async def mock_run():
        pass
    
    # Create an async mock for client.close()
    async def mock_close():
        pass
    
    # Create an async mock for mcp_manager.cleanup()
    async def mock_cleanup():
        pass

    with patch('main.load_config', return_value=mock_config), \
         patch('main.setup_logging'), \
         patch('main.Session') as MockSession, \
         patch('main.Repl') as MockRepl:

        # Setup mock client with async close
        mock_client = MagicMock()
        mock_client.close = mock_close
        
        # Setup mock mcp_manager with async cleanup
        mock_mcp_manager = MagicMock()
        mock_mcp_manager.cleanup = mock_cleanup
        mock_mcp_manager.load_config = MagicMock()
        mock_mcp_manager.connect_autoconnect_servers = AsyncMock()
        
        MockSession.return_value.client = mock_client
        MockSession.return_value.mcp_manager = mock_mcp_manager
        
        MockRepl.return_value.run = mock_run
        main()

        MockSession.assert_called_once()
        MockRepl.assert_called_once()

@pytest.mark.asyncio
async def test_repl_commands(capsys):
    """
    Test REPL commands (/version, /help, /exit).
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /version
    await repl.handle_input("/version")
    captured = capsys.readouterr()
    assert "bchat version 0.1.0" in captured.out

    # Test /help
    await repl.handle_input("/help")
    captured = capsys.readouterr()
    assert "Available commands:" in captured.out
    assert "/version" in captured.out

    # Test /exit
    with pytest.raises(SystemExit):
        await repl.handle_input("/exit")

@pytest.mark.asyncio
async def test_repl_prompt_handling(capsys, caplog):
    """
    Test REPL prompt handling (sending request to OpenAI).
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "system_instruction": "You are a helpful assistant."
    }

    # Mock AsyncOpenAI client in the session
    with patch('session.AsyncOpenAI') as MockAsyncOpenAI:
        # Setup mock response
        mock_instance = MockAsyncOpenAI.return_value
        
        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'AI Response', 'tool_calls': None})})]
            mock_response.usage = type('obj', (object,), {'total_tokens': 10})
            return mock_response
        
        mock_instance.chat.completions.create = mock_create

        # Create session
        session = Session(mock_config)
        session.client = mock_instance

        repl = Repl(session)

        # Set log level
        caplog.set_level(logging.DEBUG)

        # Send a prompt
        await repl.handle_input("Hello AI")

        captured = capsys.readouterr()

        # Verify output
        # Check for the response.
        assert "AI Response" in captured.out

        # Verify logs
        assert "Request: Hello AI" in caplog.text

def test_startup_logging(caplog):
    """
    Test that model and temperature are logged at startup.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "temperature": "0.8"
    }

    async def mock_run():
        pass
    
    async def mock_close():
        pass
    
    async def mock_cleanup():
        pass

    with patch('main.load_config', return_value=mock_config), \
         patch('main.setup_logging'), \
         patch('main.Session') as MockSession, \
         patch('main.Repl') as MockRepl:

        # Setup mock session attributes
        mock_session_instance = MockSession.return_value
        mock_session_instance.model = "gpt-4o"
        mock_session_instance.temperature = 0.8
        
        # Setup mock client with async close
        mock_client = MagicMock()
        mock_client.close = mock_close
        mock_session_instance.client = mock_client
        
        # Setup mock mcp_manager
        mock_mcp_manager = MagicMock()
        mock_mcp_manager.cleanup = mock_cleanup
        mock_mcp_manager.load_config = MagicMock()
        mock_mcp_manager.connect_autoconnect_servers = AsyncMock()
        mock_session_instance.mcp_manager = mock_mcp_manager
        
        MockRepl.return_value.run = mock_run

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

@pytest.mark.asyncio
async def test_session_management():
    """
    Test saving, loading, and listing sessions.
    """
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {
        "api_key": "test-key",
        "max_history": "100"
    }

    # Create a temp dir for sessions
    with tempfile.TemporaryDirectory() as temp_dir:
        session = Session(mock_config)
        session.sessions_dir = temp_dir

        # Add some history
        session.add_message("user", "hello")
        session.add_message("assistant", "hi")

        # Test Save
        name = await session.save_session("test_session")
        assert name == "test_session"
        assert os.path.exists(os.path.join(temp_dir, "test_session.json"))

        # Test List
        sessions = session.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["name"] == "test_session"

        # Test Load
        # Create a new session object to load into
        new_session = Session(mock_config)
        new_session.sessions_dir = temp_dir
        loaded_name = await new_session.load_session("test_session")

        assert loaded_name == "test_session"
        assert len(new_session.history) == 2
        assert new_session.history[0]["content"] == "hello"

