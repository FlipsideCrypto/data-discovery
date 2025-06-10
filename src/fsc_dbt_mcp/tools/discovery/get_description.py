"""
get_description tool for retrieving documentation blocks from dbt manifest.

Follows MCP best practices for input validation, error handling, and security.
"""
from typing import Dict, Any
from mcp.types import Tool, TextContent
import logging

from fsc_dbt_mcp.prompts import get_prompt
from .utils import load_dbt_artifacts

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
                }
            },
            "additionalProperties": False
        }
    )


async def handle_get_description(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_description tool invocation."""
    try:
        # Extract doc_name argument (default to '__MCP__')
        doc_name = arguments.get("doc_name", "__MCP__")
        
        if not isinstance(doc_name, str) or not doc_name.strip():
            raise ValueError("doc_name must be a non-empty string")
        
        doc_name = doc_name.strip()
        
        # Prevent path traversal and injection attempts
        if any(char in doc_name for char in ['/', '\\', '..', '\x00']):
            raise ValueError("doc_name contains invalid characters")
        
        # Load manifest artifact
        manifest, _ = load_dbt_artifacts()
        
        # Search for documentation blocks
        docs = manifest.get("docs", {})
        if not isinstance(docs, dict):
            raise ValueError("Invalid manifest structure: 'docs' is not a dictionary")
        
        # Find matching documentation blocks
        matching_docs = []
        for doc_id, doc_info in docs.items():
            if (isinstance(doc_info, dict) and 
                doc_info.get("resource_type") == "doc" and
                doc_info.get("name") == doc_name):
                matching_docs.append((doc_id, doc_info))
        
        if not matching_docs:
            return [TextContent(
                type="text",
                text=f"No documentation blocks found with name '{doc_name}'"
            )]
        
        # Format response for all matching docs
        response_lines = [
            f"# Documentation: {doc_name}",
            ""
        ]
        
        for doc_id, doc_info in matching_docs:
            response_lines.extend([
                f"## {doc_info.get('package_name', 'Unknown Package')}",
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