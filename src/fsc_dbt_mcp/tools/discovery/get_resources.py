"""
get_resources tool for listing all available dbt project resources.
Provides discovery of blockchain projects available for analysis.
"""
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
import logging

from fsc_dbt_mcp.prompts import get_prompt
from .utils import create_no_artifacts_error
from .properties import ToolPropertySet, SHOW_DETAILS, BLOCKCHAIN_FILTER, CATEGORY_FILTER

logger = logging.getLogger(__name__)

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


def _analyze_blockchain_matches(resources: List[Dict[str, Any]], blockchain_filter: str) -> tuple[List[Dict[str, Any]], bool, List[str]]:
    """Analyze blockchain matches and determine if it's a partial match.
    
    Returns:
        - filtered_resources: List of matching resources
        - is_partial_match: True if multiple resources matched a partial filter 
        - exact_matches: List of exact blockchain names/aliases that would be more specific
    """
    blockchain_filter = blockchain_filter.lower()
    matches = []
    exact_matches = set()
    
    for resource in resources:
        resource_matches = False
        
        # Check main blockchain name
        blockchain = resource.get("blockchain", "").lower()
        if blockchain_filter in blockchain:
            resource_matches = True
            # Check if it's an exact match
            if blockchain_filter == blockchain:
                exact_matches.add(blockchain)
        
        # Check aliases
        aliases = resource.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str):
                    alias_lower = alias.lower()
                    if blockchain_filter in alias_lower:
                        resource_matches = True
                        # Check if it's an exact match
                        if blockchain_filter == alias_lower:
                            exact_matches.add(alias_lower)
        
        if resource_matches:
            matches.append(resource)
    
    # Determine if this is a partial match (multiple matches but no exact matches)
    is_partial_match = len(matches) > 1 and len(exact_matches) == 0
    
    # Get resource IDs from matched resources for suggestions
    suggested_terms = []
    if is_partial_match:
        for resource in matches:
            resource_id = resource.get("id", "")
            if resource_id and resource_id not in suggested_terms:
                suggested_terms.append(resource_id)
    
    return matches, is_partial_match, suggested_terms


def _filter_resources(resources: List[Dict[str, Any]], blockchain_filter: str = None, category_filter: str = None) -> tuple[List[Dict[str, Any]], bool, List[str]]:
    """Filter resources based on blockchain and category criteria.
    
    Returns:
        - filtered_resources: List of matching resources
        - is_partial_blockchain_match: True if blockchain filter had multiple partial matches
        - blockchain_suggestions: List of more specific terms if partial match detected
    """
    filtered = resources
    is_partial_blockchain_match = False
    blockchain_suggestions = []
    
    if blockchain_filter:
        filtered, is_partial_blockchain_match, blockchain_suggestions = _analyze_blockchain_matches(filtered, blockchain_filter)
    
    if category_filter:
        category_filter = category_filter.lower()
        filtered = [r for r in filtered if category_filter in r.get("category", "").lower()]
    
    return filtered, is_partial_blockchain_match, blockchain_suggestions


def _format_resource_summary(resource: Dict[str, Any]) -> List[str]:
    """Format a resource for summary display."""
    lines = [f"### {resource['name']}"]
    lines.append(f"**ID:** {resource['id']}")
    lines.append(f"**Blockchain:** {resource['blockchain']}")
    lines.append(f"**Category:** {resource.get('category', 'N/A')}")
    
    if resource.get('description'):
        lines.append(f"**Description:** {resource['description']}")
    
    lines.append("")
    return lines


def _format_resource_detailed(resource: Dict[str, Any]) -> List[str]:
    """Format a resource for detailed display."""
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


async def handle_get_resources(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_resources tool invocation."""
    try:
        # Validate and extract all arguments using properties
        logger.debug(f"[GET_RESOURCES] Called with arguments: {arguments}")
        params = _tool_properties.validate_and_extract_all(arguments)
        show_details = params["show_details"]
        blockchain_filter = params["blockchain_filter"]
        category_filter = params["category_filter"]
        logger.debug(f"[GET_RESOURCES] Extracted params - show_details: {show_details}, blockchain_filter: {blockchain_filter}, category_filter: {category_filter}")
        
        # Get all available resources from project manager
        try:
            # Get a list of all project IDs and fetch their data
            from fsc_dbt_mcp.resources import resource_registry
            project_ids = resource_registry.list_project_ids()
            
            if not project_ids:
                logger.debug(f"[GET_RESOURCES] No project IDs found")
                return create_no_artifacts_error()
            
            # Get detailed data for each project
            all_resources = []
            for project_id in project_ids:
                try:
                    project_data = resource_registry.get_project_by_id(project_id)
                    all_resources.append(project_data)
                except Exception as e:
                    logger.warning(f"Failed to load project {project_id}: {e}")
                    continue
            
            if not all_resources:
                logger.debug(f"[GET_RESOURCES] No resources loaded successfully")
                return create_no_artifacts_error()
            
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")
            logger.debug(f"[GET_RESOURCES] Resource loading failed: {e}")
            return [TextContent(
                type="text",
                text="Failed to load available resources"
            )]
        
        # Apply filters
        logger.debug(f"[GET_RESOURCES] Applying filters to {len(all_resources)} resources")
        filtered_resources, is_partial_blockchain_match, blockchain_suggestions = _filter_resources(all_resources, blockchain_filter, category_filter)
        logger.debug(f"[GET_RESOURCES] Filtered to {len(filtered_resources)} resources")
        
        # Build response
        response_lines = ["# Available dbt Resources"]
        
        # Add filter information
        filter_info = []
        if blockchain_filter:
            filter_info.append(f"blockchain='{blockchain_filter}'")
        if category_filter:
            filter_info.append(f"category='{category_filter}'")
        
        if filter_info:
            response_lines.append(f"**Filters:** {', '.join(filter_info)}")
        
        # Add partial match suggestion if detected
        if is_partial_blockchain_match and blockchain_suggestions:
            if len(blockchain_suggestions) <= 3:
                suggestions_text = "', '".join(blockchain_suggestions)
                response_lines.append(f"**Note:** Partial match found. Did you mean '{suggestions_text}'?")
            else:
                suggestions_text = "', '".join(blockchain_suggestions[:3])
                response_lines.append(f"**Note:** Partial match found ({len(blockchain_suggestions)} matches). Did you mean '{suggestions_text}' or others?")
        
        response_lines.extend([
            f"**Found:** {len(filtered_resources)} of {len(all_resources)} total resources",
            ""
        ])
        
        if not filtered_resources:
            response_lines.append("No resources match the specified filters.")
            return [TextContent(type="text", text="\n".join(response_lines))]
        
        # Sort resources by blockchain then name
        sorted_resources = sorted(filtered_resources, key=lambda x: (x.get("blockchain", ""), x.get("name", "")))
        
        # Group by blockchain for better organization
        resources_by_blockchain = {}
        for resource in sorted_resources:
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
            
            for resource in blockchain_resources:
                if show_details:
                    response_lines.extend(_format_resource_detailed(resource))
                else:
                    response_lines.extend(_format_resource_summary(resource))
        
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
        
    except Exception as e:
        logger.error(f"Unexpected error in get_resources: {e}")
        return [TextContent(
            type="text",
            text="Internal error retrieving resources"
        )]