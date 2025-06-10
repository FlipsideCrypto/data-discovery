"""
Generic dbt project resource for FlipsideCrypto blockchain projects.

This module provides a standardized way to define dbt project resources
using CSV data, eliminating the need for individual Python files for each project.
"""
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp import types
import logging

logger = logging.getLogger(__name__)


class DbtProjectResource:
    """Generic dbt project resource that can be configured from CSV data."""
    
    def __init__(self, project_data: Dict[str, Any]):
        """Initialize with project data from CSV."""
        self.data = project_data
        self.id = project_data["id"]
        self.name = project_data["name"]
        self.blockchain = project_data["blockchain"]
        self.type = project_data["type"]
        
        # Generate description if not provided
        self.description = project_data.get("description") or f"dbt models for {self.blockchain} blockchain data analysis and exploration"
        
    def get_resource_definition(self) -> types.Resource:
        """Get the MCP Resource definition for this project."""
        return types.Resource(
            uri=f"dbt://project/{self.id}",
            name=self.name,
            description=self.description,
            mimeType="application/json"
        )
    
    def get_resource_data(self) -> Dict[str, Any]:
        """Get the complete project data."""
        # Base data from CSV
        resource_data = dict(self.data)
        
        # Add generated description
        resource_data["description"] = self.description
        
        # Generate aliases if not provided
        if "aliases" not in resource_data or not resource_data["aliases"]:
            resource_data["aliases"] = self._generate_aliases()
        
        # Generate artifact locations based on type
        if self.type == "github":
            resource_data["artifact_location"] = self._generate_github_artifact_urls()
        elif self.type == "local":
            resource_data["artifact_location"] = self._generate_local_artifact_paths()
        
        # Default schemas if not provided
        if "schemas" not in resource_data or not resource_data["schemas"]:
            resource_data["schemas"] = ["core", "bronze", "silver", "gold"]
        
        return resource_data
    
    def _generate_aliases(self) -> List[str]:
        """Generate common aliases for the project."""
        aliases = [self.id]
        
        # Add blockchain name
        aliases.append(self.blockchain)
        
        # Add common variations
        if "-models" in self.id:
            base_name = self.id.replace("-models", "")
            aliases.extend([
                base_name,
                f"{base_name}_models",
                f"{base_name}-models"
            ])
        
        # Add common blockchain abbreviations
        blockchain_abbrevs = {
            "bitcoin": ["btc"],
            "ethereum": ["eth"],
            "polygon": ["matic", "poly"],
            "avalanche": ["avax"],
            "binance": ["bsc", "bnb"],
            "solana": ["sol"],
            "arbitrum": ["arb"],
            "optimism": ["op"]
        }
        
        if self.blockchain in blockchain_abbrevs:
            aliases.extend(blockchain_abbrevs[self.blockchain])
        
        return list(set(aliases))  # Remove duplicates
    
    def _generate_github_artifact_urls(self) -> Dict[str, str]:
        """Generate GitHub raw URLs for manifest and catalog."""
        location = self.data.get("location")
        if not location:
            raise ValueError(f"GitHub project {self.id} must specify 'location' field with repository path")
        
        # If location doesn't contain '/', assume it's just the repo name under FlipsideCrypto
        if '/' not in location:
            github_repo = f"FlipsideCrypto/{location}"
        else:
            github_repo = location
        
        branch = self.data.get("target_branch", "main")
        base_url = f"https://raw.githubusercontent.com/{github_repo}/{branch}/target"
        
        return {
            "manifest": f"{base_url}/manifest.json",
            "catalog": f"{base_url}/catalog.json"
        }
    
    def _generate_local_artifact_paths(self) -> Dict[str, str]:
        """Generate local file paths for manifest and catalog."""
        location = self.data.get("location")
        if not location:
            raise ValueError(f"Local project {self.id} must specify 'location' field")
        
        return {
            "manifest": os.path.join(location, "target", "manifest.json"),
            "catalog": os.path.join(location, "target", "catalog.json")
        }


class DbtProjectResourceLoader:
    """Loads dbt project resources from CSV configuration."""
    
    def __init__(self, csv_path: Optional[str] = None):
        """Initialize with path to CSV file."""
        if csv_path is None:
            # Default to resources directory
            resources_dir = Path(__file__).parent
            csv_path = resources_dir / "dbt_projects.csv"
        
        self.csv_path = Path(csv_path)
        self._projects: Dict[str, DbtProjectResource] = {}
        self._load_projects()
    
    def _load_projects(self):
        """Load projects from CSV file."""
        if not self.csv_path.exists():
            logger.warning(f"dbt projects CSV not found at {self.csv_path}")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Skip empty rows or commented rows
                    if not row.get('id') or row.get('id', '').startswith('#'):
                        continue
                    
                    # Parse list fields
                    row = self._parse_csv_row(row)
                    
                    # Validate required fields
                    self._validate_project_data(row)
                    
                    # Create resource
                    project = DbtProjectResource(row)
                    self._projects[project.id] = project
                    
            logger.info(f"Loaded {len(self._projects)} dbt projects from CSV")
            
        except Exception as e:
            logger.error(f"Error loading dbt projects CSV: {e}")
            raise
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse CSV row, handling list fields and type conversion."""
        parsed = {}
        
        for key, value in row.items():
            if not value or value.strip() == '':
                parsed[key] = None
                continue
            
            value = value.strip()
            
            # Handle list fields (pipe-separated to avoid CSV issues)
            if key in ['aliases', 'schemas']:
                parsed[key] = [item.strip() for item in value.split('|') if item.strip()]
            else:
                parsed[key] = value
        
        return parsed
    
    def _validate_project_data(self, data: Dict[str, Any]):
        """Validate required fields in project data."""
        required_fields = ['id', 'name', 'blockchain', 'category', 'type', 'location']
        
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field '{field}' in project data")
        
        # Validate project ID format
        project_id = data['id']
        if not project_id.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid project ID '{project_id}': must contain only letters, numbers, hyphens, and underscores")
        
        # Validate type
        if data['type'] not in ['local', 'github']:
            raise ValueError(f"Invalid project type '{data['type']}': must be 'local' or 'github'")
    
    def get_all_projects(self) -> Dict[str, DbtProjectResource]:
        """Get all loaded projects."""
        return self._projects.copy()
    
    def get_project(self, project_id: str) -> Optional[DbtProjectResource]:
        """Get a specific project by ID."""
        return self._projects.get(project_id)
    
    def list_project_ids(self) -> List[str]:
        """Get list of all project IDs."""
        return list(self._projects.keys())
    
    def reload(self):
        """Reload projects from CSV file."""
        self._projects.clear()
        self._load_projects()


# Global instance for easy access
dbt_project_loader = DbtProjectResourceLoader()