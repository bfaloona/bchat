"""
MCP Manager - Manages connections to Model Context Protocol servers.

This module provides async client management for MCP servers, including:
- Dynamic server connection/disconnection
- Namespaced tool discovery
- OpenAI-format schema conversion
- Error handling and recovery
- Hot-swap capability
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Configuration for a single MCP server."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.command = config.get("command", "")
        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self.autoconnect = config.get("autoconnect", False)
        self.description = config.get("description", "")
        
    def __eq__(self, other):
        """Compare configs for equality to detect changes."""
        if not isinstance(other, MCPServerConfig):
            return False
        return (self.command == other.command and 
                self.args == other.args and 
                self.env == other.env and 
                self.autoconnect == other.autoconnect)
        
    def get_server_params(self) -> StdioServerParameters:
        """Create StdioServerParameters from config."""
        # Expand environment variables in env values
        expanded_env = {}
        for key, value in self.env.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                expanded_env[key] = os.environ.get(env_var, "")
            else:
                expanded_env[key] = value
                
        # Merge with current environment
        env = os.environ.copy()
        env.update(expanded_env)
        
        return StdioServerParameters(
            command=self.command,
            args=self.args,
            env=env
        )


class MCPConnection:
    """Manages a single MCP server connection."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self.connected = False
        self.tools: Dict[str, Any] = {}
        self._client_context = None
        self._session_context = None
        self._connection_lock = asyncio.Lock()  # Prevent concurrent connections
        
    async def connect(self) -> bool:
        """
        Connect to the MCP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        # Prevent concurrent connection attempts
        async with self._connection_lock:
            if self.connected:
                logger.warning(f"Server {self.config.name} already connected")
                return True
                
            try:
                logger.info(f"Connecting to MCP server: {self.config.name}")
                server_params = self.config.get_server_params()
                
                # Create client context with timeout
                self._client_context = stdio_client(server_params)
                
                # Use asyncio.wait_for to add timeout protection
                try:
                    self.read_stream, self.write_stream = await asyncio.wait_for(
                        self._client_context.__aenter__(),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Connection to {self.config.name} timed out after 30 seconds")
                    return False
                
                # Create session context
                self._session_context = ClientSession(self.read_stream, self.write_stream)
                self.session = await self._session_context.__aenter__()
                
                # Initialize the session with timeout
                try:
                    await asyncio.wait_for(self.session.initialize(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.error(f"Session initialization for {self.config.name} timed out")
                    await self._cleanup()
                    return False
                
                # Discover tools
                await self._discover_tools()
                
                self.connected = True
                logger.info(f"Successfully connected to {self.config.name}, discovered {len(self.tools)} tools")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to {self.config.name}: {e}", exc_info=True)
                await self._cleanup()
                return False
            
    async def disconnect(self) -> bool:
        """
        Disconnect from the MCP server.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.connected:
            logger.warning(f"Server {self.config.name} not connected")
            return True
            
        try:
            logger.info(f"Disconnecting from MCP server: {self.config.name}")
            await self._cleanup()
            self.connected = False
            self.tools.clear()
            logger.info(f"Successfully disconnected from {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.config.name}: {e}", exc_info=True)
            return False
            
    async def _cleanup(self):
        """Clean up connection resources ensuring both contexts are cleaned."""
        exceptions = []
        
        # Clean up session context first
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                exceptions.append(e)
                logger.error(f"Error closing session context for {self.config.name}: {e}", exc_info=True)
            finally:
                self._session_context = None
                self.session = None
        
        # Clean up client context
        if self._client_context:
            try:
                await asyncio.wait_for(self._client_context.__aexit__(None, None, None), timeout=10)
            except asyncio.CancelledError:
                # Log the cancellation and ensure resources are cleaned up
                logger.warning("Cleanup was cancelled. Ensuring resources are released.")
            except asyncio.TimeoutError:
                # Handle timeout during cleanup
                logger.error("Cleanup timed out. Subprocess may not have terminated properly.")
            finally:
                # Additional cleanup logic if necessary
                if self._process and not self._process.returncode:
                    self._process.terminate()
                    await self._process.wait()
                self._client_context = None
                self.read_stream = None
                self.write_stream = None
        
        # Re-raise first exception if any occurred
        if exceptions:
            raise exceptions[0]
            
    async def _discover_tools(self):
        """Discover tools from the connected server."""
        if not self.session:
            return
            
        try:
            tools_result = await self.session.list_tools()
            
            # Store tools with namespace prefix
            self.tools = {}
            for tool in tools_result.tools:
                namespaced_name = self._namespace_tool_name(tool.name)
                self.tools[namespaced_name] = tool
                logger.debug(f"Discovered tool: {namespaced_name} - {tool.description}")
                
        except Exception as e:
            logger.error(f"Failed to discover tools from {self.config.name}: {e}", exc_info=True)
            
    def _namespace_tool_name(self, tool_name: str) -> str:
        """
        Create namespaced tool name.
        
        Format: mcp_{server_name}_{tool_name}
        """
        return f"mcp_{self.config.name}_{tool_name}"
        
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-format schemas for all tools.
        
        Returns:
            List of tool schemas in OpenAI function calling format
        """
        schemas = []
        for namespaced_name, tool in self.tools.items():
            schema = {
                "type": "function",
                "function": {
                    "name": namespaced_name,
                    "description": f"[{self.config.name}] {tool.description}",
                    "parameters": tool.inputSchema if tool.inputSchema else {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            schemas.append(schema)
        return schemas
        
    def _extract_original_tool_name(self, namespaced_name: str) -> str:
        """Extract original tool name from namespaced name."""
        return namespaced_name.replace(f"mcp_{self.config.name}_", "", 1)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the connected server.
        
        Args:
            tool_name: Namespaced tool name (mcp_{server}_{tool})
            arguments: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        if not self.connected or not self.session:
            raise RuntimeError(f"Server {self.config.name} not connected")
            
        # Extract original tool name using helper method
        original_tool_name = self._extract_original_tool_name(tool_name)
        
        if original_tool_name not in [t.name for t in self.tools.values()]:
            raise ValueError(f"Tool {original_tool_name} not found on server {self.config.name}")
            
        try:
            result = await self.session.call_tool(original_tool_name, arguments)
            
            # Extract content from result
            if hasattr(result, 'content') and result.content:
                content_parts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_parts.append(item.text)
                    elif hasattr(item, 'type'):
                        content_parts.append(f"[{item.type}]")
                return "\n".join(content_parts) if content_parts else str(result)
            return str(result)
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            return f"Error: {str(e)}"


class MCPManager:
    """Manages multiple MCP server connections."""
    
    def __init__(self, config_path: str = "mcp_servers.yaml"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connections: Dict[str, MCPConnection] = {}
        self.logger = logging.getLogger(__name__)
        self._connection_locks: Dict[str, asyncio.Lock] = {}
        
    def load_config(self):
        """Load server configurations from YAML file with validation."""
        if not self.config_path.exists():
            self.logger.warning(f"MCP config file not found: {self.config_path}")
            return
            
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
            # Validate config structure
            if not isinstance(config_data, dict):
                self.logger.error("MCP config must be a dictionary")
                return
                
            if 'servers' not in config_data:
                self.logger.warning("No servers defined in MCP config")
                return
                
            if not isinstance(config_data['servers'], dict):
                self.logger.error("MCP config 'servers' must be a dictionary")
                return
                
            self.servers = {}
            for name, server_config in config_data['servers'].items():
                if not isinstance(server_config, dict):
                    self.logger.warning(f"Skipping invalid server config for '{name}'")
                    continue
                self.servers[name] = MCPServerConfig(name, server_config)
                
            self.logger.info(f"Loaded {len(self.servers)} MCP server configurations")
            
        except Exception as e:
            self.logger.error(f"Error loading MCP config: {e}", exc_info=True)
            
    async def connect_autoconnect_servers(self):
        """Connect to all servers marked with autoconnect=true."""
        if not self.servers:
            self.load_config()
            
        for name, config in self.servers.items():
            if config.autoconnect:
                await self.connect_server(name)
                
    async def connect_server(self, name: str) -> bool:
        """
        Connect to a specific server with race condition protection.
        
        Args:
            name: Server name from config
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.servers:
            self.logger.error(f"Server {name} not found in config")
            return False
        
        # Get or create lock for this server
        if name not in self._connection_locks:
            self._connection_locks[name] = asyncio.Lock()
        
        # Prevent concurrent connection attempts to the same server
        async with self._connection_locks[name]:
            if name in self.connections and self.connections[name].connected:
                self.logger.info(f"Server {name} already connected")
                return True
                
            config = self.servers[name]
            connection = MCPConnection(config)
            
            success = await connection.connect()
            if success:
                self.connections[name] = connection
                
            return success
        
    async def disconnect_server(self, name: str) -> bool:
        """
        Disconnect from a specific server.
        
        Args:
            name: Server name
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.connections:
            self.logger.warning(f"Server {name} not connected")
            return True
            
        success = await self.connections[name].disconnect()
        if success:
            del self.connections[name]
            
        return success
        
    async def reload_config(self):
        """
        Reload configuration and reconnect changed servers.
        
        Disconnects removed servers and reconnects servers with changed configs.
        """
        # Store old config
        old_servers = self.servers.copy()
        
        # Load new config
        self.load_config()
        
        # Disconnect servers that are no longer in config
        for name in list(self.connections.keys()):
            if name not in self.servers:
                self.logger.info(f"Server {name} removed from config, disconnecting")
                await self.disconnect_server(name)
                
        # Reconnect servers that changed or are new autoconnect servers
        for name, config in self.servers.items():
            if config.autoconnect:
                if name not in old_servers or old_servers[name] != config:
                    # Reconnect if config changed
                    if name in self.connections:
                        await self.disconnect_server(name)
                    await self.connect_server(name)
                    
    def get_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all servers.
        
        Returns:
            List of server status information
        """
        status_list = []
        for name, config in self.servers.items():
            connected = name in self.connections and self.connections[name].connected
            tool_count = len(self.connections[name].tools) if connected else 0
            
            status_list.append({
                "name": name,
                "description": config.description,
                "connected": connected,
                "autoconnect": config.autoconnect,
                "tool_count": tool_count
            })
            
        return status_list
        
    def get_all_tools(self, server_filter: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all available tools from connected servers.
        
        Args:
            server_filter: Optional server name to filter by
            
        Returns:
            Dictionary mapping tool names to tool info
        """
        all_tools = {}
        
        for name, connection in self.connections.items():
            if not connection.connected:
                continue
                
            if server_filter and name != server_filter:
                continue
                
            for tool_name, tool in connection.tools.items():
                all_tools[tool_name] = {
                    "server": name,
                    "description": tool.description,
                    "tool": tool
                }
                
        return all_tools
        
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-format schemas for all tools from all connected servers.
        
        Returns:
            List of tool schemas in OpenAI function calling format
        """
        all_schemas = []
        for connection in self.connections.values():
            if connection.connected:
                all_schemas.extend(connection.get_tool_schemas())
        return all_schemas
        
    def _extract_server_name(self, tool_name: str) -> str:
        """
        Extract server name from namespaced tool name.
        
        Args:
            tool_name: Namespaced tool name (mcp_{server}_{tool})
            
        Returns:
            Server name
            
        Raises:
            ValueError: If tool name format is invalid
        """
        if not tool_name.startswith("mcp_"):
            raise ValueError(f"Invalid MCP tool name: {tool_name}")
            
        parts = tool_name.split("_", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid MCP tool name format: {tool_name}")
            
        return parts[1]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the appropriate server.
        
        Args:
            tool_name: Namespaced tool name (mcp_{server}_{tool})
            arguments: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        # Extract server name using helper method
        server_name = self._extract_server_name(tool_name)
        
        if server_name not in self.connections:
            raise RuntimeError(f"Server {server_name} not connected")
            
        return await self.connections[server_name].call_tool(tool_name, arguments)
        
    async def cleanup(self):
        """Disconnect from all servers and cleanup resources."""
        for name in list(self.connections.keys()):
            await self.disconnect_server(name)
            
    @property
    def connected_servers(self) -> list:
        """Return a list of currently connected server names."""
        return [name for name, conn in self.connections.items() if conn.connected]
    
    @property
    def available_tools(self) -> list:
        """Return a list of tools available from all connected servers."""
        tools = []
        for conn in self.connections.values():
            if conn.connected:
                tools.extend(conn.get_tools())
        return tools
