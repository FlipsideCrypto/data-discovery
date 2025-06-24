"""
Configuration settings for the data discovery API.
"""
import os
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings."""
    
    debug_mode: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    deployment_mode: str = os.getenv("DEPLOYMENT_MODE", "api").lower()
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    max_projects: int = int(os.getenv("MAX_PROJECTS", "50"))
    
    # API settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()