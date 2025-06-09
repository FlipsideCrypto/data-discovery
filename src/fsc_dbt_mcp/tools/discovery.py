"""
Discovery tools for dbt model exploration and metadata retrieval.

Follows MCP best practices for input validation, error handling, and security.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from mcp.types import Tool, TextContent
import logging

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


def get_model_details_tool() -> Tool:
    """Tool definition for get_model_details."""
    return Tool(
        name="get_model_details",
        description="Retrieves detailed information about a specific dbt model, including description, columns, SQL, and metadata",
        inputSchema={
            "type": "object",
            "properties": {
                "uniqueId": {
                    "type": "string",
                    "description": "The unique identifier of the model (format: 'model.project_name.model_name'). STRONGLY RECOMMENDED when available."
                },
                "model_name": {
                    "type": "string", 
                    "description": "The name of the dbt model. Only use when uniqueId is unavailable."
                }
            },
            "oneOf": [
                {"required": ["uniqueId"]},
                {"required": ["model_name"]}
            ]
        }
    )


def _validate_model_arguments(arguments: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Validate and extract model identification arguments."""
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a dictionary")
    
    unique_id = arguments.get("uniqueId")
    model_name = arguments.get("model_name")
    
    # Input sanitization
    if unique_id is not None:
        if not isinstance(unique_id, str) or not unique_id.strip():
            raise ValueError("uniqueId must be a non-empty string")
        unique_id = unique_id.strip()
        
        # Basic format validation for unique_id
        if not unique_id.startswith("model."):
            raise ValueError("uniqueId must start with 'model.'")
    
    if model_name is not None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        model_name = model_name.strip()
        
        # Prevent path traversal and injection attempts
        if any(char in model_name for char in ['/', '\\', '..', '\x00']):
            raise ValueError("model_name contains invalid characters")
    
    if not unique_id and not model_name:
        raise ValueError("Either uniqueId or model_name must be provided")
    
    return unique_id, model_name


def _find_model_node(manifest: Dict[str, Any], unique_id: Optional[str], 
                     model_name: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Find model node in manifest with proper error handling."""
    nodes = manifest.get("nodes", {})
    
    if not isinstance(nodes, dict):
        raise ValueError("Invalid manifest structure: 'nodes' is not a dictionary")
    
    if unique_id:
        # Direct lookup by unique_id
        model_node = nodes.get(unique_id)
        if model_node and model_node.get("resource_type") == "model":
            return model_node, unique_id
        return None, None
    
    elif model_name:
        # Search by model name
        for node_id, node in nodes.items():
            if (isinstance(node, dict) and 
                node.get("resource_type") == "model" and 
                node.get("name") == model_name):
                return node, node_id
    
    return None, None


async def handle_get_model_details(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_model_details tool invocation with comprehensive validation."""
    try:
        # Validate input arguments
        unique_id, model_name = _validate_model_arguments(arguments)
        
        # Load artifacts
        manifest, catalog = load_dbt_artifacts()
        
        # Find the model
        model_node, found_unique_id = _find_model_node(manifest, unique_id, model_name)
        
        if not model_node or not found_unique_id:
            identifier = unique_id if unique_id else model_name
            return [TextContent(
                type="text",
                text=f"Model '{identifier}' not found in manifest"
            )]
        
        unique_id = found_unique_id
        
        # Get catalog information if available
        catalog_node = catalog.get("nodes", {}).get(unique_id, {})
        
        # Extract model details
        model_details = {
            "unique_id": unique_id,
            "name": model_node.get("name"),
            "description": model_node.get("description", ""),
            "schema": model_node.get("schema"),
            "database": model_node.get("database"),
            "relation_name": model_node.get("relation_name"),
            "materialized": model_node.get("config", {}).get("materialized"),
            "tags": model_node.get("tags", []),
            "meta": model_node.get("meta", {}),
            "path": model_node.get("original_file_path"),
            "raw_code": model_node.get("raw_code", ""),
            "compiled_code": model_node.get("compiled_code"),
            "depends_on": model_node.get("depends_on", {}),
            "refs": model_node.get("refs", []),
            "sources": model_node.get("sources", []),
            "fqn": model_node.get("fqn", []),
            "access": model_node.get("access"),
            "constraints": model_node.get("constraints", []),
            "version": model_node.get("version"),
            "latest_version": model_node.get("latest_version"),
        }
        
        # Add column information from manifest
        manifest_columns = model_node.get("columns", {})
        columns = {}
        for col_name, col_info in manifest_columns.items():
            columns[col_name] = {
                "name": col_name,
                "description": col_info.get("description", ""),
                "data_type": col_info.get("data_type"),
                "meta": col_info.get("meta", {}),
                "tags": col_info.get("tags", []),
                "constraints": col_info.get("constraints", [])
            }
        
        # Enhance with catalog column information if available
        catalog_columns = catalog_node.get("columns", {})
        for col_name, col_info in catalog_columns.items():
            if col_name in columns:
                columns[col_name].update({
                    "type": col_info.get("type"),
                    "index": col_info.get("index"),
                    "comment": col_info.get("comment")
                })
            else:
                # Column exists in catalog but not manifest
                columns[col_name] = {
                    "name": col_name,
                    "type": col_info.get("type"),
                    "index": col_info.get("index"),
                    "comment": col_info.get("comment", ""),
                    "description": "",
                    "data_type": col_info.get("type"),
                    "meta": {},
                    "tags": [],
                    "constraints": []
                }
        
        model_details["columns"] = columns
        
        # Add catalog metadata if available
        if catalog_node:
            model_details["catalog_metadata"] = catalog_node.get("metadata", {})
            model_details["stats"] = catalog_node.get("stats", {})
        
        # Format the response
        response_lines = [
            f"# Model Details: {model_details['name']}",
            f"**Unique ID:** {model_details['unique_id']}",
            f"**Database:** {model_details['database']}",
            f"**Schema:** {model_details['schema']}",
            f"**Relation Name:** {model_details['relation_name']}",
            f"**File Path:** {model_details['path']}",
            f"**Materialization:** {model_details['materialized']}",
            ""
        ]
        
        if model_details["description"]:
            response_lines.extend([
                "## Description",
                model_details["description"],
                ""
            ])
        
        if model_details["tags"]:
            response_lines.extend([
                "## Tags",
                ", ".join(model_details["tags"]),
                ""
            ])
        
        if model_details["meta"]:
            response_lines.extend([
                "## Meta",
                json.dumps(model_details["meta"], indent=2),
                ""
            ])
        
        # Columns section
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
        if model_details["refs"] or model_details["sources"]:
            response_lines.extend([
                "## Dependencies",
                ""
            ])
            
            if model_details["refs"]:
                response_lines.extend([
                    "**Models Referenced:**",
                    ""
                ])
                for ref in model_details["refs"]:
                    response_lines.append(f"- {'.'.join(ref) if isinstance(ref, list) else ref}")
                response_lines.append("")
            
            if model_details["sources"]:
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
        if model_details["raw_code"]:
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
            model_details["compiled_code"] != model_details["raw_code"]):
            response_lines.extend([
                "## Compiled SQL",
                "",
                "```sql",
                model_details["compiled_code"],
                "```"
            ])
        
        return [TextContent(type="text", text="\n".join(response_lines))]
        
    except FileNotFoundError as e:
        logger.error(f"File not found in get_model_details: {e}")
        return [TextContent(
            type="text",
            text=f"Required dbt artifacts not found: {str(e)}"
        )]
    except ValueError as e:
        logger.error(f"Invalid input in get_model_details: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"Unexpected error in get_model_details: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving model details: {str(e)}"
        )]