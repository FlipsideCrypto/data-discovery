"""
dbt CLI tools integration for fsc-dbt-mcp server.

Implements specific dbt CLI tools:
- list: Lists resources in the dbt project
- compile: Compile models
- show: Runs a query against the data warehouse returning a data sample
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from mcp.types import Tool, TextContent

# Import the prompt system
from fsc_dbt_mcp.prompts.prompts import get_prompt

logger = logging.getLogger(__name__)


def _get_dbt_path() -> str:
    """Get the path to the dbt executable."""
    # Check for DBT_PATH environment variable first
    dbt_path = os.getenv('DBT_PATH', 'dbt')
    return dbt_path


def _get_project_dir() -> str:
    """Get the dbt project directory."""
    return os.getenv('DBT_PROJECT_DIR', os.getcwd())


def _run_dbt_command(command: List[str], selector: Optional[str] = None) -> str:
    """Execute a dbt command and return the output."""
    project_dir = _get_project_dir()
    dbt_path = _get_dbt_path()
    
    # Log the project directory and dbt path
    logger.info(f"Project directory: {project_dir}")
    logger.info(f"dbt path: {dbt_path}")

    # Commands that should always be quiet to reduce output verbosity
    verbose_commands = ["build", "compile", "docs", "parse", "run", "test"]
    
    if selector:
        selector_str = str(selector)
        if not selector_str.startswith("-s"):
            selector_str = f"-s {selector_str}"
        selector_params = selector_str.split(" ")
        command = command + selector_params
    
    full_command = command.copy()
    # Add --quiet flag to specific commands to reduce context window usage
    if len(full_command) > 0 and full_command[0] in verbose_commands:
        main_command = full_command[0]
        command_args = full_command[1:] if len(full_command) > 1 else []
        full_command = [main_command, "--quiet", *command_args]
    
    # Make the format json to make it easier to parse for the LLM
    full_command = full_command + ["--log-format", "json"]
    
    try:
        full_cmd_str = ' '.join([dbt_path] + full_command)
        logger.info(f"Executing dbt command: {full_cmd_str}")
        print(f"🚀 dbt command: {full_cmd_str}")
        
        process = subprocess.Popen(
            args=[dbt_path, *full_command],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output, _ = process.communicate()
        
        if process.returncode != 0:
            logger.warning(f"dbt command returned non-zero exit code: {process.returncode}")
            print(f"⚠️  dbt command exited with code: {process.returncode}")

        else:
            print(f"✅ dbt command completed successfully")
        
        return output or "OK"
    except FileNotFoundError:
        raise ValueError("dbt command not found. Please ensure dbt is installed and available in PATH.")
    except Exception as e:
        raise RuntimeError(f"Failed to execute dbt command: {str(e)}")


def get_dbt_cli_tools() -> List[Tool]:
    """Get list of available dbt CLI tools."""
    tools = [
        Tool(
            name="dbt_list", 
            description="List dbt resources in the project such as models, tests, sources, etc. Useful for discovering what's available in the dbt project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": get_prompt("dbt_cli/selector")
                    }
                }
            }
        ),
        Tool(
            name="dbt_compile",
            description="Compile dbt models to generate SQL. This parses the project and compiles Jinja templates into raw SQL without executing against the warehouse.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": get_prompt("dbt_cli/selector")
                    }
                }
            }
        ),
        Tool(
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
                "required": ["sql_query"]
            }
        )
    ]
    
    logger.info(f"Created {len(tools)} dbt CLI tools")
    return tools


async def handle_dbt_cli_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle dbt CLI tool calls."""
    try:
        if name == "dbt_list":
            selector = arguments.get("selector")
            output = _run_dbt_command(["ls"], selector)
            return [TextContent(type="text", text=output)]
        
        elif name == "dbt_compile":
            output = _run_dbt_command(["compile"])
            return [TextContent(type="text", text=output)]
        
        elif name == "dbt_show":
            sql_query = arguments.get("sql_query")
            if not sql_query:
                raise ValueError("sql_query is required for dbt_show")
            
            limit = arguments.get("limit", 5)  # Default to 5 if not specified
            limit = min(max(1, limit), 10)  # Ensure limit is between 1 and 10
            args = ["show", "--inline", sql_query, "--favor-state", "--limit", str(limit), "--output", "json"]
            
            output = _run_dbt_command(args)
            return [TextContent(type="text", text=output)]
        
        else:
            available_tools = ["dbt_list", "dbt_compile", "dbt_show"]
            error_msg = f"Unknown dbt CLI tool: {name}. Available tools: {available_tools}"
            logger.error(error_msg)
            return [TextContent(type="text", text=error_msg)]
    
    except ValueError as e:
        logger.error(f"Invalid input for dbt CLI tool '{name}': {e}")
        return [TextContent(type="text", text=f"Invalid input: {str(e)}")]
    except Exception as e:
        logger.error(f"Error executing dbt CLI tool '{name}': {e}")
        return [TextContent(type="text", text=f"Error executing dbt command: {str(e)}")]


def is_dbt_cli_tool(tool_name: str) -> bool:
    """Check if a tool name corresponds to a dbt CLI tool."""
    return tool_name in ["dbt_list", "dbt_compile", "dbt_show"]