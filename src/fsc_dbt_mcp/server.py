#!/usr/bin/env python3
"""
FSC dbt MCP Server

A comprehensive MCP server that provides both core dbt functionality 
and custom discovery tools for dbt projects.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from pydantic import AnyUrl

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp import stdio_server, types
from mcp.types import TextContent

# Add the src directory to the Python path for absolute imports
server_dir = Path(__file__).parent.parent.parent
src_dir = server_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fsc_dbt_mcp.tools.discovery import get_model_details_tool, handle_get_model_details, get_description_tool, handle_get_description, get_models_tool, handle_get_models, get_resources_tool, handle_get_resources
from fsc_dbt_mcp.tools.dbt_cli import get_dbt_cli_tools, handle_dbt_cli_tool, is_dbt_cli_tool
from fsc_dbt_mcp.resources import resource_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServerConfig:
    """Server configuration management."""
    
    def __init__(self):
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.deployment_mode = os.getenv('DEPLOYMENT_MODE', 'desktop').lower()
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
        
    def validate(self):
        """Validate configuration settings."""
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)


def create_server() -> Server:
    """Create a comprehensive MCP server with discovery functionality."""
    config = ServerConfig()
    config.validate()
    
    server = Server("fsc-dbt-mcp")
    
    @server.list_resources()
    async def list_resources() -> List[types.Resource]:
        """List available MCP resources for dbt projects."""
        try:
            resources = resource_registry.list_all_resources()
            logger.info(f"Listed {len(resources)} MCP resources")
            return resources
        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            raise RuntimeError(f"Failed to list resources: {str(e)}")
    
    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> str:
        """Read MCP resource content for dbt projects."""
        try:
            uri_str = str(uri)
            logger.info(f"Reading resource: {uri_str}")
            
            content = resource_registry.get_resource_content(uri_str)
            return content
                
        except Exception as e:
            logger.error(f"Error reading resource '{uri}': {e}")
            raise RuntimeError(f"Failed to read resource: {str(e)}")
    
    @server.list_tools()
    async def list_tools():
        """List available discovery and dbt CLI tools."""
        try:
            tools = []
            
            # Add custom discovery tools
            tools.append(get_model_details_tool())
            tools.append(get_description_tool())
            tools.append(get_models_tool())
            tools.append(get_resources_tool())
            
            # Add dbt CLI tools
            # dbt_tools = get_dbt_cli_tools()
            # tools.extend(dbt_tools)

            # disable dbt tools for now as they have not been migrated to multi-project
            dbt_tools = []
            
            logger.info(f"Listed {len(tools)} total tools ({len(dbt_tools)} dbt CLI tools)")
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            raise RuntimeError(f"Failed to list tools: {str(e)}")
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls with comprehensive error handling."""
        logger.debug(f"[SERVER] call_tool invoked - name='{name}', arguments={arguments}")
        
        try:
            # Input validation
            if not name:
                logger.debug(f"[SERVER] Tool name validation failed - empty name")
                raise ValueError("Tool name cannot be empty")
            
            if not isinstance(arguments, dict):
                logger.debug(f"[SERVER] Arguments validation failed - not dict: {type(arguments)}")
                raise ValueError("Arguments must be a dictionary")
            
            logger.debug(f"[SERVER] Input validation passed for tool '{name}'")
            
            # Route to appropriate tool handler
            logger.debug(f"[SERVER] Routing to tool handler for '{name}'")
            
            if name == "get_model_details":
                logger.debug(f"[SERVER] Calling handle_get_model_details with args: {arguments}")
                return await handle_get_model_details(arguments)
            elif name == "get_description":
                logger.debug(f"[SERVER] Calling handle_get_description with args: {arguments}")
                return await handle_get_description(arguments)
            elif name == "get_models":
                logger.debug(f"[SERVER] Calling handle_get_models with args: {arguments}")
                return await handle_get_models(arguments)
            elif name == "get_resources":
                logger.debug(f"[SERVER] Calling handle_get_resources with args: {arguments}")
                return await handle_get_resources(arguments)
            elif is_dbt_cli_tool(name):
                logger.debug(f"[SERVER] Calling dbt CLI tool handler for '{name}' with args: {arguments}")
                return await handle_dbt_cli_tool(name, arguments)
            else:
                logger.debug(f"[SERVER] Unknown tool name: '{name}'")
                raise ValueError(f"Unknown tool: {name}")
                
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"[SERVER] Error in tool '{name}': {e}")
            raise
        except Exception as e:
            logger.error(f"[SERVER] Unexpected error in tool '{name}': {e}")
            raise RuntimeError(f"Internal error: {str(e)}")
    
    return server


async def main() -> int:
    """Main entry point for the FSC dbt MCP server."""
    try:
        logger.info("Starting data-discovery server")
        
        # Create and configure server
        server = create_server()
        
        # Initialize server options
        init_options = InitializationOptions(
            server_name="data-discovery",
            server_version="0.2.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )
        
        # Run the server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, init_options)
        
        logger.info("Server shutdown completed")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        return 0
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
