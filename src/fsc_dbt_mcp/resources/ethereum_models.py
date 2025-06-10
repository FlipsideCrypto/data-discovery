"""
Ethereum Models project resource definition.
"""
from typing import Dict, Any
from mcp import types

# Resource metadata
RESOURCE_URI = "dbt://project/ethereum-models"
RESOURCE_NAME = "Ethereum Models Project"
RESOURCE_DESCRIPTION = "dbt models for Ethereum blockchain data analysis"

def get_resource_definition() -> types.Resource:
    """Get the MCP Resource definition for Ethereum Models project."""
    return types.Resource(
        uri=RESOURCE_URI,
        name=RESOURCE_NAME,
        description=RESOURCE_DESCRIPTION,
        mimeType="application/json"
    )

def get_resource_data() -> Dict[str, Any]:
    """Get the project data for Ethereum Models."""
    return {
        "id": "ethereum-models", 
        "name": "Ethereum Models",
        "description": "dbt models for Ethereum blockchain data analysis and exploration",
        "location": "flipside-crypto/ethereum-models",
        "type": "github",
        "aliases": ["ethereum", "eth", "mainnet"],
        "blockchain": "ethereum",
        "artifact_location": {
            "manifest": "https://raw.githubusercontent.com/FlipsideCrypto/ethereum-models/refs/heads/docs/docs/manifest.json",
            "catalog": "https://raw.githubusercontent.com/FlipsideCrypto/ethereum-models/refs/heads/docs/docs/catalog.json"
        },
        "schemas": ["core", "defi", "nft", "bronze", "silver", "gold"],
        "documentation": "Comprehensive Ethereum blockchain data models including transactions, events, DeFi protocols, and NFT analytics",
        "features": [
            "Transaction analysis",
            "Smart contract events",
            "DeFi protocol tracking",
            "NFT marketplace data",
            "Gas optimization insights",
            "ERC20 token analytics"
        ],
        "last_updated": "2024-12-01",
        "models_count": 120
    }