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
from .utils import create_error_response, create_resource_not_found_error, create_no_artifacts_error
from .properties import ToolPropertySet, DOC_NAME, REQUIRED_RESOURCE_ID

logger = logging.getLogger(__name__)

# Define tool properties
_tool_properties = ToolPropertySet({
    "doc_name": DOC_NAME,
    "resource_id": REQUIRED_RESOURCE_ID
})


def get_description_tool() -> Tool:
    """Tool definition for get_description."""
    return Tool(
        name="get_description",
        description=get_prompt("discovery/get_description"),
        inputSchema=_tool_properties.get_input_schema(required_properties=["resource_id"]),
        annotations={
            "title": "Get Documentation",
            "readOnlyHint": True
        }
    )


async def handle_get_description(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle the get_description tool invocation."""
    try:
        # Validate and extract all arguments using properties
        logger.debug(f"[GET_DESC] Called with arguments: {arguments}")
        params = _tool_properties.validate_and_extract_all(arguments)
        doc_name = params["doc_name"]
        resource_id = params["resource_id"]
        logger.debug(f"[GET_DESC] Extracted params - doc_name: {doc_name}, resource_id: {resource_id}")
        
        # Require resource_id to avoid cross-contamination of blockchain-specific context
        if not resource_id:
            logger.debug(f"[GET_DESC] resource_id is required but was not provided")
            return [TextContent(
                type="text",
                text="resource_id is required for get_description to avoid cross-contamination of blockchain-specific documentation. Please specify which project(s) to search",
                isError=True
            )]
        
        # Load project artifacts
        logger.debug(f"[GET_DESC] Loading artifacts for resource_id: {resource_id}")
        artifacts = await project_manager.get_project_artifacts(resource_id)
        if not artifacts:
            logger.debug(f"[GET_DESC] No artifacts found")
            return create_no_artifacts_error()
        
        # Search for documentation blocks across all specified projects
        all_matching_docs = []
        logger.debug(f"[GET_DESC] Searching for doc_name '{doc_name}' in {len(artifacts)} projects")
        
        for proj_id, (manifest, _) in artifacts.items():
            logger.debug(f"[GET_DESC] Searching in project: {proj_id}")
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
            logger.debug(f"[GET_DESC] No matching docs found for '{doc_name}'")
            resource_info = f" in resources {resource_id}" if resource_id else ""
            return create_resource_not_found_error(doc_name, resource_info, "Documentation block")
        
        logger.debug(f"[GET_DESC] Found {len(all_matching_docs)} matching documentation blocks")
        
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
            text=f"Required dbt artifacts not found: {str(e)}",
            isError=True
        )]
    except ValueError as e:
        logger.error(f"Invalid input in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Invalid input: {str(e)}",
            isError=True
        )]
    except Exception as e:
        logger.error(f"Unexpected error in get_description: {e}")
        return [TextContent(
            type="text",
            text=f"Internal error retrieving description: {str(e)}",
            isError=True
        )]
