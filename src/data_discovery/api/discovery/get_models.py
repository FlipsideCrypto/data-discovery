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
        default="gold",
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
    ),
    show_details: bool = Query(
        default=False,
        description="Include additional model details beyond basic fields (name, database, schema, description, relation_name)"
    )
) -> ModelsResponse:
    """
    Search for dbt models with various filtering options.
    
    At least one of schema, level, or resource_id must be provided. Level defaults to gold.
    Results are sorted by project, schema, then model name.
    
    Basic fields (always returned): name, database, schema, description, relation_name.
    Additional fields (show_details=True): unique_id, materialized, tags, path, fqn, resource_id.
    """
    result = await service.get_models(
        schema=schema,
        level=level,
        resource_id=resource_id,
        limit=limit,
        show_details=show_details
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
    ),
    show_details: bool = Query(
        default=False,
        description="Include additional model details beyond basic fields (name, database, schema, description, relation_name, columns)"
    )
) -> ModelDetailsResponse:
    """
    Get detailed information about a specific model by its unique ID or FQN (FQN in this case is in the context of the deployed table. dbt calls this "relation_name").
    
    Supports two formats:
    - Unique ID: model.{project}.{name}
    - FQN: {database}.{schema}.{table}
    
    Basic fields (always returned): name, database, schema, description, relation_name, columns.
    Additional fields (show_details=True): unique_id, materialized, tags, meta, path, raw_code, 
    compiled_code, depends_on, refs, sources, fqn, access, constraints, version, latest_version, 
    resource_id, catalog_metadata, stats.
    """
    # Check if it's a unique_id (starts with "model.") or FQN
    if identifier.startswith("model."):
        # Handle as unique_id
        result = await service.get_model_details(unique_id=identifier, show_details=show_details)
    else:
        # Handle as FQN (database.schema.table)
        result = await service.get_model_details(fqn=identifier, resource_id=resource_id, show_details=show_details)
    
    if not result["success"] and "Invalid unique_id" in result.get("error", ""):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ModelDetailsResponse(**result)