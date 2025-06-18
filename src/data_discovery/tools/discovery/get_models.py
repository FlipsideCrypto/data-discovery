"""
get_models tool for retrieving dbt models with filtering by schema or medallion level.
Supports multi-project operations with project-aware functionality.
"""
import os
from typing import Dict, Any, List, Optional, Union
from mcp.types import Tool, TextContent
from pydantic import Field
from loguru import logger

from data_discovery.prompts import get_prompt
from data_discovery.api.service import DataDiscoveryService
from .utils import get_available_resources
from .properties import ToolPropertySet, SCHEMA_FILTER, LEVEL_FILTER, STANDARD_RESOURCE_ID, STANDARD_LIMIT

# Define tool properties using the shared properties system
_tool_properties = ToolPropertySet({
    "schema": SCHEMA_FILTER,
    "level": LEVEL_FILTER,
    "resource_id": STANDARD_RESOURCE_ID,
    "limit": STANDARD_LIMIT
})


def get_models_tool() -> Tool:
    """Tool definition for get_models."""
    return Tool(
        name="get_models",
        description=get_prompt("discovery/get_models"),
        inputSchema=_tool_properties.get_input_schema()
    )


def _validate_models_arguments(arguments: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[Any], int]:
    """Validate and extract model filtering arguments."""
    logger.debug(f"[GET_MODELS] _validate_models_arguments called with: {arguments}")
    
    # Use shared properties for validation
    params = _tool_properties.validate_and_extract_all(arguments)
    logger.debug(f"[GET_MODELS] Shared properties validation result: {params}")
    
    schema = params["schema"]
    level = params["level"]
    resource_id = params["resource_id"]
    limit = params["limit"]
    
    # Require at least one filtering parameter
    if not schema and not level and not resource_id:
        logger.debug(f"[GET_MODELS] Validation failed - no filtering parameters provided")
        raise ValueError("At least one parameter (schema, level, or resource_id) is required. Use get_resources() to see available options.")
    
    logger.debug(f"[GET_MODELS] Validation successful - schema={schema}, level={level}, resource_id={resource_id}, limit={limit}")
    return schema, level, resource_id, limit




async def handle_get_models(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_models tool invocation using shared service."""
    logger.debug(f"[GET_MODELS] Starting handle_get_models with arguments: {arguments}")
    
    try:
        # Validate input arguments
        logger.debug(f"[GET_MODELS] Calling _validate_models_arguments")
        schema, level, resource_id, limit = _validate_models_arguments(arguments)
        
        # Use shared service to get models
        service = DataDiscoveryService()
        result = await service.get_models(
            schema=schema,
            level=level,
            resource_id=resource_id,
            limit=limit
        )
        
        # Handle error case
        if result.get("error"):
            logger.debug(f"[GET_MODELS] Service returned error: {result['error']}")
            return [TextContent(
                type="text",
                text=result["error"],
                isError=True
            )]
        
        # Convert service result to MCP TextContent format
        return _convert_models_to_mcp_format(result, schema, level, resource_id, limit)
        
    except ValueError as e:
        logger.error(f"[GET_MODELS] Validation error: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}",
            isError=True
        )]
    except Exception as e:
        logger.error(f"[GET_MODELS] Unexpected error: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving models: {str(e)}",
            isError=True
        )]


# FastMCP-compatible wrapper function
async def fastmcp_get_models(
    schema: Optional[str] = Field(
        default=None,
        description="Filter models by schema name (e.g., 'core', 'defi', 'nft'). Takes precedence over level if both are provided."
    ),
    level: Optional[str] = Field(
        default=None,
        description="Filter models by medallion level (bronze, silver, gold). Ignored if schema is provided."
    ),
    resource_id: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Resource ID(s) to search in. Can be a single resource ID string or array of resource IDs. Example: 'ethereum-models' or ['bitcoin-models', 'ethereum-models']"
    ),
    limit: int = Field(
        default=25,
        description="Maximum number of models to return",
        ge=1,
        le=100
    )
) -> str:
    """
    FastMCP wrapper for get_models tool.
    Search and retrieve dbt models with filtering by schema or medallion level.
    Supports multi-project operations with project-aware functionality.
    """
    try:
        # Validate that at least one filtering parameter is provided
        if not schema and not level and not resource_id:
            raise ValueError("At least one parameter (schema, level, or resource_id) is required. Use get_resources() to see available options.")
        
        logger.debug(f"get_models called with schema={schema}, level={level}, resource_id={resource_id}, limit={limit}")
        
        service = DataDiscoveryService()
        result = await service.get_models(
            schema=schema,
            level=level,
            resource_id=resource_id,
            limit=limit
        )
        
        if result.get("error"):
            logger.error(f"Service error in get_models: {result['error']}")
            raise RuntimeError(result["error"])
        
        # Convert service result to formatted text
        text_result = _convert_models_to_mcp_format(result, schema, level, resource_id, limit)
        return text_result[0].text if text_result else "No models found"
        
    except Exception as e:
        logger.error(f"Error in get_models: {e}")
        raise RuntimeError(f"Internal error retrieving models: {str(e)}")


def _convert_models_to_mcp_format(
    result: Dict[str, Any], 
    schema: Optional[str], 
    level: Optional[str], 
    resource_id: Optional[Any], 
    limit: int
) -> list[TextContent]:
    """Convert shared service result to MCP TextContent format."""
    # Format response header
    filter_desc = f"schema '{schema}'" if schema else f"level '{level}'" if level else "all"
    successful_projects = result.get("successful_projects", [])
    project_info = f" in projects {successful_projects}" if resource_id else " across all projects"
    
    response_lines = [
        f"# Models ({filter_desc}){project_info}",
        f"**Found:** {result['returned_count']} models" + (" (truncated)" if result.get('truncated') else ""),
    ]
    
    # Add warning about failed resources if any
    failed_projects = result.get("failed_projects", [])
    if failed_projects:
        response_lines.append(f"**Warning:** Failed to load resources: {failed_projects}")
    
    response_lines.append("")
    
    models = result.get("models", [])
    if not models:
        logger.debug(f"[GET_MODELS] No models found matching criteria")
        available_resources = get_available_resources()
        response_lines.append(f"No models found matching the specified criteria. Available resources: {available_resources}")
        return [TextContent(type="text", text="\n".join(response_lines))]
    
    # Group by project first, then by schema for better organization
    models_by_project = {}
    for model in models:
        model_project = model.get("resource_id", "unknown")
        if model_project not in models_by_project:
            models_by_project[model_project] = {}
        
        model_schema = model.get("schema", "unknown")
        if model_schema not in models_by_project[model_project]:
            models_by_project[model_project][model_schema] = []
        models_by_project[model_project][model_schema].append(model)
    
    # Output models grouped by project and schema
    for project_name in sorted(models_by_project.keys()):
        project_schemas = models_by_project[project_name]
        total_project_models = sum(len(models) for models in project_schemas.values())
        
        response_lines.extend([
            f"## Project: {project_name}",
            f"**Total Models:** {total_project_models}",
            ""
        ])
        
        for schema_name in sorted(project_schemas.keys()):
            schema_models = project_schemas[schema_name]
            response_lines.extend([
                f"### Schema: {schema_name}",
                f"**Models:** {len(schema_models)}",
                ""
            ])
            
            for model in schema_models:
                response_lines.append(f"#### {model['name']}")
                response_lines.append(f"**Unique ID:** {model['unique_id']}")
                response_lines.append(f"**Database:** {model.get('database', 'N/A')}")
                response_lines.append(f"**Materialized:** {model.get('materialized', 'N/A')}")
                response_lines.append(f"**Path:** {model.get('path', 'N/A')}")
                
                if model.get("description"):
                    response_lines.append(f"**Description:** {model['description']}")
                
                if model.get("tags"):
                    response_lines.append(f"**Tags:** {', '.join(model['tags'])}")
                
                response_lines.append("")
        
        response_lines.append("---")
        response_lines.append("")
    
    if result.get('truncated'):
        response_lines.extend([
            f"**Note:** Results limited to {limit} models. Use a higher limit or more specific filters to see more results."
        ])
    
    return [TextContent(type="text", text="\n".join(response_lines))]