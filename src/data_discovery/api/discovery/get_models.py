"""
GET /models endpoints - Search and retrieve dbt models.
"""
from typing import Optional, Union, List
from fastapi import APIRouter, Query, Path, HTTPException
from pydantic import BaseModel

from data_discovery.core.service import service


class ModelsResponse(BaseModel):
    """Response model for models list endpoint."""
    success: bool
    data: list
    count: Optional[int] = None
    truncated: Optional[bool] = None
    failed_resources: Optional[list] = None
    filters: Optional[dict] = None
    error: Optional[str] = None


class ModelDetailsResponse(BaseModel):
    """Response model for single model details endpoint."""
    success: bool
    data: Optional[dict] = None
    multiple_matches: Optional[list] = None
    error: Optional[str] = None


router = APIRouter()


@router.get(
    "/models",
    response_model=ModelsResponse,
    operation_id="get_models",
    summary="Search dbt models",
    description="Retrieve dbt models with filtering by schema, medallion level, or resource"
)
async def get_models(
    schema: Optional[str] = Query(
        default=None,
        description="Filter models by schema name (partial match supported)"
    ),
    level: Optional[str] = Query(
        default=None,
        description="Filter models by medallion architecture level (bronze, silver, gold)"
    ),
    resource_id: Optional[str] = Query(
        default=None,
        description="Specific resource/project ID to search within"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of models to return"
    )
) -> ModelsResponse:
    """
    Search for dbt models with various filtering options.
    
    At least one of schema, level, or resource_id must be provided.
    Results are sorted by project, schema, then model name.
    """
    result = await service.get_models(
        schema=schema,
        level=level,
        resource_id=resource_id,
        limit=limit
    )
    
    return ModelsResponse(**result)


@router.get(
    "/models/{identifier:path}",
    response_model=ModelDetailsResponse,
    operation_id="get_model_by_id",
    summary="Get model details by unique ID or FQN",
    description="Retrieve detailed information about a specific model using its unique ID or FQN (database.schema.table)"
)
async def get_model_by_id(
    identifier: str = Path(
        ...,
        description="The unique ID (model.project.name) or FQN (database.schema.table) of the model"
    ),
    resource_id: Optional[str] = Query(
        default=None,
        description="Specific resource/project ID to search within (optional for FQN)"
    )
) -> ModelDetailsResponse:
    """
    Get detailed information about a specific model by its unique ID or FQN.
    
    Supports two formats:
    - Unique ID: model.{project}.{name}
    - FQN: {database}.{schema}.{table}
    """
    # Check if it's a unique_id (starts with "model.") or FQN
    if identifier.startswith("model."):
        # Handle as unique_id
        result = await service.get_model_details(unique_id=identifier)
    else:
        # Handle as FQN (database.schema.table)
        result = await service.get_model_details(fqn=identifier, resource_id=resource_id)
    
    if not result["success"] and "Invalid unique_id" in result.get("error", ""):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ModelDetailsResponse(**result)