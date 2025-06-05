#!/usr/bin/env python3
"""
Custom dbt MCP Server - Core Tools Only

A lightweight wrapper around dbt-mcp that enables only Core functionality.
"""

import asyncio
import os
import logging
from dbt_mcp.main import create_dbt_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the custom dbt MCP server."""
    try:
        # Configure environment for Core-only tools
        os.environ.update({
            'DISABLE_SEMANTIC_LAYER': 'true',
            'DISABLE_DISCOVERY': 'true', 
            'DISABLE_REMOTE': 'true'
        })
        
        # Validate required environment variable
        if not os.getenv('DBT_PROJECT_DIR'):
            logger.error("DBT_PROJECT_DIR environment variable is required")
            return 1
        
        logger.info("Starting custom dbt MCP server with Core tools only")
        logger.info(f"Using dbt project: {os.getenv('DBT_PROJECT_DIR')}")
        
        # Create and run the dbt MCP server
        server = create_dbt_mcp()
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))