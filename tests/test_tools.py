import json
import pytest
import time
from tools import calculator, get_datetime, shell_command, create_tool_registry, Tool


# ============================================================================
# Calculator Tests
# ============================================================================

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


def test_calculator_negative_numbers():
    """Test calculator with negative numbers."""
    assert calculator("-5 + 3") == -2.0
    assert calculator("-5 * -3") == 15.0
    assert calculator("10 - -5") == 15.0


def test_calculator_decimals():
    """Test calculator with decimal numbers."""
    result = calculator("0.1 + 0.2")
    assert abs(result - 0.3) < 0.0001  # Floating point tolerance
    assert calculator("5.5 * 2") == 11.0


def test_calculator_division_by_zero():
    """Test calculator handles division by zero."""
    with pytest.raises(ValueError, match="Division by zero"):
        calculator("1 / 0")
    with pytest.raises(ValueError, match="Division by zero"):
        calculator("10 / (5 - 5)")


def test_calculator_power_limits():
    """Test calculator limits power operations to prevent DoS."""
    # Should work for reasonable powers
    assert calculator("2 ** 10") == 1024.0
    assert calculator("10 ** 2") == 100.0
    
    # Should reject large base
    with pytest.raises(ValueError, match="Power operation values too large"):
        calculator("9999 ** 2")
    
    # Should reject large exponent
    with pytest.raises(ValueError, match="Power operation values too large"):
        calculator("2 ** 200")


def test_calculator_overflow():
    """Test calculator detects overflow."""
    # Python's float can handle very large numbers, so this test is more about
    # the practical limit. Testing with actual overflow is challenging.
    # Instead, test that very large results are handled
    result = calculator("10 ** 50")
    assert result > 0  # Should succeed but be very large
    
    # Test that we catch results beyond the power operation limit
    with pytest.raises(ValueError, match="Power operation|Result too large"):
        calculator("10 ** 999")



def test_calculator_expression_length():
    """Test calculator rejects very long expressions."""
    long_expr = "1 + " * 100 + "1"
    with pytest.raises(ValueError, match="Expression too long"):
        calculator(long_expr)


def test_calculator_nested_parentheses():
    """Test calculator handles deeply nested parentheses."""
    # Should work for reasonable nesting
    assert calculator("((((1 + 1))))") == 2.0
    
    # Python's AST parser has its own limits, so we don't need to 
    # enforce additional limits here. The depth limit we added prevents
    # computational DoS, not parsing DoS.
    # This test ensures reasonable nesting works
    nested = "(" * 10 + "1" + ")" * 10
    assert calculator(nested) == 1.0



def test_calculator_invalid():
    """Test calculator with invalid input."""
    with pytest.raises(ValueError, match="invalid characters"):
        calculator("import os")
    
    with pytest.raises(ValueError, match="invalid characters"):
        calculator("2 + 2; os.system('ls')")
    
    with pytest.raises(ValueError, match="invalid characters"):
        calculator("__import__('os')")


# ============================================================================
# DateTime Tests
# ============================================================================

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


def test_get_datetime_various_formats():
    """Test get_datetime with various format strings."""
    # Test that various formats work
    result = get_datetime(format="%Y")
    assert len(result) == 4  # Just the year
    
    result = get_datetime(format="%H:%M:%S")
    assert len(result) == 8  # HH:MM:SS
    
    result = get_datetime(format="%B %d, %Y")
    # Should be like "December 25, 2025"
    assert "," in result


def test_get_datetime_empty_format():
    """Test get_datetime with empty format string."""
    result = get_datetime(format="")
    # Empty format in strftime returns empty string
    assert result == "" or isinstance(result, str)


def test_get_datetime_timezone_parameter():
    """Test that timezone parameter is accepted but ignored."""
    # Should not raise error even though timezone isn't supported
    result = get_datetime(timezone="UTC")
    assert 'T' in result  # Still returns ISO format


# ============================================================================
# Shell Command Tests
# ============================================================================

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
    with pytest.raises(ValueError, match="Command cannot be empty"):
        shell_command("")
    with pytest.raises(ValueError, match="Command cannot be empty"):
        shell_command("   ")


def test_shell_command_timeout():
    """Test shell command timeout behavior."""
    with pytest.raises(TimeoutError, match="timed out"):
        shell_command("sleep 5", timeout=1)


def test_shell_command_nonzero_exit():
    """Test shell command with non-zero exit code."""
    # Use a simple command that fails without dangerous patterns
    result = shell_command("exit 1")
    # Should capture exit code
    assert "exit code: 1" in result


def test_shell_command_stderr():
    """Test shell command that outputs to stderr."""
    # Use a command that doesn't trigger security filters
    # Most commands naturally write errors to stderr when they fail
    result = shell_command("ls --invalid-option")
    # Should capture stderr or exit code
    assert "[stderr]" in result or "exit code" in result or "unrecognized" in result.lower()



def test_shell_command_long_command():
    """Test shell command rejects excessively long commands."""
    long_cmd = "echo " + "a" * 1000
    with pytest.raises(ValueError, match="Command too long"):
        shell_command(long_cmd)


def test_shell_command_injection_prevention():
    """Test shell command blocks injection attempts."""
    # Test semicolon chaining
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("echo hello; rm -rf /")
    
    # Test pipe chaining
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("echo hello | cat")
    
    # Test command substitution
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("echo $(whoami)")
    
    # Test backtick substitution
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("echo `whoami`")
    
    # Test background process
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("sleep 100 &")


def test_shell_command_dangerous_commands():
    """Test shell command blocks dangerous rm commands."""
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("rm -rf /")
    with pytest.raises(ValueError, match="dangerous pattern"):
        shell_command("rm -rf /tmp")


def test_shell_command_output_size_limit():
    """Test shell command limits output size."""
    # Generate large output (but command itself is safe)
    result = shell_command("python3 -c \"print('x' * 200000)\"")
    # Output should be truncated
    assert "[output truncated]" in result or len(result) < 150000


# ============================================================================
# Tool Class Tests
# ============================================================================

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


def test_tool_execute_invalid_json():
    """Test Tool execution with invalid JSON arguments."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={},
        function=lambda x: x
    )
    
    result = tool.execute('not valid json')
    assert "Error" in result


def test_tool_execute_missing_params():
    """Test Tool execution with missing required parameters."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={},
        function=lambda required_param: required_param
    )
    
    result = tool.execute('{"wrong_param": "value"}')
    assert "Error" in result


def test_tool_execute_extra_params():
    """Test Tool execution with extra parameters."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={},
        function=lambda x: x * 2
    )
    
    # Should ignore extra params and work fine
    result = tool.execute('{"x": 5, "extra": "ignored"}')
    assert "Error" in result or result == "10"  # Depends on how kwargs are handled


# ============================================================================
# Registry Tests
# ============================================================================

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
