"""
dbt_list tool for listing dbt resources in the project.

Lists dbt resources such as models, tests, sources, etc.
"""
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
import logging

from data_discovery.prompts import get_prompt
from .utils import run_dbt_command, validate_selector

logger = logging.getLogger(__name__)


def dbt_list_tool() -> Tool:
    """Tool definition for dbt_list."""
    return Tool(
        name="dbt_list", 
        description="List dbt resources in the project such as models, tests, sources, etc. Useful for discovering what's available in the dbt project.",
        inputSchema={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": get_prompt("dbt_cli/selector")
                }
            },
            "additionalProperties": True
        }
    )


async def handle_dbt_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle the dbt_list tool invocation."""
    try:
        selector = validate_selector(arguments.get("selector"))
        output = run_dbt_command(["ls"], selector)
        return [TextContent(type="text", text=output)]
    
    except ValueError as e:
        logger.error(f"Invalid input for dbt_list: {e}")
        return [TextContent(type="text", text=f"Invalid input: {str(e)}", isError=True)]
    except Exception as e:
        logger.error(f"Error executing dbt_list: {e}")
        return [TextContent(type="text", text=f"Error executing dbt command: {str(e)}", isError=True)]
