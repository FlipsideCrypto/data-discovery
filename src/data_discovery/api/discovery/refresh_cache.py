"""
POST /cache/refresh endpoint - Refresh cached artifacts for dbt project resources.
"""
from typing import Optional, List, Union
from fastapi import APIRouter, Body
from pydantic import BaseModel
from loguru import logger

from data_discovery.project_manager import project_manager



class RefreshCacheRequest(BaseModel):
    """Request model for cache refresh endpoint."""
    resource_ids: Optional[Union[str, List[str]]] = None
    force: bool = False


class RefreshCacheResponse(BaseModel):
    """Response model for cache refresh endpoint."""
    success: bool
    data: dict
    message: str
    discovery_summary: dict
    error: Optional[str] = None


router = APIRouter()


@router.post(
    "/cache/refresh",
    response_model=RefreshCacheResponse,
    operation_id="refresh_cache",
    summary="Discover and refresh cached artifacts for dbt project resources",
    description="Discovers FlipsideCrypto repositories and refreshes cached manifest and catalog artifacts. Always starts with GitHub discovery to ensure latest project list, then refreshes cache for specified or all discovered resources."
)
async def refresh_cache(
    request: RefreshCacheRequest = Body(
        default=RefreshCacheRequest(),
        description="Cache refresh parameters"
    )
) -> RefreshCacheResponse:
    """
    Discover and refresh cached artifacts for dbt project resources.
    
    This endpoint performs a complete discovery and cache refresh workflow:
    1. Discovers FlipsideCrypto repositories from GitHub
    2. Refreshes cache for specified resources or all discovered resources
    3. Returns summary of both discovery and refresh operations
    
    Args:
        request: Contains resource_ids (specific resources or None for all) and force flag
        
    Returns:
        RefreshCacheResponse with discovery summary and refresh results per resource
    """
    logger.info(f"Discovery + cache refresh request received - resource_ids: {request.resource_ids}, force: {request.force}")
    
    try:
        # Step 1: Always start with discovery to get latest repository list
        logger.info("Step 1: Starting GitHub repository discovery")
        
        # Normalize resource_ids for discovery
        specific_projects = None
        if request.resource_ids:
            if isinstance(request.resource_ids, list):
                specific_projects = request.resource_ids
            else:
                specific_projects = [request.resource_ids]
            logger.info(f"Discovery will be limited to specific projects: {specific_projects}")
        else:
            logger.info("Discovery will scan all FlipsideCrypto repositories")
        
        # Optimization: skip docs branch checks for projects with valid cache unless force=True
        # If specific resource_ids are requested, only discover those projects
        discovered_projects = await project_manager.discover_projects(
            skip_valid_cache=True,
            force_refresh=request.force,
            specific_projects=specific_projects
        )
        
        total_discovered = len(discovered_projects)
        projects_with_docs = sum(1 for p in discovered_projects if p.get('has_docs_branch') == 'True')
        projects_without_docs = total_discovered - projects_with_docs
        
        discovery_summary = {
            "total_discovered": total_discovered,
            "projects_with_docs": projects_with_docs,
            "projects_without_docs": projects_without_docs,
            "discovery_completed": True
        }
        
        logger.info(f"Discovery completed: {total_discovered} repositories found, {projects_with_docs} with docs branch, {projects_without_docs} without docs branch")
        
        # Step 2: Refresh cache for specified or all discovered resources
        logger.info("Step 2: Starting cache refresh")
        
        refresh_results = await project_manager.refresh_cache(
            resource_ids=request.resource_ids,
            force=request.force
        )
        
        # Count different types of results
        skipped = sum(1 for result in refresh_results.values() if result.get("action") == "skipped")
        refreshed = sum(1 for result in refresh_results.values() if result.get("action") == "refreshed")
        failed = sum(1 for result in refresh_results.values() if result.get("action") == "failed")
        
        # Build more accurate message
        message_parts = [f"Discovery + cache refresh completed: {total_discovered} repositories discovered"]
        
        if refreshed > 0:
            message_parts.append(f"{refreshed} cache(s) refreshed")
        if skipped > 0:
            message_parts.append(f"{skipped} cache(s) skipped (not expired)")
        if failed > 0:
            message_parts.append(f"{failed} cache(s) failed")
            
        message = ", ".join(message_parts)
        
        logger.info(f"Discovery + cache refresh workflow completed successfully - {message}")
        
        # Overall success is True if no failures occurred (skipped and refreshed are both successful outcomes)
        overall_success = failed == 0
        
        return RefreshCacheResponse(
            success=overall_success,
            data=refresh_results,
            message=message,
            discovery_summary=discovery_summary
        )
        
    except Exception as e:
        logger.error(f"Discovery + cache refresh failed with error: {str(e)}", exc_info=True)
        return RefreshCacheResponse(
            success=False,
            data={},
            message="Discovery + cache refresh failed",
            discovery_summary={"discovery_completed": False, "error": str(e)},
            error=str(e)
        )