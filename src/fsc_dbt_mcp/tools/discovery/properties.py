"""
Shared property definitions for discovery tools.

This module provides reusable property classes that define common parameters
used across discovery tools, including validation, schema generation, and 
error handling functionality. Follows MCP best practices for tool design.
"""
import os
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

# Enable debug logging if environment variable is set
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1', 'yes', 'on')
if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)


class ToolProperty(ABC):
    """Base class for reusable tool properties."""
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for this property."""
        pass
    
    @abstractmethod
    def validate_and_extract(self, arguments: Dict[str, Any]) -> Any:
        """Validate and extract this property from tool arguments."""
        pass


@dataclass
class ResourceIdProperty(ToolProperty):
    """Resource ID property for specifying which resources to search."""
    
    required: bool = False
    description: Optional[str] = None
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for resource_id parameter."""
        default_description = (
            "resource_id is the ID returned by get_resources() and represents a dbt project. "
            "resource_id can be a single string or an array of strings. resource_id cannot be any other type. "
            "If resource_id is optional, choose to omit passing it instead of passing null or false."
            "example: `bitcoin-models` or `['bitcoin-models', 'ethereum-models', 'solana-models']`"
        )
        
        return {
            "type": ["string", "array"],
            "description": self.description or default_description,
            "not": {"type": ["boolean", "null"]},
            "items": {
                "type": "string"
            }
        }
    
    def _validate_string(self, value: str, arg_name: str, allow_empty: bool = False) -> str:
        """Validate and sanitize string arguments with security checks."""
        if not isinstance(value, str):
            raise ValueError(f"{arg_name} must be a string")
        
        if not allow_empty and not value.strip():
            raise ValueError(f"{arg_name} must be a non-empty string")
        
        value = value.strip()
        
        # Prevent path traversal and injection attempts
        if any(char in value for char in ['/', '\\', '..', '\x00']):
            raise ValueError(f"{arg_name} contains invalid characters")
        
        return value
    
    def validate_and_extract(self, arguments: Dict[str, Any]) -> Optional[Union[str, List[str]]]:
        """Validate and extract resource_id from arguments."""
        resource_id = arguments.get("resource_id")

        # Check if passed as a boolean, None or null and set to None
        if isinstance(resource_id, bool) or resource_id is None or resource_id == "null" or resource_id == "true" or resource_id == "false":
            resource_id = None
        
        # Check if required but missing
        if self.required and resource_id is None:
            raise ValueError("resource_id is required for this operation")
        
        # Return None if not provided (for optional resource_id)
        if resource_id is None:
            return None
        
        # Validate string resource_id
        if isinstance(resource_id, str):
            return self._validate_string(resource_id, "resource_id")
        
        # Validate array resource_id
        if isinstance(resource_id, list):
            if len(resource_id) == 0:
                return None  # Empty array treated as None
            
            # Validate each item in array
            validated_array = []
            for i, item in enumerate(resource_id):
                if not isinstance(item, str):
                    raise ValueError(f"resource_id array item {i} must be a string")
                validated_array.append(self._validate_string(item, f"resource_id[{i}]"))
            
            return validated_array
        
        # Invalid type
        raise ValueError("resource_id must be a string or array of strings")


@dataclass
class NameProperty(ToolProperty):
    """Name property for specifying object names to search for."""
    
    param_name: str
    description: str
    required: bool = False
    default_value: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for name parameter."""
        schema = {
            "type": "string",
            "description": self.description
        }
        
        if self.default_value is not None:
            schema["default"] = self.default_value
            
        if self.validation_rules:
            schema.update(self.validation_rules)
            
        return schema
    
    def _validate_string(self, value: str, arg_name: str, allow_empty: bool = False) -> str:
        """Validate and sanitize string arguments with security checks."""
        if not isinstance(value, str):
            raise ValueError(f"{arg_name} must be a string")
        
        if not allow_empty and not value.strip():
            raise ValueError(f"{arg_name} must be a non-empty string")
        
        value = value.strip()
        
        # Prevent path traversal and injection attempts
        if any(char in value for char in ['/', '\\', '..', '\x00']):
            raise ValueError(f"{arg_name} contains invalid characters")
        
        return value
    
    def validate_and_extract(self, arguments: Dict[str, Any]) -> Optional[str]:
        """Validate and extract name from arguments."""
        value = arguments.get(self.param_name, self.default_value)
        
        if self.required and value is None:
            raise ValueError(f"{self.param_name} is required")
            
        if value is None:
            return None
            
        validated_value = self._validate_string(value, self.param_name)
        
        # Apply custom validation rules
        if self.validation_rules:
            if "enum" in self.validation_rules:
                if validated_value not in self.validation_rules["enum"]:
                    enum_values = ", ".join(self.validation_rules["enum"])
                    raise ValueError(f"{self.param_name} must be one of: {enum_values}")
        
        return validated_value


@dataclass
class FilterProperty(ToolProperty):
    """Filter property for schema/level/category filtering."""
    
    param_name: str
    description: str
    filter_type: str = "string"  # "string" or "enum"
    enum_values: Optional[List[str]] = None
    required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for filter parameter."""
        schema = {
            "type": "string",
            "description": self.description
        }
        
        if self.filter_type == "enum" and self.enum_values:
            schema["enum"] = self.enum_values
            
        if self.validation_rules:
            schema.update(self.validation_rules)
            
        return schema
    
    def _validate_string(self, value: str, arg_name: str, allow_empty: bool = False) -> str:
        """Validate and sanitize string arguments with security checks."""
        if not isinstance(value, str):
            raise ValueError(f"{arg_name} must be a string")
        
        if not allow_empty and not value.strip():
            raise ValueError(f"{arg_name} must be a non-empty string")
        
        value = value.strip()
        
        # Prevent path traversal and injection attempts
        if any(char in value for char in ['/', '\\', '..', '\x00']):
            raise ValueError(f"{arg_name} contains invalid characters")
        
        return value
    
    def validate_and_extract(self, arguments: Dict[str, Any]) -> Optional[str]:
        """Validate and extract filter value from arguments."""
        value = arguments.get(self.param_name)
        
        if self.required and value is None:
            raise ValueError(f"{self.param_name} is required")
            
        if value is None:
            return None
            
        validated_value = self._validate_string(value, self.param_name).lower()
        
        # Apply enum validation
        if self.filter_type == "enum" and self.enum_values:
            if validated_value not in [v.lower() for v in self.enum_values]:
                enum_values = ", ".join(self.enum_values)
                raise ValueError(f"{self.param_name} must be one of: {enum_values}")
        
        # Apply custom validation rules
        if self.validation_rules:
            # Check for SQL injection attempts
            if any(char in validated_value for char in [';', '--']):
                raise ValueError(f"{self.param_name} contains invalid characters")
        
        return validated_value


@dataclass
class LimitProperty(ToolProperty):
    """Limit property for controlling result set size."""
    
    default_value: int = 25
    min_value: int = 1
    max_value: int = 250
    description: Optional[str] = None
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for limit parameter."""
        default_description = f"Maximum number of results to return (default: {self.default_value}, max: {self.max_value})"
        
        return {
            "type": "integer",
            "description": self.description or default_description,
            "default": self.default_value,
            "minimum": self.min_value,
            "maximum": self.max_value
        }
    
    def validate_and_extract(self, arguments: Dict[str, Any]) -> int:
        """Validate and extract limit from arguments."""
        limit = arguments.get("limit", self.default_value)
        
        if not isinstance(limit, int) or limit < self.min_value or limit > self.max_value:
            raise ValueError(f"limit must be an integer between {self.min_value} and {self.max_value}")
        
        return limit


@dataclass
class BooleanProperty(ToolProperty):
    """Boolean property for flags and toggles."""
    
    param_name: str
    description: str
    default_value: bool = False
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for boolean parameter."""
        return {
            "type": "boolean",
            "description": self.description,
            "default": self.default_value
        }
    
    def validate_and_extract(self, arguments: Dict[str, Any]) -> bool:
        """Validate and extract boolean value from arguments."""
        value = arguments.get(self.param_name, self.default_value)
        
        # Handle null/None values by converting to default
        if value is None:
            return self.default_value
            
        # Convert string "true"/"false" to boolean if needed
        if isinstance(value, str):
            value = value.lower()
            if value == "true":
                value = True
            elif value == "false":
                value = False
            else:
                raise ValueError(f"{self.param_name} must be a boolean or 'true'/'false' string")
        
        if not isinstance(value, bool):
            raise ValueError(f"{self.param_name} must be a boolean")
        
        return value


class ToolPropertySet:
    """Container for managing multiple tool properties."""
    
    def __init__(self, properties: Dict[str, ToolProperty]):
        self.properties = properties
    
    def get_input_schema(self, required_properties: List[str] = None, 
                        one_of_groups: List[List[str]] = None) -> Dict[str, Any]:
        """Generate complete input schema for all properties."""
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
        
        # Add property schemas
        for prop_name, prop_obj in self.properties.items():
            schema["properties"][prop_name] = prop_obj.get_schema()
        
        # Add required properties
        if required_properties:
            schema["required"] = required_properties
        
        # Add oneOf constraints
        if one_of_groups:
            schema["oneOf"] = [{"required": group} for group in one_of_groups]
        
        return schema
    
    def validate_and_extract_all(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and extract all properties from arguments."""
        logger.debug(f"[PROPS] validate_and_extract_all called with arguments: {arguments}")
        
        # Validate arguments structure
        if not isinstance(arguments, dict):
            logger.debug(f"[PROPS] Arguments validation failed - not dict: {type(arguments)}")
            raise ValueError("Arguments must be a dictionary")
        
        logger.debug(f"[PROPS] Processing {len(self.properties)} properties: {list(self.properties.keys())}")
        
        # Extract all property values
        extracted = {}
        for prop_name, prop_obj in self.properties.items():
            try:
                logger.debug(f"[PROPS] Validating property: {prop_name}")
                value = prop_obj.validate_and_extract(arguments)
                extracted[prop_name] = value
                logger.debug(f"[PROPS] Property {prop_name} validated successfully: {value}")
            except Exception as e:
                logger.error(f"[PROPS] Error validating property {prop_name}: {e}")
                logger.debug(f"[PROPS] Property validation failed for {prop_name}, raising ValueError")
                raise ValueError(f"Invalid {prop_name}: {str(e)}")
        
        logger.debug(f"[PROPS] All properties validated successfully: {extracted}")
        return extracted


# Pre-defined property instances for common use cases
STANDARD_RESOURCE_ID = ResourceIdProperty()
REQUIRED_RESOURCE_ID = ResourceIdProperty(required=True)

DOC_NAME = NameProperty(
    param_name="doc_name",
    description="Name of the documentation block to retrieve (default: '__overview__')",
    default_value="__overview__"
)

MODEL_NAME = NameProperty(
    param_name="model_name",
    description="The name of the dbt model (format: 'schema__table_name'). Only use when uniqueId is unavailable."
)

TABLE_NAME = NameProperty(
    param_name="table_name",
    description="The table name to search for (e.g., 'fact_transactions'). Will search across all schemas for models that produce this table name. For best results, include the resource_id with this argument."
)

UNIQUE_ID = NameProperty(
    param_name="uniqueId",
    description="The unique identifier of the model (format: 'model.project_name.model_name'). STRONGLY RECOMMENDED when available."
)

SCHEMA_FILTER = FilterProperty(
    param_name="schema",
    description="Filter models by schema name (e.g., 'core', 'defi', 'nft'). Takes precedence over level if both are provided.",
    validation_rules={"no_sql_injection": True}
)

LEVEL_FILTER = FilterProperty(
    param_name="level",
    description="Filter models by medallion level (bronze, silver, gold). Ignored if schema is provided.",
    filter_type="enum",
    enum_values=["bronze", "silver", "gold"]
)

BLOCKCHAIN_FILTER = NameProperty(
    param_name="blockchain_filter",
    description="Filter resources by blockchain name or alias (e.g., 'ethereum', 'eth', 'bitcoin', 'btc', 'polygon', 'matic')"
)

CATEGORY_FILTER = NameProperty(
    param_name="category_filter",
    description="Filter resources by category (e.g., 'evm', 'l1', 'svm', 'multi-chain', 'internal')"
)

STANDARD_LIMIT = LimitProperty()

SHOW_DETAILS = BooleanProperty(
    param_name="show_details",
    description="Include detailed information like schemas, aliases, and artifact locations (default: false)"
)