"""
Prompt management for data-discovery server. Allows tool descriptions to be loaded from markdown files.
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
