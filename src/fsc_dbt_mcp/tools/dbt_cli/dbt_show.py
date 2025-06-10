"""
dbt_show tool for executing inline SQL queries with sample results.

Runs a query against the data warehouse returning a data sample.
"""
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
import logging

from fsc_dbt_mcp.prompts import get_prompt
from .utils import run_dbt_command

logger = logging.getLogger(__name__)


def dbt_show_tool() -> Tool:
    """Tool definition for dbt_show."""
    return Tool(
        name="dbt_show",
        description=get_prompt("dbt_cli/dbt_show"),
        inputSchema={
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The SQL query to execute. Do not include a LIMIT clause. Do not use the dbt ref() syntax."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return (optional)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["sql_query"],
            "additionalProperties": False
        },
    )


def _validate_sql_query(sql_query: str) -> str:
    """Validate and sanitize SQL query input."""
    if not isinstance(sql_query, str):
        raise ValueError("sql_query must be a string")
    
    sql_query = sql_query.strip()
    if not sql_query:
        raise ValueError("sql_query cannot be empty")
    
    # Basic security checks - prevent obviously dangerous patterns
    dangerous_patterns = [
        "drop ", "delete ", "truncate ", "insert ", "update ",
        "create ", "alter ", "grant ", "revoke ", "--", "/*", "*/"
    ]
    
    sql_lower = sql_query.lower()
    for pattern in dangerous_patterns:
        if pattern in sql_lower:
            raise ValueError(f"SQL query contains potentially dangerous pattern: {pattern.strip()}")
    
    return sql_query


def _validate_limit(limit: int) -> int:
    """Validate and sanitize limit parameter."""
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    
    # Ensure limit is between 1 and 10
    return min(max(1, limit), 10)


async def handle_dbt_show(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle the dbt_show tool invocation."""
    try:
        sql_query = arguments.get("sql_query")
        if not sql_query:
            raise ValueError("sql_query is required for dbt_show")
        
        # Validate inputs
        sql_query = _validate_sql_query(sql_query)
        limit = _validate_limit(arguments.get("limit", 5))
        
        # Build dbt show command
        args = ["show", "--inline", sql_query, "--favor-state", "--limit", str(limit), "--output", "json"]
        
        output = run_dbt_command(args)
        return [TextContent(type="text", text=output)]
    
    except ValueError as e:
        logger.error(f"Invalid input for dbt_show: {e}")
        return [TextContent(type="text", text=f"Invalid input: {str(e)}")]
    except Exception as e:
        logger.error(f"Error executing dbt_show: {e}")
        return [TextContent(type="text", text=f"Error executing dbt command: {str(e)}")]
