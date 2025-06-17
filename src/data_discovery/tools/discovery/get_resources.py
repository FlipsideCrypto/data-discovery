"""
get_resources tool for listing all available dbt project resources.
Provides discovery of blockchain projects available for analysis.
"""
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
from loguru import logger

from data_discovery.prompts import get_prompt
from data_discovery.api.service import DataDiscoveryService
from .utils import create_no_artifacts_error
from .properties import ToolPropertySet, SHOW_DETAILS, BLOCKCHAIN_FILTER, CATEGORY_FILTER

# Define tool properties
_tool_properties = ToolPropertySet({
    "show_details": SHOW_DETAILS,
    "blockchain_filter": BLOCKCHAIN_FILTER,
    "category_filter": CATEGORY_FILTER
})


def get_resources_tool() -> Tool:
    """Tool definition for get_resources."""
    return Tool(
        name="get_resources",
        description=get_prompt("discovery/get_resources"),
        inputSchema=_tool_properties.get_input_schema()
    )




async def handle_get_resources(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_resources tool invocation using shared service."""
    try:
        # Validate and extract all arguments using properties
        logger.debug(f"[GET_RESOURCES] Called with arguments: {arguments}")
        params = _tool_properties.validate_and_extract_all(arguments)
        show_details = params["show_details"]
        blockchain_filter = params["blockchain_filter"]
        category_filter = params["category_filter"]
        logger.debug(f"[GET_RESOURCES] Extracted params - show_details: {show_details}, blockchain_filter: {blockchain_filter}, category_filter: {category_filter}")
        
        # Use shared service to get resources
        service = DataDiscoveryService()
        result = await service.get_resources(
            show_details=show_details,
            blockchain_filter=blockchain_filter,
            category_filter=category_filter
        )
        
        # Handle error case
        if result.get("error"):
            logger.debug(f"[GET_RESOURCES] Service returned error: {result['error']}")
            return [TextContent(
                type="text",
                text=result["error"],
                isError=True
            )]
        
        # Convert service result to MCP TextContent format
        return _convert_resources_to_mcp_format(result)
        
    except Exception as e:
        logger.error(f"Unexpected error in get_resources: {e}")
        return [TextContent(
            type="text",
            text="Internal error retrieving resources",
            isError=True
        )]


def _convert_resources_to_mcp_format(result: Dict[str, Any]) -> list[TextContent]:
    """Convert shared service result to MCP TextContent format."""
    response_lines = ["# Available dbt Resources"]
    
    # Add filter information
    filters_applied = result.get("filters_applied", {})
    filter_info = []
    if filters_applied.get("blockchain_filter"):
        filter_info.append(f"blockchain='{filters_applied['blockchain_filter']}'")
    if filters_applied.get("category_filter"):
        filter_info.append(f"category='{filters_applied['category_filter']}'")
    
    if filter_info:
        response_lines.append(f"**Filters:** {', '.join(filter_info)}")
    
    # Add partial match suggestions if any
    partial_suggestions = result.get("partial_match_suggestions", [])
    if partial_suggestions:
        if len(partial_suggestions) <= 3:
            suggestions_text = "', '".join(partial_suggestions)
            response_lines.append(f"**Note:** Partial match found. Did you mean '{suggestions_text}'?")
        else:
            suggestions_text = "', '".join(partial_suggestions[:3])
            response_lines.append(f"**Note:** Partial match found ({len(partial_suggestions)} matches). Did you mean '{suggestions_text}' or others?")
    
    response_lines.extend([
        f"**Found:** {result['filtered_count']} of {result['total_count']} total resources",
        ""
    ])
    
    resources = result.get("resources", [])
    if not resources:
        response_lines.append("No resources match the specified filters.")
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    # Group by blockchain for better organization
    resources_by_blockchain = {}
    for resource in resources:
        blockchain = resource.get("blockchain", "unknown")
        if blockchain not in resources_by_blockchain:
            resources_by_blockchain[blockchain] = []
        resources_by_blockchain[blockchain].append(resource)
    
    # Format output
    for blockchain in sorted(resources_by_blockchain.keys()):
        blockchain_resources = resources_by_blockchain[blockchain]
        
        response_lines.extend([
            f"## {blockchain.title()} Blockchain",
            f"**Resources:** {len(blockchain_resources)}",
            ""
        ])
        
        show_details = filters_applied.get("show_details", False)
        for resource in blockchain_resources:
            if show_details:
                response_lines.extend(_format_resource_detailed_mcp(resource))
            else:
                response_lines.extend(_format_resource_summary_mcp(resource))
    
    # Add usage hints
    response_lines.extend([
        "---",
        "",
        "**Usage Tips:**",
        "- Use resource IDs or aliases in other tools (e.g., `get_models(resource_id=\"ethereum-models\")`)",
        "- Use `show_details=true` for comprehensive information including schemas and URLs",
        "- Filter by blockchain or category to focus on specific ecosystems (e.g., EVM, L1, SVM)"
    ])
    
    return [TextContent(type="text", text="\n".join(response_lines))]


def _format_resource_summary_mcp(resource: Dict[str, Any]) -> List[str]:
    """Format a resource for summary display in MCP format."""
    lines = [f"### {resource['name']}"]
    lines.append(f"**ID:** {resource['id']}")
    lines.append(f"**Blockchain:** {resource['blockchain']}")
    lines.append(f"**Category:** {resource.get('category', 'N/A')}")
    
    if resource.get('description'):
        lines.append(f"**Description:** {resource['description']}")
    
    lines.append("")
    return lines


def _format_resource_detailed_mcp(resource: Dict[str, Any]) -> List[str]:
    """Format a resource for detailed display in MCP format."""
    lines = [f"### {resource['name']}"]
    lines.append(f"**ID:** {resource['id']}")
    lines.append(f"**Blockchain:** {resource['blockchain']}")
    lines.append(f"**Category:** {resource.get('category', 'N/A')}")
    lines.append(f"**Location:** {resource.get('location', 'N/A')}")
    
    if resource.get('description'):
        lines.append(f"**Description:** {resource['description']}")
    
    # Show aliases
    aliases = resource.get('aliases', [])
    if aliases:
        lines.append(f"**Aliases:** {', '.join(aliases)}")
    
    # Show schemas
    schemas = resource.get('schemas', [])
    if schemas:
        lines.append(f"**Schemas:** {', '.join(schemas)}")
    
    # Show artifact location for GitHub projects
    if resource.get('artifact_location'):
        artifact_location = resource['artifact_location']
        lines.append(f"**Manifest URL:** {artifact_location.get('manifest', 'N/A')}")
        if resource.get('target_branch'):
            lines.append(f"**Branch:** {resource['target_branch']}")
    
    lines.append("")
    return lines