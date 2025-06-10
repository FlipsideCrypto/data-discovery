"""
Bitcoin Models project resource definition.
"""
from typing import Dict, Any
from mcp import types

# Resource metadata
RESOURCE_URI = "dbt://project/bitcoin-models"
RESOURCE_NAME = "Bitcoin Models Project"
RESOURCE_DESCRIPTION = "dbt models for Bitcoin blockchain data analysis"

def get_resource_definition() -> types.Resource:
    """Get the MCP Resource definition for Bitcoin Models project."""
    return types.Resource(
        uri=RESOURCE_URI,
        name=RESOURCE_NAME,
        description=RESOURCE_DESCRIPTION,
        mimeType="application/json"
    )

def get_resource_data() -> Dict[str, Any]:
    """Get the project data for Bitcoin Models."""
    return {
        "id": "bitcoin-models",
        "name": "Bitcoin Models",
        "description": "dbt models for Bitcoin blockchain data analysis and exploration",
        "location": "/Users/jackforgash/gh/fs/bitcoin-models",
        "type": "local",
        "aliases": ["bitcoin", "btc"],
        "blockchain": "bitcoin",
        "artifact_location": {
            "manifest": "/Users/jackforgash/gh/fs/bitcoin-models/target/manifest.json",
            "catalog": "/Users/jackforgash/gh/fs/bitcoin-models/target/catalog.json"
        },
        "schemas": ["core", "bronze", "silver", "gold"],
        "documentation": "Comprehensive Bitcoin blockchain data models including transactions, blocks, addresses, and derived analytics",
        "features": [
            "Transaction analysis",
            "Block exploration", 
            "Address clustering",
            "UTXO tracking",
            "Fee analysis"
        ],
        "last_updated": "2024-12-01",
        "models_count": 45
    }