"""
GET /resources endpoint - List available dbt project resources.
"""
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from data_discovery.core.service import service


class ResourcesResponse(BaseModel):
    """Response model for resources endpoint."""
    success: bool
    data: list
    total_count: Optional[int] = None
    filtered_count: Optional[int] = None
    filters: Optional[dict] = None
    suggestions: Optional[list] = None
    error: Optional[str] = None


router = APIRouter()


@router.get(
    "/resources",
    response_model=ResourcesResponse,
    operation_id="get_resources",
    summary="List available dbt project resources",
    description="Retrieve all available dbt project resources with optional filtering by blockchain or category"
)
async def get_resources(
    show_details: bool = Query(
        default=False,
        description="Include detailed information about each resource"
    ),
    blockchain_filter: Optional[str] = Query(
        default=None,
        description="Filter resources by blockchain name or alias"
    ),
    category_filter: Optional[str] = Query(
        default=None,
        description="Filter resources by category (e.g., 'L1', 'DeFi', 'Gaming')"
    )
) -> ResourcesResponse:
    """
    List all available dbt project resources.
    
    This endpoint provides discovery of blockchain projects available for analysis.
    Resources can be filtered by blockchain type or category.
    """
    result = await service.get_resources(
        show_details=show_details,
        blockchain_filter=blockchain_filter,
        category_filter=category_filter
    )
    
    return ResourcesResponse(**result)