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


def create_error_response(message: str, include_available_resources: bool = True) -> List[TextContent]:
    """Create a standardized error response with optional available resources list."""
    if include_available_resources:
        available_resources = get_available_resources()
        full_message = f"{message}. Available resources: {available_resources}"
    else:
        full_message = message
    
    return [TextContent(type="text", text=full_message)]


def create_resource_not_found_error(identifier: str, resource_info: str = "", 
                                  item_type: str = "item") -> List[TextContent]:
    """Create a standardized 'not found' error with available resources."""
    available_resources = get_available_resources()
    resource_suffix = resource_info if resource_info else " in any available resources"
    message = f"{item_type.title()} '{identifier}' not found{resource_suffix}. Available resources: {available_resources}"
    return [TextContent(type="text", text=message)]


def create_no_artifacts_error() -> List[TextContent]:
    """Create a standardized 'no artifacts loaded' error with available resources."""
    return create_error_response("No resource artifacts could be loaded")


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
    if value is None or value == "null" or (isinstance(value, str) and value.lower() == "null"):
        return None
    return value
