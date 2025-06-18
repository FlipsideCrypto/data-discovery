"""
get_description tool for retrieving documentation blocks from dbt manifest.

Follows MCP best practices for input validation, error handling, and security.
Supports multi-project operations with project-aware functionality.
"""
from typing import Dict, Any, Union, List
from mcp.types import Tool, TextContent
from pydantic import Field
from loguru import logger

from data_discovery.prompts import get_prompt
from data_discovery.api.service import DataDiscoveryService
from .properties import ToolPropertySet, DOC_NAME, REQUIRED_RESOURCE_ID

# Define tool properties
_tool_properties = ToolPropertySet({
    "doc_name": DOC_NAME,
    "resource_id": REQUIRED_RESOURCE_ID
})


def get_description_tool() -> Tool:
    """Tool definition for get_description."""
    return Tool(
        name="get_description",
        description=get_prompt("discovery/get_description"),
        inputSchema=_tool_properties.get_input_schema(required_properties=["resource_id"])
    )


async def handle_get_description(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_description tool invocation using shared service."""
    try:
        # Validate and extract all arguments using properties
        logger.debug(f"[GET_DESC] Called with arguments: {arguments}")
        params = _tool_properties.validate_and_extract_all(arguments)
        doc_name = params["doc_name"]
        resource_id = params["resource_id"]
        logger.debug(f"[GET_DESC] Extracted params - doc_name: {doc_name}, resource_id: {resource_id}")
        
        # Use shared service to get description
        service = DataDiscoveryService()
        result = await service.get_description(
            doc_name=doc_name,
            resource_id=resource_id
        )
        
        # Handle error case
        if result.get("error"):
            logger.debug(f"[GET_DESC] Service returned error: {result['error']}")
            return [TextContent(
                type="text",
                text=result["error"],
                isError=True
            )]
        
        # Convert service result to MCP TextContent format
        return _convert_description_to_mcp_format(result)
        
    except ValueError as e:
        logger.error(f"Invalid input in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}",
            isError=True
        )]
    except Exception as e:
        logger.error(f"Unexpected error in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving description: {str(e)}",
            isError=True
        )]


# FastMCP-compatible wrapper function
async def fastmcp_get_description(
    resource_id: Union[str, List[str]] = Field(
        description="Resource ID(s) to search in. Required to avoid cross-contamination of blockchain-specific documentation."
    ),
    doc_name: str = Field(
        default="__overview__",
        description="Name of the documentation block to retrieve"
    )
) -> str:
    """
    FastMCP wrapper for get_description tool.
    Retrieve documentation blocks from dbt manifest.
    Follows MCP best practices for input validation, error handling, and security.
    """
    try:
        logger.debug(f"get_description called with doc_name={doc_name}, resource_id={resource_id}")
        
        service = DataDiscoveryService()
        result = await service.get_description(
            doc_name=doc_name,
            resource_id=resource_id
        )
        
        if result.get("error"):
            logger.error(f"Service error in get_description: {result['error']}")
            raise RuntimeError(result["error"])
        
        # Convert service result to formatted text
        text_result = _convert_description_to_mcp_format(result)
        return text_result[0].text if text_result else "Documentation not found"
        
    except Exception as e:
        logger.error(f"Error in get_description: {e}")
        raise RuntimeError(f"Internal error retrieving description: {str(e)}")


def _convert_description_to_mcp_format(result: Dict[str, Any]) -> list[TextContent]:
    """Convert shared service description result to MCP TextContent format."""
    doc_name = result["doc_name"]
    matches = result.get("matches", [])
    total_matches = result.get("total_matches", 0)
    
    # Format response for all matching docs
    response_lines = [
        f"# Documentation: {doc_name}",
        ""
    ]
    
    if total_matches > 1:
        response_lines.append(f"Found {total_matches} documentation blocks across projects:")
        response_lines.append("")
    
    for match in matches:
        response_lines.extend([
            f"## Project: {match['project_id']}",
            f"**Package:** {match['package_name']}",
            f"**Document ID:** {match['doc_id']}",
            f"**Path:** {match['path']}",
            ""
        ])
        
        # Add the actual content
        content = match.get("content", "")
        if content:
            response_lines.extend([
                "### Content",
                "",
                content,
                "",
                "---",
                ""
            ])
        else:
            response_lines.extend([
                "*No content available*",
                "",
                "---",
                ""
            ])
    
    return [TextContent(type="text", text="\n".join(response_lines))]
