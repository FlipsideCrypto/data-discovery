"""
API package for shared service layer.

Provides core data discovery functionality that can be used by both:
- MCP server (returning MCP TextContent responses)
- REST API server (returning JSON objects)
"""

from .service import DataDiscoveryService

__all__ = [
    "DataDiscoveryService"
]