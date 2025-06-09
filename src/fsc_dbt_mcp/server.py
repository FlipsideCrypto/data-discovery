#!/usr/bin/env python3
"""
Custom dbt MCP Server - Discovery Tools

A standalone MCP server that provides discovery tools for dbt projects.
Run this alongside dbt-mcp to get both core dbt functionality and discovery tools.
"""

import asyncio
import logging
from typing import Any, Dict
from mcp.server import Server
from mcp import stdio_server
from fsc_dbt_mcp.tools.discovery import get_model_details_tool, handle_get_model_details

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_discovery_server() -> Server:
    """Create a MCP server with discovery functionality for dbt projects."""
    server = Server("fsc-dbt-discovery")
    
    @server.list_tools()
    async def list_tools():
        """List available discovery tools."""
        return [get_model_details_tool()]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        """Handle tool calls for discovery tools."""
        if name == "get_model_details":
            return await handle_get_model_details(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    return server


async def main():
    """Main entry point for the discovery MCP server."""
    try:        
        logger.info("Starting dbt discovery MCP server")
        
        # Create and run the discovery server
        server = create_discovery_server()
        
        # Run the server using stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))