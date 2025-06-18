#!/usr/bin/env python3
"""
FSC data-discovery MCP Server using FastMCP

A lightweight, modular MCP server that provides discovery tools for dbt projects.
Uses FastMCP for simplified server management and type safety.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from loguru import logger

from mcp.server.fastmcp import FastMCP

# Add the src directory to the Python path for absolute imports
server_dir = Path(__file__).parent.parent.parent
src_dir = server_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from data_discovery.api.service import DataDiscoveryService
from data_discovery.resources import resource_registry

# Import FastMCP tool wrappers
from data_discovery.tools.discovery.get_resources import fastmcp_get_resources
from data_discovery.tools.discovery.get_models import fastmcp_get_models
from data_discovery.tools.discovery.get_model_details import fastmcp_get_model_details
from data_discovery.tools.discovery.get_description import fastmcp_get_description


# Configure loguru for MCP server
def setup_logging():
    """Configure loguru for MCP server communication."""
    # Remove default handler to avoid duplicate logs
    logger.remove()

    # Add stderr handler for MCP server communication
    # This ensures logs appear in Claude Desktop's MCP logs
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler for debugging claude desktop spawned MCP server logs
    log_file = Path.home() / ".cache" / "data-discovery" / "claude-server.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
    )


# Global service instance for FastMCP tools
_service_instance: Optional[DataDiscoveryService] = None


def get_service() -> DataDiscoveryService:
    """Get the global service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DataDiscoveryService()
    return _service_instance


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[None]:
    """Manage application lifecycle and dependencies."""
    logger.info("Starting data-discovery server")
    
    # Initialize global service
    global _service_instance
    _service_instance = DataDiscoveryService()
    
    # Debug info at startup
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Deployment mode: {os.getenv('DEPLOYMENT_MODE', 'desktop')}")
    
    try:
        yield
    finally:
        logger.info("Server shutdown completed")
        _service_instance = None


# Initialize FastMCP server
setup_logging()
mcp = FastMCP("data-discovery", lifespan=app_lifespan)


# ========== RESOURCES ==========

@mcp.resource("dbt://projects")
async def dbt_projects_index() -> str:
    """Index of all available dbt projects with metadata."""
    try:
        content = resource_registry.get_resource_content("dbt://projects")
        logger.info("Served dbt projects index resource")
        return content
    except Exception as e:
        logger.error(f"Error reading projects index: {e}")
        raise RuntimeError(f"Failed to read projects index: {str(e)}")


@mcp.resource("dbt://project/{project_id}")
async def dbt_project_resource(project_id: str) -> str:
    """Individual dbt project resource with metadata."""
    try:
        uri = f"dbt://project/{project_id}"
        content = resource_registry.get_resource_content(uri)
        logger.info(f"Served dbt project resource: {project_id}")
        return content
    except Exception as e:
        logger.error(f"Error reading project resource '{project_id}': {e}")
        raise RuntimeError(f"Failed to read project resource: {str(e)}")


# ========== TOOLS ==========

# Register FastMCP tools with proper names and full signatures
get_resources = mcp.tool(name="get_resources")(fastmcp_get_resources)
get_models = mcp.tool(name="get_models")(fastmcp_get_models) 
get_model_details = mcp.tool(name="get_model_details")(fastmcp_get_model_details)
get_description = mcp.tool(name="get_description")(fastmcp_get_description)


# ========== SERVER ENTRY POINT ==========

if __name__ == "__main__":
    # Enable debug logging if requested
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    mcp.run()