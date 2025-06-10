"""
dbt CLI tools package for executing dbt commands.

This package provides tools for interacting with dbt CLI functionality
including listing resources, compiling models, and running inline queries.
"""

from .dbt_list import dbt_list_tool, handle_dbt_list
from .dbt_compile import dbt_compile_tool, handle_dbt_compile
from .dbt_show import dbt_show_tool, handle_dbt_show
from .utils import run_dbt_command, get_dbt_path, get_project_dir

# Legacy compatibility functions
def get_dbt_cli_tools():
    """Get list of available dbt CLI tools."""
    return [
        dbt_list_tool(),
        dbt_compile_tool(),
        dbt_show_tool()
    ]

async def handle_dbt_cli_tool(name: str, arguments):
    """Handle dbt CLI tool calls - legacy compatibility function."""
    if name == "dbt_list":
        return await handle_dbt_list(arguments)
    elif name == "dbt_compile":
        return await handle_dbt_compile(arguments)
    elif name == "dbt_show":
        return await handle_dbt_show(arguments)
    else:
        raise ValueError(f"Unknown dbt CLI tool: {name}")

def is_dbt_cli_tool(tool_name: str) -> bool:
    """Check if a tool name corresponds to a dbt CLI tool."""
    return tool_name in ["dbt_list", "dbt_compile", "dbt_show"]

__all__ = [
    "dbt_list_tool",
    "handle_dbt_list",
    "dbt_compile_tool", 
    "handle_dbt_compile",
    "dbt_show_tool",
    "handle_dbt_show",
    "get_dbt_cli_tools",
    "handle_dbt_cli_tool",
    "is_dbt_cli_tool",
    "run_dbt_command",
    "get_dbt_path",
    "get_project_dir"
]
