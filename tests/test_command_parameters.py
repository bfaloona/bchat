import configparser
import pytest
import pytest_asyncio
from session import Session
from repl import Repl
import tempfile
import os

async def test_clear_command(capsys):
    """Test /clear command empties history and file context."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)
    # Add history and fake file context
    session.add_message("user", "hello")
    session.file_context.files = [type("FakeFile", (), {"path": "foo.txt", "line_count": 1, "size": 10})()]
    assert len(session.history) == 1
    assert len(session.file_context.files) == 1
    await repl.handle_input("/clear")
    # Output may not be captured due to Rich, so just check state
    assert len(session.history) == 0
    assert len(session.file_context.files) == 0
"""Tests for command parameter parsing architecture."""


@pytest.mark.asyncio
async def test_zero_param_commands(capsys):
    """Test commands that take no parameters."""
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

    # Test /history
    await repl.handle_input("/history")
    captured = capsys.readouterr()
    # Should show no sessions or list sessions
    assert ("No saved sessions" in captured.out or "Saved Sessions" in captured.out)


@pytest.mark.asyncio
async def test_one_param_save_command(capsys):
    """Test /save command with various parameter formats."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session = Session(mock_config)
        session.sessions_dir = temp_dir
        repl = Repl(session)
        
        # Add some history
        session.add_message("user", "test message")
        
        # Test save with simple name
        await repl.handle_input("/save simple")
        captured = capsys.readouterr()
        assert "Saved:" in captured.out
        assert "simple" in captured.out
        assert os.path.exists(os.path.join(temp_dir, "simple.json"))
        
        # Reset session_name to test multi-word name
        session.session_name = None
        await repl.handle_input("/save my important session")
        captured = capsys.readouterr()
        assert "Saved:" in captured.out
        assert "my important session" in captured.out
        assert os.path.exists(os.path.join(temp_dir, "my important session.json"))
        
        # Test save without name (auto-generated) - clear session_name first
        session.session_name = None
        await repl.handle_input("/save")
        captured = capsys.readouterr()
        assert "Saved:" in captured.out
        # Should save with auto-generated name containing "session_"
        # The auto-generated name will be in the output
        saved_files = os.listdir(temp_dir)
        auto_generated = [f for f in saved_files if f.startswith("session_")]
        assert len(auto_generated) > 0


@pytest.mark.asyncio
async def test_one_param_load_command(capsys):
    """Test /load command with various parameter formats."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session = Session(mock_config)
        session.sessions_dir = temp_dir
        repl = Repl(session)
        
        # Create test sessions with multi-word names
        session.add_message("user", "test1")
        await session.save_session("my test session")
        
        session.history = []
        session.add_message("user", "test2")
        await session.save_session("another test")
        
        # Test load with simple name
        session.history = []
        await repl.handle_input("/load another test")
        captured = capsys.readouterr()
        assert "Loaded:" in captured.out
        assert "another test" in captured.out
        assert len(session.history) == 1
        
        # Test load with multi-word name
        session.history = []
        await repl.handle_input("/load my test session")
        captured = capsys.readouterr()
        assert "Loaded:" in captured.out
        assert "my test session" in captured.out
        assert len(session.history) == 1
        
        # Test load without name (loads most recent)
        session.history = []
        await repl.handle_input("/load")
        captured = capsys.readouterr()
        assert "Loaded:" in captured.out
        # Should load one of the sessions
        assert len(session.history) == 1


@pytest.mark.asyncio
async def test_two_param_set_command(capsys):
    """Test /set command with proper parameter splitting."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set with numeric temperature
    await repl.handle_input("/set temp 0.9")
    captured = capsys.readouterr()
    assert "0.9" in captured.out
    assert session.temperature == 0.9

    # Test /set with preset temperature
    await repl.handle_input("/set temperature creative")
    captured = capsys.readouterr()
    assert "creative" in captured.out.lower()
    assert session.temperature == 1.2

    # Test /set with model preset (use standard to avoid temp validation)
    await repl.handle_input("/set model standard")
    captured = capsys.readouterr()
    assert "gpt-4o" in captured.out
    assert session.model == "gpt-4o"

    # Test /set with personality
    await repl.handle_input("/set personality terse")
    captured = capsys.readouterr()
    assert "terse" in captured.out
    assert session.personality == "terse"


@pytest.mark.asyncio
async def test_set_command_missing_parameters(capsys):
    """Test /set command validation with missing parameters."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set with no parameters
    await repl.handle_input("/set")
    captured = capsys.readouterr()
    assert "Usage:" in captured.out
    assert "/set <option> <value>" in captured.out

    # Test /set with only option, no value
    await repl.handle_input("/set temp")
    captured = capsys.readouterr()
    assert "Usage:" in captured.out


@pytest.mark.asyncio
async def test_set_command_invalid_option(capsys):
    """Test /set command with invalid option."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set with invalid option
    await repl.handle_input("/set invalid value")
    captured = capsys.readouterr()
    assert "Unknown option" in captured.out
    assert "invalid" in captured.out
    assert "Valid options:" in captured.out


@pytest.mark.asyncio
async def test_set_command_invalid_value(capsys):
    """Test /set command with invalid value."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /set with invalid temperature value
    await repl.handle_input("/set temp invalid_number")
    captured = capsys.readouterr()
    assert "Error:" in captured.out
    assert "Invalid temperature" in captured.out


@pytest.mark.asyncio
async def test_unknown_command(capsys):
    """Test handling of unknown commands."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test unknown command
    await repl.handle_input("/unknown")
    captured = capsys.readouterr()
    assert "Unknown command:" in captured.out
    assert "/unknown" in captured.out


@pytest.mark.asyncio
async def test_add_command_with_pattern(capsys):
    """Test /add command treats entire parameter as single value."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /add with simple file (will fail but tests parameter parsing)
    await repl.handle_input("/add nonexistent.txt")
    captured = capsys.readouterr()
    # Should show error since file doesn't exist
    assert "Error:" in captured.out


@pytest.mark.asyncio
async def test_remove_command(capsys):
    """Test /remove command treats entire parameter as single value."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    session = Session(mock_config)
    repl = Repl(session)

    # Test /remove (will warn that file not in context)
    await repl.handle_input("/remove somefile.txt")
    captured = capsys.readouterr()
    assert "Warning:" in captured.out or "not in context" in captured.out.lower()


@pytest.mark.asyncio
async def test_command_parameter_parsing_edge_cases(capsys):
    """Test edge cases in command parameter parsing."""
    mock_config = configparser.ConfigParser()
    mock_config["DEFAULT"] = {"api_key": "test-key"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session = Session(mock_config)
        session.sessions_dir = temp_dir
        repl = Repl(session)
        
        # Add history for saving
        session.add_message("user", "test")
        
        # Test save with leading/trailing spaces
        await repl.handle_input("/save   test with spaces   ")
        captured = capsys.readouterr()
        assert "Saved:" in captured.out
        # The strip() in handle_input should handle this
        
        # Test empty command (just /)
        await repl.handle_input("/")
        captured = capsys.readouterr()
        # Should show unknown command
        assert "Unknown command:" in captured.out
