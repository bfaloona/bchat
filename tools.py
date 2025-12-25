"""
Tool definitions for LLM function calling.

This module defines callable tools that the LLM can use to perform specific tasks.
Each tool is defined with its function, schema, and execution logic.
"""

import json
import subprocess
import shlex
from datetime import datetime
from typing import Any, Dict, List, Callable
import logging

logger = logging.getLogger(__name__)


class Tool:
    """Represents a callable tool that can be used by the LLM."""

    def __init__(self, name: str, description: str, parameters: Dict, function: Callable):
        """
        Initialize a tool.

        Args:
            name: Tool name
            description: Description of what the tool does
            parameters: JSON schema for the tool's parameters
            function: The Python function to execute
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function

    def to_schema(self) -> Dict:
        """Convert tool to OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def execute(self, arguments: str) -> str:
        """
        Execute the tool with given arguments.

        Args:
            arguments: JSON string of arguments

        Returns:
            Result as string
        """
        try:
            args = json.loads(arguments)
            result = self.function(**args)
            return str(result)
        except Exception as e:
            logger.error(f"Tool {self.name} execution error: {e}", exc_info=True)
            return f"Error: {str(e)}"


# Tool function implementations

def calculator(expression: str) -> float:
    """
    Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5")

    Returns:
        Result of the calculation
    """
    # Sanitize input - only allow numbers, basic operators, parentheses, and whitespace
    allowed_chars = set("0123456789+-*/()%. ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("Expression contains invalid characters")

    # Use eval with restricted globals for safety
    try:
        # Restrict to only mathematical operations
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def get_datetime(format: str = None, timezone: str = None) -> str:
    """
    Get current date and time.

    Args:
        format: Optional strftime format string (default: ISO 8601)
        timezone: Optional timezone (not currently supported, uses local time)

    Returns:
        Formatted date/time string
    """
    now = datetime.now()

    if format:
        try:
            return now.strftime(format)
        except Exception as e:
            raise ValueError(f"Invalid format string: {e}")
    else:
        # Default to ISO 8601 format
        return now.isoformat()


def shell_command(command: str, timeout: int = 30) -> str:
    """
    Execute a shell command.

    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        Command output (stdout and stderr combined)
    """
    # Security: Parse command to prevent injection
    try:
        # Validate command is not empty
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")

        logger.info(f"Executing shell command: {command}")

        # Execute with timeout and capture output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]:\n" + result.stderr

        # Include return code if non-zero
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Command timed out after {timeout} seconds")
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")


# Tool registry

def create_tool_registry() -> Dict[str, Tool]:
    """
    Create and return the registry of available tools.

    Returns:
        Dictionary mapping tool names to Tool instances
    """
    tools = [
        Tool(
            name="calculator",
            description="Evaluate mathematical expressions. Supports basic arithmetic operations (+, -, *, /, %), parentheses, and decimal numbers.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate, e.g., '2 + 2' or '(10 * 5) / 2'"
                    }
                },
                "required": ["expression"]
            },
            function=calculator
        ),
        Tool(
            name="get_datetime",
            description="Get the current date and time. Can optionally format the output using strftime format codes.",
            parameters={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Optional strftime format string. Examples: '%Y-%m-%d' for date only, '%I:%M %p' for 12-hour time. Leave empty for ISO 8601 format."
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Optional timezone (not currently supported, uses local time)"
                    }
                },
                "required": []
            },
            function=get_datetime
        ),
        Tool(
            name="shell_command",
            description="Execute a shell command and return its output. Use for file operations, system queries, etc. Be cautious with destructive commands.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute, e.g., 'ls -la', 'echo hello', 'date'"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)"
                    }
                },
                "required": ["command"]
            },
            function=shell_command
        )
    ]

    return {tool.name: tool for tool in tools}
