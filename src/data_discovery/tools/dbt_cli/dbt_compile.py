"""
dbt_compile tool for compiling dbt models to generate SQL.

Compiles dbt models to generate SQL, parsing the project and compiling Jinja templates 
into raw SQL without executing against the warehouse.
"""
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
import logging

from data_discovery.prompts import get_prompt
from .utils import run_dbt_command, validate_selector

logger = logging.getLogger(__name__)


def dbt_compile_tool() -> Tool:
    """Tool definition for dbt_compile."""
    return Tool(
        name="dbt_compile",
        description="Compile dbt models to generate SQL. This parses the project and compiles Jinja templates into raw SQL without executing against the warehouse.",
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


async def handle_dbt_compile(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle the dbt_compile tool invocation."""
    try:
        selector = validate_selector(arguments.get("selector"))
        output = run_dbt_command(["compile"], selector)
        return [TextContent(type="text", text=output)]
    
    except ValueError as e:
        logger.error(f"Invalid input for dbt_compile: {e}")
        return [TextContent(type="text", text=f"Invalid input: {str(e)}", isError=True)]
    except Exception as e:
        logger.error(f"Error executing dbt_compile: {e}")
        return [TextContent(type="text", text=f"Error executing dbt command: {str(e)}", isError=True)]
