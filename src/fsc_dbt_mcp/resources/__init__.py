"""
MCP Resources package for dbt project discovery.

This package provides MCP resources for exposing dbt project information
to AI models through the Model Context Protocol.
"""

import json
from typing import Dict, Any, List
from mcp import types

from .bitcoin_models import get_resource_definition as bitcoin_definition, get_resource_data as bitcoin_data
from .ethereum_models import get_resource_definition as ethereum_definition, get_resource_data as ethereum_data
from .kairos_models import get_resource_definition as kairos_definition, get_resource_data as kairos_data


class ResourceRegistry:
    """Registry for managing MCP resources."""
    
    def __init__(self):
        self._project_resources = {
            "dbt://project/bitcoin-models": {
                "definition": bitcoin_definition,
                "data": bitcoin_data
            },
            "dbt://project/ethereum-models": {
                "definition": ethereum_definition,
                "data": ethereum_data
            },
            "dbt://project/kairos-models": {
                "definition": kairos_definition,
                "data": kairos_data
            }
        }
    
    def list_all_resources(self) -> List[types.Resource]:
        """Get list of all available MCP resources."""
        resources = []
        
        # Add individual project resources
        for uri, resource_info in self._project_resources.items():
            resources.append(resource_info["definition"]())
        
        # Add project index resource
        resources.append(types.Resource(
            uri="dbt://projects",
            name="Available dbt Projects",
            description="Index of all available dbt projects with metadata",
            mimeType="application/json"
        ))
        
        return resources
    
    def get_resource_content(self, uri: str) -> str:
        """Get resource content by URI."""
        if uri in self._project_resources:
            # Individual project resource
            data = self._project_resources[uri]["data"]()
            return json.dumps(data, indent=2)
        
        elif uri == "dbt://projects":
            # Project index resource
            projects_index = self._build_projects_index()
            return json.dumps(projects_index, indent=2)
        
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    def _build_projects_index(self) -> Dict[str, Any]:
        """Build the projects index from all available projects."""
        projects = []
        
        for uri, resource_info in self._project_resources.items():
            project_data = resource_info["data"]()
            projects.append({
                "id": project_data["id"],
                "name": project_data["name"],
                "resource_uri": uri,
                "blockchain": project_data["blockchain"],
                "type": project_data["type"],
                "description": project_data["description"]
            })
        
        return {
            "projects": projects,
            "total_projects": len(projects),
            "resource_uri": "dbt://projects"
        }
    
    def get_project_by_id(self, project_id: str) -> Dict[str, Any]:
        """Get project data by project ID."""
        uri = f"dbt://project/{project_id}"
        if uri in self._project_resources:
            return self._project_resources[uri]["data"]()
        else:
            raise ValueError(f"Unknown project ID: {project_id}")
    
    def list_project_ids(self) -> List[str]:
        """Get list of all project IDs."""
        project_ids = []
        for uri, resource_info in self._project_resources.items():
            project_data = resource_info["data"]()
            project_ids.append(project_data["id"])
        return project_ids


# Global resource registry instance
resource_registry = ResourceRegistry()

__all__ = [
    "ResourceRegistry",
    "resource_registry"
]
