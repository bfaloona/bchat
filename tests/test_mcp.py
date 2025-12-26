"""Tests for MCP manager and tool registry."""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from mcp_manager import MCPManager, MCPConnection, MCPServerConfig
from tool_registry import ToolRegistry


def test_mcp_server_config():
    """Test MCPServerConfig initialization."""
    config = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/test"],
        "autoconnect": True,
        "description": "Test server"
    }
    
    server_config = MCPServerConfig("test_server", config)
    
    assert server_config.name == "test_server"
    assert server_config.command == "npx"
    assert server_config.args == ["-y", "@modelcontextprotocol/server-filesystem", "~/test"]
    assert server_config.autoconnect is True
    assert server_config.description == "Test server"


def test_mcp_manager_initialization():
    """Test MCPManager initialization."""
    manager = MCPManager("test_config.yaml")
    
    assert manager.config_path.name == "test_config.yaml"
    assert len(manager.servers) == 0
    assert len(manager.connections) == 0


def test_mcp_manager_namespace_tool_name():
    """Test tool name namespacing."""
    config = MCPServerConfig("github", {"command": "test", "args": []})
    connection = MCPConnection(config)
    
    namespaced = connection._namespace_tool_name("list_repos")
    assert namespaced == "mcp_github_list_repos"


def test_tool_registry_initialization():
    """Test ToolRegistry initialization."""
    registry = ToolRegistry()
    
    # Should have local tools initialized
    assert "calculator" in registry.local_tools
    assert "get_datetime" in registry.local_tools
    assert "shell_command" in registry.local_tools


def test_tool_registry_list_tools():
    """Test listing tools without MCP manager."""
    registry = ToolRegistry()
    
    tools = registry.list_tools()
    
    assert "calculator" in tools
    assert "get_datetime" in tools
    assert "shell_command" in tools


def test_tool_registry_get_tool_schemas():
    """Test getting tool schemas without MCP."""
    registry = ToolRegistry()
    
    schemas = registry.get_tool_schemas()
    
    # Should have 3 local tools
    assert len(schemas) == 3
    assert all(schema["type"] == "function" for schema in schemas)


@pytest.mark.asyncio
async def test_tool_registry_execute_local_tool():
    """Test executing a local tool through the registry."""
    registry = ToolRegistry()
    
    result = await registry.execute_tool("calculator", '{"expression": "5 + 5"}')
    
    assert result == "10.0"


@pytest.mark.asyncio
async def test_tool_registry_execute_unknown_tool():
    """Test executing an unknown tool."""
    registry = ToolRegistry()
    
    result = await registry.execute_tool("nonexistent_tool", '{}')
    
    assert "Error" in result
    assert "Unknown tool" in result


def test_tool_registry_get_tool_info():
    """Test getting tool information."""
    registry = ToolRegistry()
    
    # Test local tool
    info = registry.get_tool_info("calculator")
    
    assert info is not None
    assert info["name"] == "calculator"
    assert info["type"] == "local"
    assert "description" in info
    assert "parameters" in info


def test_tool_registry_get_tool_info_not_found():
    """Test getting info for non-existent tool."""
    registry = ToolRegistry()
    
    info = registry.get_tool_info("nonexistent_tool")
    
    assert info is None


@pytest.mark.asyncio
async def test_tool_registry_with_mcp_manager():
    """Test tool registry with mocked MCP manager."""
    # Create mock MCP manager
    mock_mcp_manager = MagicMock()
    
    # Mock the get_all_tools method
    mock_mcp_manager.get_all_tools.return_value = {
        "mcp_github_list_repos": {
            "server": "github",
            "description": "List repositories",
            "tool": MagicMock()
        }
    }
    
    # Mock get_tool_schemas
    mock_mcp_manager.get_tool_schemas.return_value = [
        {
            "type": "function",
            "function": {
                "name": "mcp_github_list_repos",
                "description": "List repositories",
                "parameters": {}
            }
        }
    ]
    
    registry = ToolRegistry(mock_mcp_manager)
    
    # Test that MCP tools are included
    all_tools = registry.get_all_tools()
    assert "calculator" in all_tools  # Local tool
    assert "mcp_github_list_repos" in all_tools  # MCP tool
    
    # Test schemas include both local and MCP
    schemas = registry.get_tool_schemas()
    assert len(schemas) == 4  # 3 local + 1 MCP
    
    # Test list_tools
    tools = registry.list_tools()
    assert "calculator" in tools
    assert "mcp_github_list_repos" in tools


@pytest.mark.asyncio
async def test_tool_registry_execute_mcp_tool():
    """Test executing an MCP tool through the registry."""
    # Create mock MCP manager
    mock_mcp_manager = MagicMock()
    
    # Mock the call_tool method to return a coroutine
    async def mock_call_tool(tool_name, args):
        return "Mock result"
    
    mock_mcp_manager.call_tool = mock_call_tool
    
    # Mock get_all_tools to include our tool
    mock_mcp_manager.get_all_tools.return_value = {
        "mcp_test_tool": {
            "server": "test",
            "description": "Test tool",
            "tool": MagicMock()
        }
    }
    
    registry = ToolRegistry(mock_mcp_manager)
    
    result = await registry.execute_tool("mcp_test_tool", '{"arg": "value"}')
    
    assert result == "Mock result"


def test_mcp_manager_get_status_empty():
    """Test getting status with no servers configured."""
    manager = MCPManager()
    
    status = manager.get_status()
    
    assert status == []


def test_tool_registry_list_tools_with_server_filter():
    """Test listing tools with server filter."""
    # Create mock MCP manager
    mock_mcp_manager = MagicMock()
    
    # Mock get_all_tools with server filter
    mock_mcp_manager.get_all_tools.return_value = {
        "mcp_github_list_repos": {
            "server": "github",
            "description": "List repositories",
            "tool": MagicMock()
        }
    }
    
    registry = ToolRegistry(mock_mcp_manager)
    
    # Test filtering by server (should only return MCP tools from that server)
    tools = registry.list_tools(server_filter="github")
    
    assert "mcp_github_list_repos" in tools
    assert "calculator" not in tools  # Local tools not included with filter
