"""
Shared utilities for discovery tools.

Provides common functions for error message generation and resource management.
"""
from typing import List
from mcp.types import TextContent
from loguru import logger




def get_available_resources() -> List[str]:
    """Get list of available resource IDs from resource registry."""
    from data_discovery.resources import resource_registry
    return resource_registry.list_project_ids()


def create_error_response(message: str, include_available_resources: bool = True) -> list[TextContent]:
    """Create a standardized error response with optional available resources list."""
    logger.debug(f"[UTILS] create_error_response called with message: {message}, include_resources: {include_available_resources}")
    
    if include_available_resources:
        available_resources = get_available_resources()
        full_message = f"{message}. Available resources: {available_resources}"
        logger.debug(f"[UTILS] Added available resources to message")
    else:
        full_message = message
    
    result = [TextContent(type="text", text=full_message, isError=True)]
    logger.debug(f"[UTILS] create_error_response returning: {type(result)} with {len(result)} items")
    return result


def create_resource_not_found_error(identifier: str, resource_info: str = "", 
                                  item_type: str = "item") -> list[TextContent]:
    """Create a standardized 'not found' error with available resources."""
    available_resources = get_available_resources()
    resource_suffix = resource_info if resource_info else " in any available resources"
    message = f"{item_type.title()} '{identifier}' not found{resource_suffix}. Available resources: {available_resources}"
    return [TextContent(type="text", text=message, isError=True)]


def create_no_artifacts_error() -> list[TextContent]:
    """Create a standardized 'no artifacts loaded' error with available resources."""
    return create_error_response("No resource artifacts could be loaded")

