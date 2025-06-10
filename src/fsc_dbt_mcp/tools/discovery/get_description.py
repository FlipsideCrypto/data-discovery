"""
get_description tool for retrieving documentation blocks from dbt manifest.

Follows MCP best practices for input validation, error handling, and security.
Supports multi-project operations with project-aware functionality.
"""
from typing import Dict, Any
from mcp.types import Tool, TextContent
import logging

from fsc_dbt_mcp.prompts import get_prompt
from fsc_dbt_mcp.project_manager import project_manager
from .utils import create_error_response, create_resource_not_found_error, create_no_artifacts_error, validate_string_argument, get_available_resources, normalize_null_to_none

logger = logging.getLogger(__name__)


def get_description_tool() -> Tool:
    """Tool definition for get_description."""
    return Tool(
        name="get_description",
        description=get_prompt("discovery/get_description"),
        inputSchema={
            "type": "object",
            "properties": {
                "doc_name": {
                    "type": "string",
                    "description": "Name of the documentation block to retrieve (default: '__MCP__')",
                    "default": "__MCP__"
                },
                "resource_id": {
                    "type": ["string", "array"],
                    "description": "Resource ID(s) to search in. Can be a single resource ID string or array of resource IDs (max 5). REQUIRED to avoid cross-contamination of blockchain-specific documentation.",
                    "items": {
                        "type": "string"
                    },
                    "maxItems": 5
                }
            },
            "required": ["resource_id"],
            "additionalProperties": False
        }
    )


async def handle_get_description(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_description tool invocation."""
    try:
        # Extract arguments
        doc_name = arguments.get("doc_name", "__MCP__")
        resource_id = normalize_null_to_none(arguments.get("resource_id"))
        
        doc_name = validate_string_argument(doc_name, "doc_name")
        
        # Require resource_id to avoid cross-contamination of blockchain-specific context
        if not resource_id:
            return create_error_response(
                "resource_id is required for get_description to avoid cross-contamination of blockchain-specific documentation. Please specify which project(s) to search"
            )
        
        # Load project artifacts
        artifacts = await project_manager.get_project_artifacts(resource_id)
        if not artifacts:
            return create_no_artifacts_error()
        
        # Search for documentation blocks across all specified projects
        all_matching_docs = []
        
        for proj_id, (manifest, _) in artifacts.items():
            # Search for documentation blocks in this project
            docs = manifest.get("docs", {})
            if not isinstance(docs, dict):
                logger.warning(f"Invalid manifest structure in project {proj_id}: 'docs' is not a dictionary")
                continue
            
            # Find matching documentation blocks
            for doc_id, doc_info in docs.items():
                if (isinstance(doc_info, dict) and 
                    doc_info.get("resource_type") == "doc" and
                    doc_info.get("name") == doc_name):
                    all_matching_docs.append((proj_id, doc_id, doc_info))
        
        if not all_matching_docs:
            resource_info = f" in resources {resource_id}" if resource_id else ""
            return create_resource_not_found_error(doc_name, resource_info, "Documentation block")
        
        # Format response for all matching docs
        response_lines = [
            f"# Documentation: {doc_name}",
            ""
        ]
        
        if len(all_matching_docs) > 1:
            response_lines.append(f"Found {len(all_matching_docs)} documentation blocks across projects:")
            response_lines.append("")
        
        for proj_id, doc_id, doc_info in all_matching_docs:
            response_lines.extend([
                f"## Project: {proj_id}",
                f"**Package:** {doc_info.get('package_name', 'Unknown Package')}",
                f"**Document ID:** {doc_id}",
                f"**Path:** {doc_info.get('original_file_path', 'Unknown path')}",
                ""
            ])
            
            # Add the actual content
            block_contents = doc_info.get("block_contents", "")
            if block_contents:
                response_lines.extend([
                    "### Content",
                    "",
                    block_contents,
                    "",
                    "---",
                    ""
                ])
            else:
                response_lines.extend([
                    "*No content available*",
                    "",
                    "---",
                    ""
                ])
        
        return [TextContent(type="text", text="\n".join(response_lines))]
        
    except FileNotFoundError as e:
        logger.error(f"File not found in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Required dbt artifacts not found: {str(e)}"
        )]
    except ValueError as e:
        logger.error(f"Invalid input in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"Unexpected error in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving description: {str(e)}"
        )]
