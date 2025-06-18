"""
GET /descriptions/{doc_name} endpoint - Retrieve documentation blocks.
"""
from typing import Optional
from fastapi import APIRouter, Path, Query
from pydantic import BaseModel

from data_discovery.core.service import service


class DescriptionResponse(BaseModel):
    """Response model for description endpoint."""
    success: bool
    data: list
    count: Optional[int] = None
    error: Optional[str] = None


router = APIRouter()


@router.get(
    "/descriptions/{doc_name}",
    response_model=DescriptionResponse,
    operation_id="get_description",
    summary="Get documentation block by name",
    description="Retrieve documentation blocks by name from specified dbt projects"
)
async def get_description(
    doc_name: str = Path(
        ...,
        description="Name of the documentation block to retrieve"
    ),
    resource_id: str = Query(
        ...,
        description="Required resource/project ID to search within (prevents cross-contamination)"
    )
) -> DescriptionResponse:
    """
    Retrieve documentation blocks by name from dbt projects.
    
    The resource_id parameter is required to avoid cross-contamination
    of blockchain-specific documentation context.
    """
    result = await service.get_description(
        doc_name=doc_name,
        resource_id=resource_id
    )
    
    return DescriptionResponse(**result)