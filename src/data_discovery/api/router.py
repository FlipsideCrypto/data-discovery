"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from data_discovery.api.discovery.get_resources import router as resources_router
from data_discovery.api.discovery.get_models import router as models_router
from data_discovery.api.discovery.get_description import router as descriptions_router

api_router = APIRouter()

# Include all discovery routers
api_router.include_router(resources_router, prefix="/discovery", tags=["discovery"])
api_router.include_router(models_router, prefix="/discovery", tags=["discovery"])
api_router.include_router(descriptions_router, prefix="/discovery", tags=["discovery"])