"""
get_models tool for retrieving dbt models with filtering by schema or medallion level.
Supports multi-project operations with project-aware functionality.
"""
import os
from typing import Dict, Any, List, Optional
from mcp.types import Tool, TextContent
import logging

from fsc_dbt_mcp.prompts import get_prompt
from fsc_dbt_mcp.project_manager import project_manager
from .utils import create_error_response, create_resource_not_found_error, create_no_artifacts_error, get_available_resources
from .properties import ToolPropertySet, SCHEMA_FILTER, LEVEL_FILTER, STANDARD_RESOURCE_ID, STANDARD_LIMIT

logger = logging.getLogger(__name__)

# Enable debug logging if environment variable is set
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1', 'yes', 'on')
if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)

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


def _filter_models_by_criteria(models: Dict[str, Any], schema: Optional[str], level: Optional[str], resource_id: str) -> List[Dict[str, Any]]:
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
                "relation_name": model_info.get("relation_name"),
                "resource_id": resource_id
            }
            filtered_models.append(model_data)
    
    # Sort by schema then name for consistent ordering
    return sorted(filtered_models, key=lambda x: (x.get("schema", ""), x.get("name", "")))


async def handle_get_models(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_models tool invocation."""
    logger.debug(f"[GET_MODELS] Starting handle_get_models with arguments: {arguments}")
    
    try:
        # Validate input arguments
        logger.debug(f"[GET_MODELS] Calling _validate_models_arguments")
        schema, level, resource_id, limit = _validate_models_arguments(arguments)
        
        # Load project artifacts with graceful handling of invalid resources
        requested_resources = []
        logger.debug(f"[GET_MODELS] Processing resource_id: {resource_id} (type: {type(resource_id)})")
        
        if resource_id:
            if isinstance(resource_id, str):
                requested_resources = [resource_id]
                logger.debug(f"[GET_MODELS] Using single resource: {requested_resources}")
            elif isinstance(resource_id, list):
                requested_resources = resource_id
                logger.debug(f"[GET_MODELS] Using resource list: {requested_resources}")
        else:
            # Get all available resources if none specified
            from fsc_dbt_mcp.resources import resource_registry
            requested_resources = resource_registry.list_project_ids()
            logger.debug(f"[GET_MODELS] No resource_id specified, using all available: {requested_resources}")
        
        # Load artifacts one by one to handle failures gracefully
        successful_artifacts = {}
        failed_resources = []
        logger.debug(f"[GET_MODELS] Loading artifacts for {len(requested_resources)} resources")
        
        for res_id in requested_resources:
            try:
                logger.debug(f"[GET_MODELS] Loading artifacts for resource: {res_id}")
                artifacts = await project_manager.get_project_artifacts([res_id])
                if artifacts and res_id in artifacts:
                    successful_artifacts[res_id] = artifacts[res_id]
                    logger.debug(f"[GET_MODELS] Successfully loaded artifacts for: {res_id}")
                else:
                    failed_resources.append(res_id)
                    logger.debug(f"[GET_MODELS] No artifacts found for: {res_id}")
            except Exception as e:
                logger.warning(f"[GET_MODELS] Failed to load artifacts for resource {res_id}: {e}")
                failed_resources.append(res_id)
        
        logger.debug(f"[GET_MODELS] Artifact loading complete - successful: {list(successful_artifacts.keys())}, failed: {failed_resources}")
        
        if not successful_artifacts:
            logger.debug(f"[GET_MODELS] No successful artifacts loaded")
            if failed_resources:
                logger.debug(f"[GET_MODELS] Returning error response for failed resources")
                return create_error_response(f"No valid resources found. Failed resources: {failed_resources}")
            else:
                logger.debug(f"[GET_MODELS] Returning no artifacts error")
                return create_no_artifacts_error()
        
        # Collect all filtered models across successfully loaded projects
        all_filtered_models = []
        logger.debug(f"[GET_MODELS] Starting model filtering across {len(successful_artifacts)} projects")
        
        for proj_id, (manifest, _) in successful_artifacts.items():
            logger.debug(f"[GET_MODELS] Processing project: {proj_id}")
            # Get all models from manifest
            nodes = manifest.get("nodes", {})
            if not isinstance(nodes, dict):
                logger.warning(f"[GET_MODELS] Invalid manifest structure in project {proj_id}: 'nodes' is not a dictionary")
                continue
            
            logger.debug(f"[GET_MODELS] Found {len(nodes)} nodes in project {proj_id}")
            # Filter models based on criteria for this project
            project_models = _filter_models_by_criteria(nodes, schema, level, proj_id)
            logger.debug(f"[GET_MODELS] Filtered to {len(project_models)} models for project {proj_id}")
            all_filtered_models.extend(project_models)
        
        # Sort all models by project, schema, then name
        all_filtered_models = sorted(all_filtered_models, key=lambda x: (x.get("resource_id", ""), x.get("schema", ""), x.get("name", "")))
        
        # Apply limit
        if len(all_filtered_models) > limit:
            all_filtered_models = all_filtered_models[:limit]
            truncated = True
        else:
            truncated = False
        
        # Format response
        filter_desc = f"schema '{schema}'" if schema else f"level '{level}'" if level else "all"
        successful_projects = list(successful_artifacts.keys())
        project_info = f" in projects {successful_projects}" if resource_id else " across all projects"
        
        response_lines = [
            f"# Models ({filter_desc}){project_info}",
            f"**Found:** {len(all_filtered_models)} models" + (" (truncated)" if truncated else ""),
        ]
        
        # Add warning about failed resources if any
        if failed_resources:
            response_lines.append(f"**Warning:** Failed to load resources: {failed_resources}")
        
        response_lines.append("")
        
        if not all_filtered_models:
            logger.debug(f"[GET_MODELS] No models found matching criteria")
            available_resources = get_available_resources()
            response_lines.append(f"No models found matching the specified criteria. Available resources: {available_resources}")
            result = [TextContent(type="text", text="\n".join(response_lines))]
            logger.debug(f"[GET_MODELS] Returning no-results response: {type(result)} with {len(result)} items")
            return result
        
        # Group by project first, then by schema for better organization
        models_by_project = {}
        for model in all_filtered_models:
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
        
        if truncated:
            response_lines.extend([
                f"**Note:** Results limited to {limit} models. Use a higher limit or more specific filters to see more results."
            ])
        
        result = [TextContent(type="text", text="\n".join(response_lines))]
        logger.debug(f"[GET_MODELS] Returning successful response: {type(result)} with {len(result)} items")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"[GET_MODELS] File not found error: {e}")
        return [TextContent(
            type="text",
            text=f"Required dbt artifacts not found: {str(e)}"
        )]
    except ValueError as e:
        logger.error(f"[GET_MODELS] Validation error: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"[GET_MODELS] Unexpected error: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving models: {str(e)}"
        )]