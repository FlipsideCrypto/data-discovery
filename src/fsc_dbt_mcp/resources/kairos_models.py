"""
Kairos Models project resource definition.
"""
from typing import Dict, Any
from mcp import types

# Resource metadata
RESOURCE_URI = "dbt://project/kairos-models"
RESOURCE_NAME = "Kairos Models Project"
RESOURCE_DESCRIPTION = "Flipside developed stats and metrics models across all blockchains"

def get_resource_definition() -> types.Resource:
    """Get the MCP Resource definition for Kairos Models project."""
    return types.Resource(
        uri=RESOURCE_URI,
        name=RESOURCE_NAME,
        description=RESOURCE_DESCRIPTION,
        mimeType="application/json"
    )

def get_resource_data() -> Dict[str, Any]:
    """Get the project data for Kairos Models."""
    return {
        "id": "kairos-models",
        "name": "Kairos Models", 
        "description": "Flipside developed stats and metrics models across all blockchains",
        "location": "/Users/jackforgash/gh/fs/kairos-models", 
        "type": "local",
        "aliases": ["kairos", "metrics", "stats"],
        "blockchain": "multi-chain",
        "artifact_location": {
            "manifest": "/Users/jackforgash/gh/fs/kairos-models/target/manifest.json",
            "catalog": "/Users/jackforgash/gh/fs/kairos-models/target/catalog.json"
        },
        "schemas": ["core", "metrics", "aggregates"],
        "documentation": "Cross-chain statistics and metrics models providing unified analytics across multiple blockchain networks",
        "features": [
            "Cross-chain metrics",
            "Protocol statistics",
            "Market analytics",
            "User behavior insights",
            "Network health indicators",
            "Comparative blockchain analysis"
        ],
        "supported_chains": [
            "bitcoin",
            "ethereum", 
            "solana",
            "avalanche",
            "polygon",
            "arbitrum",
            "optimism"
        ],
        "last_updated": "2024-12-01",
        "models_count": 85
    }