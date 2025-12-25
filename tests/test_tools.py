import json
import pytest
from tools import calculator, get_datetime, shell_command, create_tool_registry, Tool


def test_calculator_basic():
    """Test basic calculator operations."""
    assert calculator("2 + 2") == 4.0
    assert calculator("10 * 5") == 50.0
    assert calculator("100 / 4") == 25.0
    assert calculator("10 - 3") == 7.0
    assert calculator("10 % 3") == 1.0


def test_calculator_complex():
    """Test complex calculator expressions."""
    assert calculator("(2 + 3) * 4") == 20.0
    assert calculator("10 / (2 + 3)") == 2.0


def test_calculator_invalid():
    """Test calculator with invalid input."""
    with pytest.raises(ValueError, match="invalid characters"):
        calculator("import os")
    
    with pytest.raises(ValueError, match="invalid characters"):
        calculator("2 + 2; os.system('ls')")


def test_get_datetime_default():
    """Test get_datetime with default format."""
    result = get_datetime()
    # Should return ISO format (contains 'T')
    assert 'T' in result


def test_get_datetime_custom_format():
    """Test get_datetime with custom format."""
    result = get_datetime(format="%Y-%m-%d")
    # Should match YYYY-MM-DD pattern
    assert len(result) == 10
    assert result[4] == '-' and result[7] == '-'


def test_get_datetime_invalid_format():
    """Test get_datetime with custom formats."""
    # Test that various formats work
    result = get_datetime(format="%Y")
    assert len(result) == 4  # Just the year


def test_shell_command_basic():
    """Test basic shell command execution."""
    result = shell_command("echo hello")
    assert "hello" in result


def test_shell_command_with_output():
    """Test shell command that produces output."""
    result = shell_command("echo test123")
    assert "test123" in result


def test_shell_command_empty():
    """Test shell command with empty input."""
    with pytest.raises(RuntimeError, match="Command cannot be empty"):
        shell_command("")


def test_tool_to_schema():
    """Test Tool schema generation."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={
            "type": "object",
            "properties": {
                "arg1": {"type": "string"}
            },
            "required": ["arg1"]
        },
        function=lambda arg1: f"Result: {arg1}"
    )
    
    schema = tool.to_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "test_tool"
    assert schema["function"]["description"] == "A test tool"
    assert "properties" in schema["function"]["parameters"]


def test_tool_execute():
    """Test Tool execution."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={},
        function=lambda x, y: x + y
    )
    
    result = tool.execute('{"x": 5, "y": 3}')
    assert result == "8"


def test_tool_execute_error():
    """Test Tool execution with error."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={},
        function=lambda x: 1 / x
    )
    
    result = tool.execute('{"x": 0}')
    assert "Error" in result


def test_create_tool_registry():
    """Test tool registry creation."""
    tools = create_tool_registry()
    
    # Check that all expected tools are present
    assert "calculator" in tools
    assert "get_datetime" in tools
    assert "shell_command" in tools
    
    # Check that tools are Tool instances
    assert isinstance(tools["calculator"], Tool)
    assert isinstance(tools["get_datetime"], Tool)
    assert isinstance(tools["shell_command"], Tool)


def test_tool_registry_schemas():
    """Test that all tools can generate valid schemas."""
    tools = create_tool_registry()
    
    for tool_name, tool in tools.items():
        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]


def test_calculator_tool_execution():
    """Test calculator tool through tool registry."""
    tools = create_tool_registry()
    calc_tool = tools["calculator"]
    
    result = calc_tool.execute('{"expression": "5 * 5"}')
    assert result == "25.0"


def test_datetime_tool_execution():
    """Test datetime tool through tool registry."""
    tools = create_tool_registry()
    dt_tool = tools["get_datetime"]
    
    result = dt_tool.execute('{}')
    # Should return ISO format timestamp
    assert 'T' in result


def test_shell_tool_execution():
    """Test shell tool through tool registry."""
    tools = create_tool_registry()
    shell_tool = tools["shell_command"]
    
    result = shell_tool.execute('{"command": "echo test"}')
    assert "test" in result
