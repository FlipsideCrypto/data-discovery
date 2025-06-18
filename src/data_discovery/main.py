#!/usr/bin/env python3
"""
FastAPI application for data discovery REST API with MCP integration.
"""
from fastapi import FastAPI
from loguru import logger

try:
    from fastapi_mcp import FastApiMCP
    MCP_AVAILABLE = True
except ImportError:
    logger.warning("fastapi_mcp not available, MCP integration disabled")
    MCP_AVAILABLE = False

from data_discovery.api.router import api_router


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Data Discovery API",
        description="REST API for dbt project discovery across blockchain datasets",
        version="0.2.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Add MCP integration if available
    if MCP_AVAILABLE:
        try:
            mcp = FastApiMCP(
                app,
                name="data-discovery",
                description="MCP server for dbt project discovery across blockchain datasets"
            )
            mcp.mount(mount_path="/mcp")
            logger.info("MCP integration enabled at /mcp")
        except Exception as e:
            logger.error(f"Failed to initialize MCP integration: {e}")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.2.0", "mcp_enabled": MCP_AVAILABLE}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)