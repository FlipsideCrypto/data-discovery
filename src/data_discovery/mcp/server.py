"""
MCP server integration using fastapi_mcp to wrap REST endpoints as MCP tools.
"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from loguru import logger

from data_discovery.main import create_app


def create_mcp_app() -> FastAPI:
    """Create FastAPI app with MCP tools integration."""
    # Create the base FastAPI app
    app = create_app()
    
    # Initialize FastAPI MCP integration
    mcp = FastApiMCP(
        app,
        server_name="data-discovery",
        server_version="0.2.0"
    )
    
    # Mount MCP endpoint
    mcp.mount_mcp_server("/mcp")
    
    logger.info("MCP server integration initialized")
    
    return app


# Create the MCP-enabled app
mcp_app = create_mcp_app()


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server with MCP integration")
    uvicorn.run("data_discovery.mcp.server:mcp_app", host="0.0.0.0", port=8000, reload=True)