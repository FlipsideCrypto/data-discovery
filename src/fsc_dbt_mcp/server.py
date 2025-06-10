#!/usr/bin/env python3
"""
FSC dbt MCP Server

A comprehensive MCP server that provides both core dbt functionality 
and custom discovery tools for dbt projects.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp import stdio_server
from mcp.types import TextContent

# Add the src directory to the Python path for absolute imports
server_dir = Path(__file__).parent.parent.parent
src_dir = server_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fsc_dbt_mcp.tools.discovery import get_model_details_tool, handle_get_model_details, get_description_tool, handle_get_description, get_models_tool, handle_get_models
from fsc_dbt_mcp.tools.dbt_cli import get_dbt_cli_tools, handle_dbt_cli_tool, is_dbt_cli_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServerConfig:
    """Server configuration management following MCP best practices."""
    
    def __init__(self):
        self.project_dir = os.getenv('DBT_PROJECT_DIR', os.getcwd())
        self.debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
        
    def validate(self):
        """Validate configuration settings."""
        project_path = Path(self.project_dir)
        if not project_path.exists():
            logger.warning(f"DBT project directory does not exist: {self.project_dir}")
        
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)


def create_server() -> Server:
    """Create a comprehensive MCP server with discovery functionality."""
    config = ServerConfig()
    config.validate()
    
    server = Server("fsc-dbt-mcp")
    
    @server.list_tools()
    async def list_tools():
        """List available discovery and dbt CLI tools."""
        try:
            tools = []
            
            # Add custom discovery tools
            tools.append(get_model_details_tool())
            tools.append(get_description_tool())
            tools.append(get_models_tool())
            
            # Add dbt CLI tools
            dbt_tools = get_dbt_cli_tools()
            tools.extend(dbt_tools)
            
            logger.info(f"Listed {len(tools)} total tools ({len(dbt_tools)} dbt CLI tools)")
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            raise RuntimeError(f"Failed to list tools: {str(e)}")
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls with comprehensive error handling."""
        try:
            # Input validation
            if not name:
                raise ValueError("Tool name cannot be empty")
            
            if not isinstance(arguments, dict):
                raise ValueError("Arguments must be a dictionary")
            
            # Route to appropriate tool handler
            if name == "get_model_details":
                return await handle_get_model_details(arguments)
            elif name == "get_description":
                return await handle_get_description(arguments)
            elif name == "get_models":
                return await handle_get_models(arguments)
            elif is_dbt_cli_tool(name):
                return await handle_dbt_cli_tool(name, arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Error in tool '{name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in tool '{name}': {e}")
            raise RuntimeError(f"Internal error: {str(e)}")
    
    return server


async def main() -> int:
    """Main entry point for the FSC dbt MCP server."""
    try:
        logger.info("Starting FSC dbt MCP server")
        
        # Create and configure server
        server = create_server()
        
        # Initialize server options
        init_options = InitializationOptions(
            server_name="fsc-dbt-mcp",
            server_version="0.1.0",
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