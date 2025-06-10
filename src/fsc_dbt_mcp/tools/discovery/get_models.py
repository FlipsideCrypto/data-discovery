"""
get_models tool for retrieving dbt models with filtering by schema or medallion level.
"""
from typing import Dict, Any, List, Optional
from mcp.types import Tool, TextContent
import logging

from fsc_dbt_mcp.prompts import get_prompt
from .utils import load_dbt_artifacts

logger = logging.getLogger(__name__)


def get_models_tool() -> Tool:
    """Tool definition for get_models."""
    return Tool(
        name="get_models",
        description=get_prompt("discovery/get_models"),
        inputSchema={
            "type": "object",
            "properties": {
                "schema": {
                    "type": "string",
                    "description": "Filter models by schema name (e.g., 'core', 'defi', 'nft'). Takes precedence over level if both are provided."
                },
                "level": {
                    "type": "string",
                    "description": "Filter models by medallion level (bronze, silver, gold). Ignored if schema is provided.",
                    "enum": ["bronze", "silver", "gold"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of models to return (default: 10, max: 200)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 200
                }
            },
            "additionalProperties": False
        }
    )


def _validate_models_arguments(arguments: Dict[str, Any]) -> tuple[Optional[str], Optional[str], int]:
    """Validate and extract model filtering arguments."""
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a dictionary")
    
    schema = arguments.get("schema")
    level = arguments.get("level") 
    limit = arguments.get("limit", 10)
    
    # Validate schema
    if schema is not None:
        if not isinstance(schema, str) or not schema.strip():
            raise ValueError("schema must be a non-empty string")
        schema = schema.strip().lower()
        
        # Prevent path traversal and injection attempts
        if any(char in schema for char in ['/', '\\', '..', '\x00', ';', '--']):
            raise ValueError("schema contains invalid characters")
    
    # Validate level
    if level is not None:
        if not isinstance(level, str) or not level.strip():
            raise ValueError("level must be a non-empty string")
        level = level.strip().lower()
        
        if level not in ['bronze', 'silver', 'gold']:
            raise ValueError("level must be one of: bronze, silver, gold")
    
    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 200:
        raise ValueError("limit must be an integer between 1 and 200")
    
    # Set default to core if no schema or level provided
    if not schema and not level:
        schema = "core"
    
    return schema, level, limit


def _filter_models_by_criteria(models: Dict[str, Any], schema: Optional[str], level: Optional[str]) -> List[Dict[str, Any]]:
    """Filter models based on schema or medallion level criteria."""
    filtered_models = []
    
    for model_id, model_info in models.items():
        if not isinstance(model_info, dict) or model_info.get("resource_type") != "model":
            continue
            
        # Check if model matches criteria
        matches = False
        
        if schema:
            # Partial schema match to handle cases like silver_api
            matches = schema in model_info.get("schema", "").lower()
        elif level:
            # Check both schema and fqn for level matching
            model_fqn = model_info.get("fqn", [])
            
            if level == "bronze":
                matches = any("bronze" in part.lower() for part in model_fqn) or "bronze" in model_info.get("schema", "").lower()
            elif level == "silver":
                matches = any("silver" in part.lower() for part in model_fqn) or "silver" in model_info.get("schema", "").lower()
            elif level == "gold":
                matches = any("gold" in part.lower() for part in model_fqn) or "gold" in model_info.get("schema", "").lower()
        
        if matches:
            # Extract key model information
            model_data = {
                "unique_id": model_id,
                "name": model_info.get("name"),
                "schema": model_info.get("schema"),
                "database": model_info.get("database"),
                "materialized": model_info.get("config", {}).get("materialized"),
                "description": model_info.get("description", ""),
                "tags": model_info.get("tags", []),
                "path": model_info.get("original_file_path"),
                "fqn": model_info.get("fqn", []),
                "relation_name": model_info.get("relation_name")
            }
            filtered_models.append(model_data)
    
    # Sort by schema then name for consistent ordering
    return sorted(filtered_models, key=lambda x: (x.get("schema", ""), x.get("name", "")))


async def handle_get_models(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_models tool invocation."""
    try:
        # Validate input arguments
        schema, level, limit = _validate_models_arguments(arguments)
        
        # Load manifest artifact
        manifest, _ = load_dbt_artifacts()
        
        # Get all models from manifest
        nodes = manifest.get("nodes", {})
        if not isinstance(nodes, dict):
            raise ValueError("Invalid manifest structure: 'nodes' is not a dictionary")
        
        # Filter models based on criteria
        filtered_models = _filter_models_by_criteria(nodes, schema, level)
        
        # Apply limit
        if len(filtered_models) > limit:
            filtered_models = filtered_models[:limit]
            truncated = True
        else:
            truncated = False
        
        # Format response
        filter_desc = f"schema '{schema}'" if schema else f"level '{level}'"
        response_lines = [
            f"# Models ({filter_desc})",
            f"**Found:** {len(filtered_models)} models" + (" (truncated)" if truncated else ""),
            ""
        ]
        
        if not filtered_models:
            response_lines.append("No models found matching the specified criteria.")
            return [TextContent(type="text", text="\n".join(response_lines))]
        
        # Group by schema for better organization
        models_by_schema = {}
        for model in filtered_models:
            model_schema = model.get("schema", "unknown")
            if model_schema not in models_by_schema:
                models_by_schema[model_schema] = []
            models_by_schema[model_schema].append(model)
        
        # Output models grouped by schema
        for schema_name in sorted(models_by_schema.keys()):
            schema_models = models_by_schema[schema_name]
            response_lines.extend([
                f"## Schema: {schema_name}",
                f"**Models:** {len(schema_models)}",
                ""
            ])
            
            for model in schema_models:
                response_lines.append(f"### {model['name']}")
                response_lines.append(f"**Unique ID:** {model['unique_id']}")
                response_lines.append(f"**Database:** {model.get('database', 'N/A')}")
                response_lines.append(f"**Materialized:** {model.get('materialized', 'N/A')}")
                response_lines.append(f"**Path:** {model.get('path', 'N/A')}")
                
                if model.get("description"):
                    response_lines.append(f"**Description:** {model['description']}")
                
                if model.get("tags"):
                    response_lines.append(f"**Tags:** {', '.join(model['tags'])}")
                
                response_lines.append("")
        
        if truncated:
            response_lines.extend([
                "---",
                f"**Note:** Results limited to {limit} models. Use a higher limit or more specific filters to see more results."
            ])
        
        return [TextContent(type="text", text="\n".join(response_lines))]
        
    except FileNotFoundError as e:
        logger.error(f"File not found in get_models: {e}")
        return [TextContent(
            type="text",
            text=f"Required dbt artifacts not found: {str(e)}"
        )]
    except ValueError as e:
        logger.error(f"Invalid input in get_models: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"Unexpected error in get_models: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving models: {str(e)}"
        )]
