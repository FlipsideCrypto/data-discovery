"""
MCP Resources package for dbt project discovery.

This package provides MCP resources for exposing dbt project information
to AI models through the Model Context Protocol.

"""

import json
from typing import Dict, Any, List
from mcp import types
import logging

from .dbt_project_resource import dbt_project_loader

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """Registry for managing MCP resources with CSV-driven dbt projects."""
    
    def __init__(self):
        # Load projects from CSV
        self._refresh_projects()
    
    def _refresh_projects(self):
        """Refresh projects from CSV loader."""
        try:
            # Reload CSV data
            dbt_project_loader.reload()
            logger.info("Refreshed dbt projects from CSV")
        except Exception as e:
            logger.error(f"Failed to refresh dbt projects: {e}")
            raise
    
    def list_all_resources(self) -> List[types.Resource]:
        """Get list of all available MCP resources."""
        resources = []
        
        # Add individual project resources from CSV
        for project in dbt_project_loader.get_all_projects().values():
            resources.append(project.get_resource_definition())
        
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
        if uri.startswith("dbt://project/"):
            # Individual project resource
            project_id = uri.replace("dbt://project/", "")
            project = dbt_project_loader.get_project(project_id)
            if project:
                data = project.get_resource_data()
                return json.dumps(data, indent=2)
            else:
                raise ValueError(f"Unknown project ID: {project_id}")
        
        elif uri == "dbt://projects":
            # Project index resource
            projects_index = self._build_projects_index()
            return json.dumps(projects_index, indent=2)
        
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    def _build_projects_index(self) -> Dict[str, Any]:
        """Build the projects index from all available projects."""
        projects = []
        
        for project in dbt_project_loader.get_all_projects().values():
            project_data = project.get_resource_data()
            projects.append({
                "id": project_data["id"],
                "name": project_data["name"],
                "resource_uri": f"dbt://project/{project_data['id']}",
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
        project = dbt_project_loader.get_project(project_id)
        if project:
            return project.get_resource_data()
        else:
            raise ValueError(f"Unknown project ID: {project_id}")
    
    def list_project_ids(self) -> List[str]:
        """Get list of all project IDs."""
        return dbt_project_loader.list_project_ids()
    
    def refresh_projects(self):
        """Refresh projects from CSV file (useful for hot reloading)."""
        self._refresh_projects()


# Global resource registry instance
resource_registry = ResourceRegistry()

__all__ = [
    "ResourceRegistry",
    "resource_registry"
]
