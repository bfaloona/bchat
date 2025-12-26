"""Integration tests for tool calling functionality."""

import configparser
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from session import Session
from repl import Repl


@pytest.mark.asyncio
async def test_session_tool_integration():
    """Test Session class tool integration."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "True"
    }
    
    session = Session(config)
    
    # Test tools_enabled flag
    assert session.tools_enabled is True
    
    # Test list_tools
    tools = session.list_tools()
    assert "calculator" in tools
    assert "get_datetime" in tools
    assert "shell_command" in tools
    
    # Test get_tool_schemas
    schemas = session.get_tool_schemas()
    assert len(schemas) == 3
    assert all(s["type"] == "function" for s in schemas)
    
    # Test execute_tool
    result = await session.execute_tool("calculator", '{"expression": "10 + 5"}')
    assert result == "15.0"
    
    # Test execute_tool with invalid tool
    result = await session.execute_tool("nonexistent_tool", '{}')
    assert "Error" in result


@pytest.mark.asyncio
async def test_session_tools_disabled():
    """Test Session with tools disabled."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "False"
    }
    
    session = Session(config)
    
    assert session.tools_enabled is False
    
    # get_tool_schemas should return empty list when disabled
    schemas = session.get_tool_schemas()
    assert schemas == []


@pytest.mark.asyncio
async def test_repl_tools_command(capsys):
    """Test /tools command in REPL."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "True"
    }
    
    session = Session(config)
    repl = Repl(session)
    
    # Execute /tools command
    await repl.cmd_tools([])
    
    captured = capsys.readouterr()
    
    # Should display all three tools
    assert "calculator" in captured.out
    assert "get_datetime" in captured.out
    assert "shell_command" in captured.out
    assert "Available Tools" in captured.out


@pytest.mark.asyncio
async def test_repl_tools_command_disabled(capsys):
    """Test /tools command when tools are disabled."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "False"
    }
    
    session = Session(config)
    repl = Repl(session)
    
    # Execute /tools command
    await repl.cmd_tools([])
    
    captured = capsys.readouterr()
    
    # Should show disabled message
    assert "disabled" in captured.out.lower()


@pytest.mark.asyncio
async def test_handle_tool_calls_integration():
    """Test _handle_tool_calls method."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "True"
    }
    
    with patch('session.AsyncOpenAI') as MockAsyncOpenAI:
        session = Session(config)
        mock_client = MockAsyncOpenAI.return_value
        session.client = mock_client
        repl = Repl(session)
        
        # Create mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{"expression": "2 + 2"}'
        
        mock_message = Mock()
        mock_message.content = None
        mock_message.tool_calls = [mock_tool_call]
        
        # Mock the second API call (after tool execution) as async
        async def mock_create(*args, **kwargs):
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "The result is 4.0"
            return mock_response
        
        mock_client.chat.completions.create = mock_create
        
        # Call _handle_tool_calls
        await repl._handle_tool_calls(mock_message, [])
        
        # Verify tool was added to history
        assert len(session.history) >= 2  # Assistant message + tool result
        assert any(msg.get("role") == "tool" for msg in session.history)
        assert any(msg.get("role") == "assistant" for msg in session.history)


@pytest.mark.asyncio
async def test_tool_execution_error_handling(capsys):
    """Test error handling during tool execution."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "True"
    }
    
    session = Session(config)
    
    # Test with invalid expression
    result = await session.execute_tool("calculator", '{"expression": "1/0"}')
    assert "Error" in result or "Division by zero" in result
    
    # Test with invalid JSON
    result = await session.execute_tool("calculator", 'invalid json')
    assert "Error" in result


@pytest.mark.asyncio
async def test_tool_call_logging(caplog):
    """Test that tool calls are properly logged."""
    import logging
    caplog.set_level(logging.INFO)
    
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "True"
    }
    
    session = Session(config)
    
    # Execute a shell command to trigger logging
    result = await session.execute_tool("shell_command", '{"command": "echo test"}')
    
    # Check that logging occurred
    assert any("Executing shell command" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_session_get_messages_with_tools():
    """Test that get_messages includes proper structure."""
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "api_key": "test-key",
        "tools_enabled": "True",
        "system_instruction": "Test instruction"
    }
    
    session = Session(config)
    session.add_message("user", "Hello")
    
    messages = session.get_messages()
    
    # Should have system message + user message
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"
