"""
get_model_details tool for dbt model exploration and metadata retrieval.

Follows MCP best practices for input validation, error handling, and security.
Supports multi-project operations with project-aware functionality.
"""
import json
from typing import Dict, Any, Optional, Tuple
from mcp.types import Tool, TextContent
from loguru import logger

from data_discovery.prompts import get_prompt
from data_discovery.api.service import DataDiscoveryService
from .properties import ToolPropertySet, UNIQUE_ID, MODEL_NAME, TABLE_NAME, FQN, STANDARD_RESOURCE_ID

# Define tool properties
_tool_properties = ToolPropertySet({
    "uniqueId": UNIQUE_ID,
    "model_name": MODEL_NAME,
    "table_name": TABLE_NAME,
    "fqn": FQN,
    "resource_id": STANDARD_RESOURCE_ID
})


def get_model_details_tool() -> Tool:
    """Tool definition for get_model_details."""
    return Tool(
        name="get_model_details",
        description=get_prompt("discovery/get_model_details"),
        inputSchema=_tool_properties.get_input_schema(
            one_of_groups=[
                ["uniqueId"],
                ["model_name"],
                ["table_name"],
                ["fqn"]
            ]
        )
    )


def _validate_model_arguments(arguments: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[Any]]:
    """Validate and extract model identification arguments."""
    logger.debug(f"[GET_MODEL] _validate_model_arguments called with: {arguments}")
    
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a dictionary")
    
    # Validate and extract all arguments using properties
    params = _tool_properties.validate_and_extract_all(arguments)
    
    unique_id = params["uniqueId"]
    model_name = params["model_name"]
    table_name = params["table_name"]
    fqn = params["fqn"]
    resource_id = params["resource_id"]
    
    logger.debug(f"[GET_MODEL] Extracted params - unique_id: {unique_id}, model_name: {model_name}, table_name: {table_name}, fqn: {fqn}, resource_id: {resource_id}")
    
    # Input sanitization and validation for unique_id format
    if unique_id is not None and not unique_id.startswith("model."):
        raise ValueError("uniqueId must start with 'model.'")
    
    # Ensure at least one identifier is provided
    if not unique_id and not model_name and not table_name and not fqn:
        raise ValueError("Either uniqueId, model_name, table_name, or fqn must be provided")
    
    return unique_id, model_name, table_name, fqn, resource_id




async def handle_get_model_details(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_model_details tool invocation using shared service."""
    try:
        # Validate input arguments
        logger.debug(f"[GET_MODEL] Called with arguments: {arguments}")
        unique_id, model_name, table_name, fqn, resource_id = _validate_model_arguments(arguments)
        
        # Use shared service to get model details
        service = DataDiscoveryService()
        result = await service.get_model_by_id(
            unique_id=unique_id,
            model_name=model_name,
            table_name=table_name,
            fqn=fqn,
            resource_id=resource_id
        )
        
        # Handle error case
        if result.get("error"):
            logger.debug(f"[GET_MODEL] Service returned error: {result['error']}")
            return [TextContent(
                type="text",
                text=result["error"],
                isError=True
            )]
        
        # Handle multiple matches case
        if result.get("multiple_matches"):
            response_lines = [
                result["message"],
                ""
            ]
            for i, match in enumerate(result["matches"], 1):
                response_lines.extend([
                    f"{i}. **Project:** {match['resource_id']}",
                    f"   **Unique ID:** {match['unique_id']}",
                    f"   **Schema:** {match.get('schema', 'N/A')}",
                    f"   **Database:** {match.get('database', 'N/A')}",
                    ""
                ])
            
            response_lines.append("Please use the specific uniqueId to get details for the desired model.")
            return [TextContent(type="text", text="\n".join(response_lines))]
        
        # Convert service result to MCP TextContent format
        return _convert_model_details_to_mcp_format(result)
        
    except ValueError as e:
        logger.error(f"Invalid input in get_model_details: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}",
            isError=True
        )]
    except Exception as e:
        logger.error(f"Unexpected error in get_model_details: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving model details: {str(e)}",
            isError=True
        )]


def _convert_model_details_to_mcp_format(model_details: Dict[str, Any]) -> list[TextContent]:
    """Convert shared service model details to MCP TextContent format."""
    try:
        # Format the response
        response_lines = [
            f"# Model Details: {model_details['name']}",
            f"**Project:** {model_details['resource_id']}",
            f"**Unique ID:** {model_details['unique_id']}",
            f"**Database:** {model_details['database']}",
            f"**Schema:** {model_details['schema']}",
            f"**Relation Name:** {model_details['relation_name']}",
            f"**File Path:** {model_details['path']}",
            f"**Materialization:** {model_details['materialized']}",
            ""
        ]
        
        if model_details.get("description"):
            response_lines.extend([
                "## Description",
                model_details["description"],
                ""
            ])
        
        if model_details.get("tags"):
            response_lines.extend([
                "## Tags",
                ", ".join(model_details["tags"]),
                ""
            ])
        
        if model_details.get("meta"):
            response_lines.extend([
                "## Meta",
                json.dumps(model_details["meta"], indent=2),
                ""
            ])
        
        # Columns section
        columns = model_details.get("columns", {})
        if columns:
            response_lines.extend([
                "## Columns",
                ""
            ])
            
            for col_name, col_info in sorted(columns.items(), key=lambda x: x[1].get("index", 999)):
                response_lines.append(f"### {col_name}")
                if col_info.get("type"):
                    response_lines.append(f"**Type:** {col_info['type']}")
                if col_info.get("description"):
                    response_lines.append(f"**Description:** {col_info['description']}")
                if col_info.get("comment"):
                    response_lines.append(f"**Comment:** {col_info['comment']}")
                if col_info.get("tags"):
                    response_lines.append(f"**Tags:** {', '.join(col_info['tags'])}")
                if col_info.get("constraints"):
                    response_lines.append(f"**Constraints:** {', '.join(col_info['constraints'])}")
                response_lines.append("")
        
        # Dependencies section
        if model_details.get("refs") or model_details.get("sources"):
            response_lines.extend([
                "## Dependencies",
                ""
            ])
            
            if model_details.get("refs"):
                response_lines.extend([
                    "**Models Referenced:**",
                    ""
                ])
                for ref in model_details["refs"]:
                    response_lines.append(f"- {'.'.join(ref) if isinstance(ref, list) else ref}")
                response_lines.append("")
            
            if model_details.get("sources"):
                response_lines.extend([
                    "**Sources Referenced:**",
                    ""
                ])
                for source in model_details["sources"]:
                    response_lines.append(f"- {'.'.join(source) if isinstance(source, list) else source}")
                response_lines.append("")
        
        # Statistics section (from catalog)
        if model_details.get("stats"):
            response_lines.extend([
                "## Statistics",
                ""
            ])
            stats = model_details["stats"]
            for stat_name, stat_info in stats.items():
                if isinstance(stat_info, dict) and stat_info.get("include", True):
                    label = stat_info.get("label", stat_name)
                    value = stat_info.get("value", "N/A")
                    response_lines.append(f"**{label}:** {value}")
            response_lines.append("")
        
        # Raw SQL section
        if model_details.get("raw_code"):
            response_lines.extend([
                "## Raw SQL",
                "",
                "```sql",
                model_details["raw_code"],
                "```",
                ""
            ])
        
        # Compiled SQL section (if different from raw)
        if (model_details.get("compiled_code") and 
            model_details["compiled_code"] != model_details.get("raw_code")):
            response_lines.extend([
                "## Compiled SQL",
                "",
                "```sql",
                model_details["compiled_code"],
                "```"
            ])
        
        return [TextContent(type="text", text="\n".join(response_lines))]
        
    except Exception as e:
        logger.error(f"Error formatting model details response: {e}")
        return [TextContent(
            type="text",
            text=f"Error formatting model details: {str(e)}"
        )]
