"""
Shared utilities for discovery tools.

Provides common functions for loading and validating dbt artifacts,
error message generation, and multi-project operations.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import logging
from mcp.types import TextContent

logger = logging.getLogger(__name__)

# Enable debug logging if environment variable is set
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1', 'yes', 'on')
if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)


def _validate_file_path(file_path: str) -> Path:
    """Validate and normalize file path for security."""
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    # Normalize path and check for traversal attempts
    normalized_path = Path(file_path).resolve()
    
    # Basic security check - ensure file exists and is readable
    if not normalized_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    if not normalized_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Check file size (max 50MB for JSON artifacts)
    file_size = normalized_path.stat().st_size
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes (max: {max_size})")
    
    return normalized_path


def _safe_load_json(file_path: Path) -> Dict[str, Any]:
    """Safely load JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")
    except UnicodeDecodeError as e:
        raise ValueError(f"File encoding error in {file_path}: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to read {file_path}: {str(e)}")


def load_dbt_artifacts() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load dbt manifest and catalog artifacts with security validation."""
    # TODO - legacy support. CAN DROP
    project_dir = os.getenv('DBT_PROJECT_DIR', os.getcwd())
    
    # Define search paths in priority order
    search_paths = [
        # Development/testing paths
        (os.path.join(os.getcwd(), 'target', 'manifest.json'),
         os.path.join(os.getcwd(), 'target', 'catalog.json')),
        # Standard dbt target directory
        (os.path.join(project_dir, 'target', 'manifest.json'),
         os.path.join(project_dir, 'target', 'catalog.json')),
    ]
    
    manifest_path = None
    catalog_path = None
    
    # Find first available artifact pair
    for manifest_candidate, catalog_candidate in search_paths:
        try:
            manifest_path = _validate_file_path(manifest_candidate)
            catalog_path = _validate_file_path(catalog_candidate)
            logger.info(f"Using artifacts - Manifest: {manifest_path}, Catalog: {catalog_path}")
            break
        except (FileNotFoundError, ValueError):
            continue
    
    if not manifest_path or not catalog_path:
        raise FileNotFoundError(
            "No valid dbt artifacts found. Searched paths: " +
            ", ".join([f"{m}, {c}" for m, c in search_paths])
        )
    
    # Load and validate JSON files
    try:
        manifest = _safe_load_json(manifest_path)
        catalog = _safe_load_json(catalog_path)
        
        # Basic validation of artifact structure
        if not isinstance(manifest, dict) or 'nodes' not in manifest:
            raise ValueError("Invalid manifest.json structure")
        
        if not isinstance(catalog, dict) or 'nodes' not in catalog:
            raise ValueError("Invalid catalog.json structure")
        
        return manifest, catalog
        
    except Exception as e:
        logger.error(f"Error loading dbt artifacts: {e}")
        raise


def get_available_resources() -> List[str]:
    """Get list of available resource IDs from resource registry."""
    from fsc_dbt_mcp.resources import resource_registry
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

# TODO - migrate 
def validate_string_argument(value: Any, arg_name: str, allow_empty: bool = False) -> str:
    """Validate and sanitize string arguments with common security checks."""
    if not isinstance(value, str):
        raise ValueError(f"{arg_name} must be a string")
    
    if not allow_empty and not value.strip():
        raise ValueError(f"{arg_name} must be a non-empty string")
    
    value = value.strip()
    
    # Prevent path traversal and injection attempts
    if any(char in value for char in ['/', '\\', '..', '\x00']):
        raise ValueError(f"{arg_name} contains invalid characters")
    
    return value


def normalize_null_to_none(value: Any) -> Any:
    """Normalize null/undefined values to None for consistent handling."""
    if value is None or value == "null" or (isinstance(value, str) and value.lower() == "null") or type(value) == bool:
        return None
    return value

# TODO - migrate resource validation to ResourceIdProperty class
def validate_resource_id(resource_id: Any, required: bool = False) -> Optional[Any]:
    """Validate and normalize resource_id parameter with consistent handling across tools.
    
    Args:
        resource_id: The resource_id value to validate (can be string or array of strings)
        required: Whether resource_id is required for this tool
        
    Returns:
        Normalized resource_id value or None
        
    Raises:
        ValueError: If resource_id is invalid or required but missing
    """
    # Normalize null values first
    resource_id = normalize_null_to_none(resource_id)
    
    # Check if required but missing
    if required and resource_id is None:
        raise ValueError("resource_id is required for this operation")
    
    # Return None if not provided (for optional resource_id)
    if resource_id is None:
        return None
    
    # Validate string resource_id
    if isinstance(resource_id, str):
        return validate_string_argument(resource_id, "resource_id")
    
    # Validate array resource_id
    if isinstance(resource_id, list):
        if len(resource_id) == 0:
            return None  # Empty array treated as None
        
        # Validate each item in array
        validated_array = []
        for i, item in enumerate(resource_id):
            if not isinstance(item, str):
                raise ValueError(f"resource_id array item {i} must be a string")
            validated_array.append(validate_string_argument(item, f"resource_id[{i}]"))
        
        return validated_array
    
    # Invalid type
    raise ValueError("resource_id must be a string or array of strings")

# TODO - migrate argument validation to ToolPropertySet class
def validate_arguments_dict(arguments: Any) -> Dict[str, Any]:
    """Validate that arguments is a dictionary."""
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a dictionary")
    return arguments


def create_input_schema_for_resource_id(required: bool = False, description: str = None) -> Dict[str, Any]:
    """Create standardized input schema for resource_id parameter.
    
    Args:
        required: Whether resource_id should be required
        description: Custom description for resource_id (uses default if None)
        
    Returns:
        Dictionary with resource_id schema definition
    """
    default_description = (
        "Resource ID(s) to search in. Can be a single resource ID string or array "
        "of resource IDs (max 5). Resource_id is the ID of a resource returned by "
        "get_resources(). Example: 'blockchain-models'"
    )
    
    return {
        "type": ["string", "array"],
        "description": description or default_description,
        "not": {"type": ["boolean", "null"]},
        "items": {
            "type": "string"
        },
        "maxItems": 5
    }
