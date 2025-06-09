"""
Prompt management for fsc-dbt-mcp server.

Provides a simple interface to load prompt content from markdown files,
following the same pattern as dbt-labs/dbt-mcp.
"""

from pathlib import Path


def get_prompt(name: str) -> str:
    """
    Load prompt content from a markdown file.
    
    Args:
        name: The name of the prompt file (without .md extension)
        
    Returns:
        The content of the prompt file as a string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_file = Path(__file__).parent / f"{name}.md"
    return prompt_file.read_text()