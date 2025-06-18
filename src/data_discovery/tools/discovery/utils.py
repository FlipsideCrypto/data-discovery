"""
Shared utilities for discovery tools.

Minimal utilities for resource management and shared functionality.
"""
from typing import List


def get_available_resources() -> List[str]:
    """Get list of available resource IDs from resource registry."""
    from data_discovery.resources import resource_registry
    return resource_registry.list_project_ids()

