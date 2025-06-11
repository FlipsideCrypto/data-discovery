"""
Shared utilities for dbt CLI tools.

Provides common functions for executing dbt commands and managing configurations.
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def get_dbt_path() -> str:
    """Get the path to the dbt executable."""
    # Check for DBT_PATH environment variable first
    dbt_path = os.getenv('DBT_PATH', 'dbt')
    return dbt_path


def get_project_dir() -> str:
    """Get the dbt project directory."""
    return os.getenv('DBT_PROJECT_DIR', os.getcwd())


def run_dbt_command(command: List[str], selector: Optional[str] = None) -> str:
    """Execute a dbt command and return the output."""
    project_dir = get_project_dir()
    dbt_path = get_dbt_path()
    
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


def validate_selector(selector: Optional[str]) -> Optional[str]:
    """Validate and sanitize selector input."""
    if selector is None:
        return None
    
    if not isinstance(selector, str):
        raise ValueError("selector must be a string")
    
    selector = selector.strip()
    if not selector:
        return None
    
    # Basic security check - prevent command injection
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '{', '}']
    for char in dangerous_chars:
        if char in selector:
            raise ValueError(f"selector contains invalid character: {char}")
    
    return selector
