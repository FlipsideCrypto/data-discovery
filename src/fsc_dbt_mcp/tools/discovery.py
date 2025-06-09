"""
Discovery tools for dbt model exploration and metadata retrieval.
"""
import json
import os
from typing import Dict, Any, Optional
from mcp.types import Tool, TextContent
import logging

logger = logging.getLogger(__name__)


def load_dbt_artifacts() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Load dbt manifest and catalog artifacts."""
    # Check for artifacts in dev/inputs first, then project directory
    project_dir = os.getenv('DBT_PROJECT_DIR', os.getcwd())
    
    # Try dev/inputs path first (for testing)
    # dev_manifest_path = os.path.join(os.getcwd(), 'dev', 'inputs', 'manifest.json')
    # dev_catalog_path = os.path.join(os.getcwd(), 'dev', 'inputs', 'catalog.json')
    dev_manifest_path = "/Users/jackforgash/gh/tools/local/fsc-dbt-mcp/dev/inputs/manifest.json"
    dev_catalog_path = "/Users/jackforgash/gh/tools/local/fsc-dbt-mcp/dev/inputs/catalog.json"

    # Try project target path second
    target_manifest_path = os.path.join(project_dir, 'target', 'manifest.json')
    target_catalog_path = os.path.join(project_dir, 'target', 'catalog.json')
    
    manifest_path = None
    catalog_path = None
    
    # Determine which paths to use
    if os.path.exists(dev_manifest_path):
        manifest_path = dev_manifest_path
        logger.info(f"Using dev manifest: {manifest_path}")
    elif os.path.exists(target_manifest_path):
        manifest_path = target_manifest_path
        logger.info(f"Using target manifest: {manifest_path}")
    else:
        raise FileNotFoundError("No manifest.json found in dev/inputs or target directory")
    
    if os.path.exists(dev_catalog_path):
        catalog_path = dev_catalog_path
        logger.info(f"Using dev catalog: {catalog_path}")
    elif os.path.exists(target_catalog_path):
        catalog_path = target_catalog_path
        logger.info(f"Using target catalog: {catalog_path}")
    else:
        raise FileNotFoundError("No catalog.json found in dev/inputs or target directory")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
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


async def handle_get_model_details(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_model_details tool invocation."""
    try:
        manifest, catalog = load_dbt_artifacts()
        
        unique_id = arguments.get("uniqueId")
        model_name = arguments.get("model_name")
        
        # Find the model in manifest
        model_node = None
        
        if unique_id:
            # Direct lookup by unique_id
            model_node = manifest.get("nodes", {}).get(unique_id)
            if not model_node:
                return [TextContent(
                    type="text",
                    text=f"Model with uniqueId '{unique_id}' not found in manifest"
                )]
        elif model_name:
            # Search by model name
            for node_id, node in manifest.get("nodes", {}).items():
                if (node.get("resource_type") == "model" and 
                    node.get("name") == model_name):
                    model_node = node
                    unique_id = node_id
                    break
            
            if not model_node:
                return [TextContent(
                    type="text",
                    text=f"Model with name '{model_name}' not found in manifest"
                )]
        else:
            return [TextContent(
                type="text",
                text="Either uniqueId or model_name must be provided"
            )]
        
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
        
    except Exception as e:
        logger.error(f"Error in get_model_details: {e}")
        return [TextContent(
            type="text",
            text=f"Error retrieving model details: {str(e)}"
        )]