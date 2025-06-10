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
                "project_id": {
                    "type": ["string", "array"],
                    "description": "Project ID(s) to search in. Can be a single project ID string or array of project IDs (max 5). REQUIRED to avoid cross-contamination of blockchain-specific documentation.",
                    "items": {
                        "type": "string"
                    },
                    "maxItems": 5
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        }
    )


async def handle_get_description(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_description tool invocation."""
    try:
        # Extract arguments
        doc_name = arguments.get("doc_name", "__MCP__")
        project_id = arguments.get("project_id")
        
        if not isinstance(doc_name, str) or not doc_name.strip():
            raise ValueError("doc_name must be a non-empty string")
        
        doc_name = doc_name.strip()
        
        # Prevent path traversal and injection attempts
        if any(char in doc_name for char in ['/', '\\', '..', '\x00']):
            raise ValueError("doc_name contains invalid characters")
        
        # Require project_id to avoid cross-contamination of blockchain-specific context
        if not project_id:
            from fsc_dbt_mcp.resources import resource_registry
            available_projects = resource_registry.list_project_ids()
            return [TextContent(
                type="text",
                text=f"project_id is required for get_description to avoid cross-contamination of blockchain-specific documentation. Please specify which project(s) to search. Available projects: {available_projects}"
            )]
        
        # Load project artifacts
        artifacts = await project_manager.get_project_artifacts(project_id)
        if not artifacts:
            from fsc_dbt_mcp.resources import resource_registry
            available_projects = resource_registry.list_project_ids()
            return [TextContent(
                type="text",
                text=f"No project artifacts could be loaded. Available projects: {available_projects}"
            )]
        
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
            from fsc_dbt_mcp.resources import resource_registry
            available_projects = resource_registry.list_project_ids()
            project_info = f" in projects {project_id}" if project_id else " in any available projects"
            return [TextContent(
                type="text",
                text=f"No documentation blocks found with name '{doc_name}'{project_info}. Available projects: {available_projects}"
            )]
        
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