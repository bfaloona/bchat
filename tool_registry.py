"""
Tool Registry - Unified registry for local and MCP tools.

This module provides a single interface for accessing both local tools
(calculator, datetime, shell) and dynamically discovered MCP tools.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from tools import create_tool_registry as create_local_tool_registry

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Unified registry for local and MCP tools."""
    
    def __init__(self, mcp_manager=None):
        """
        Initialize the tool registry.
        
        Args:
            mcp_manager: Optional MCPManager instance for MCP tools
        """
        self.local_tools = create_local_tool_registry()
        self.mcp_manager = mcp_manager
        self.logger = logging.getLogger(__name__)
        
    def set_mcp_manager(self, mcp_manager):
        """Set or update the MCP manager."""
        self.mcp_manager = mcp_manager
        
    def get_all_tools(self) -> Dict[str, Any]:
        """
        Get all available tools (local + MCP).
        
        Returns:
            Dictionary mapping tool names to tool objects
        """
        all_tools = {}
        
        # Add local tools
        all_tools.update(self.local_tools)
        
        # Add MCP tools if manager is available
        if self.mcp_manager:
            mcp_tools = self.mcp_manager.get_all_tools()
            for tool_name, tool_info in mcp_tools.items():
                # Store tool info with marker that it's from MCP
                all_tools[tool_name] = {
                    "type": "mcp",
                    "server": tool_info["server"],
                    "description": tool_info["description"],
                    "tool": tool_info["tool"]
                }
                
        return all_tools
        
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-format schemas for all tools.
        
        Returns:
            List of tool schemas in OpenAI function calling format
        """
        schemas = []
        
        # Add local tool schemas
        for tool in self.local_tools.values():
            schemas.append(tool.to_schema())
            
        # Add MCP tool schemas
        if self.mcp_manager:
            schemas.extend(self.mcp_manager.get_tool_schemas())
            
        return schemas
        
    async def execute_tool(self, tool_name: str, arguments: str) -> str:
        """
        Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: JSON string of arguments
            
        Returns:
            Tool execution result as string
        """
        # Check if it's a local tool
        if tool_name in self.local_tools:
            return self.local_tools[tool_name].execute(arguments)
            
        # Check if it's an MCP tool
        if tool_name.startswith("mcp_") and self.mcp_manager:
            try:
                args_dict = json.loads(arguments)
                return await self.mcp_manager.call_tool(tool_name, args_dict)
            except Exception as e:
                logger.error(f"Error executing MCP tool {tool_name}: {e}", exc_info=True)
                return f"Error: {str(e)}"
                
        return f"Error: Unknown tool '{tool_name}'"
        
    def list_tools(self, server_filter: Optional[str] = None) -> List[str]:
        """
        List all available tool names.
        
        Args:
            server_filter: Optional MCP server name to filter by
            
        Returns:
            List of tool names
        """
        tools = []
        
        # Add local tools if no server filter
        if not server_filter:
            tools.extend(self.local_tools.keys())
            
        # Add MCP tools
        if self.mcp_manager:
            mcp_tools = self.mcp_manager.get_all_tools(server_filter)
            tools.extend(mcp_tools.keys())
            
        return tools
        
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information dictionary or None if not found
        """
        # Check local tools
        if tool_name in self.local_tools:
            tool = self.local_tools[tool_name]
            return {
                "name": tool_name,
                "type": "local",
                "description": tool.description,
                "parameters": tool.parameters
            }
            
        # Check MCP tools
        if tool_name.startswith("mcp_") and self.mcp_manager:
            all_mcp_tools = self.mcp_manager.get_all_tools()
            if tool_name in all_mcp_tools:
                tool_info = all_mcp_tools[tool_name]
                return {
                    "name": tool_name,
                    "type": "mcp",
                    "server": tool_info["server"],
                    "description": tool_info["description"]
                }
                
        return None
