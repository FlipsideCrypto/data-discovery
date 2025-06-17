"""
Shared service layer for data discovery functionality.

This service provides core business logic that can be used by both:
- MCP server tools (converting results to TextContent)
- REST API endpoints (returning JSON objects directly)

All methods return structured data as dictionaries/lists instead of formatted text.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from loguru import logger

from data_discovery.project_manager import project_manager
from data_discovery.resources import resource_registry


class DataDiscoveryService:
    """Shared service for data discovery operations across MCP and REST interfaces."""
    
    def __init__(self):
        self.project_manager = project_manager
        self.resource_registry = resource_registry
    
    # ========== RESOURCES ==========
    
    async def get_resources(
        self, 
        show_details: bool = False, 
        blockchain_filter: Optional[str] = None, 
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all available dbt project resources with optional filtering.
        
        Args:
            show_details: Include detailed information (schemas, URLs, etc.)
            blockchain_filter: Filter by blockchain name/alias
            category_filter: Filter by category
            
        Returns:
            Dict containing:
            - resources: List of project resource data
            - total_count: Total resources before filtering
            - filtered_count: Resources after filtering
            - filters_applied: Dict of applied filters
            - partial_match_suggestions: List of suggestions if partial blockchain match
        """
        try:
            # Get all available resources
            project_ids = self.resource_registry.list_project_ids()
            if not project_ids:
                return {
                    "resources": [],
                    "total_count": 0,
                    "filtered_count": 0,
                    "filters_applied": {},
                    "error": "No project resources found"
                }
            
            # Load detailed data for each project
            all_resources = []
            for project_id in project_ids:
                try:
                    project_data = self.resource_registry.get_project_by_id(project_id)
                    all_resources.append(project_data)
                except Exception as e:
                    logger.warning(f"Failed to load project {project_id}: {e}")
                    continue
            
            if not all_resources:
                return {
                    "resources": [],
                    "total_count": 0,
                    "filtered_count": 0,
                    "filters_applied": {},
                    "error": "No project resources loaded successfully"
                }
            
            # Apply filters
            filtered_resources, is_partial_blockchain_match, blockchain_suggestions = self._filter_resources(
                all_resources, blockchain_filter, category_filter
            )
            
            # Format resources based on detail level
            formatted_resources = []
            for resource in filtered_resources:
                if show_details:
                    formatted_resources.append(self._format_resource_detailed(resource))
                else:
                    formatted_resources.append(self._format_resource_summary(resource))
            
            return {
                "resources": formatted_resources,
                "total_count": len(all_resources),
                "filtered_count": len(filtered_resources),
                "filters_applied": {
                    "blockchain_filter": blockchain_filter,
                    "category_filter": category_filter,
                    "show_details": show_details
                },
                "partial_match_suggestions": blockchain_suggestions if is_partial_blockchain_match else []
            }
            
        except Exception as e:
            logger.error(f"Error in get_resources: {e}")
            return {
                "resources": [],
                "total_count": 0,
                "filtered_count": 0,
                "filters_applied": {},
                "error": f"Failed to load resources: {str(e)}"
            }
    
    def _filter_resources(
        self, 
        resources: List[Dict[str, Any]], 
        blockchain_filter: Optional[str] = None, 
        category_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], bool, List[str]]:
        """Filter resources based on blockchain and category criteria."""
        filtered = resources
        is_partial_blockchain_match = False
        blockchain_suggestions = []
        
        if blockchain_filter:
            filtered, is_partial_blockchain_match, blockchain_suggestions = self._analyze_blockchain_matches(
                filtered, blockchain_filter
            )
        
        if category_filter:
            category_filter = category_filter.lower()
            filtered = [r for r in filtered if category_filter in r.get("category", "").lower()]
        
        return filtered, is_partial_blockchain_match, blockchain_suggestions
    
    def _analyze_blockchain_matches(
        self, 
        resources: List[Dict[str, Any]], 
        blockchain_filter: str
    ) -> Tuple[List[Dict[str, Any]], bool, List[str]]:
        """Analyze blockchain matches and determine if it's a partial match."""
        blockchain_filter = blockchain_filter.lower()
        matches = []
        exact_matches = set()
        
        for resource in resources:
            resource_matches = False
            
            # Check main blockchain name
            blockchain = resource.get("blockchain", "").lower()
            if blockchain_filter in blockchain:
                resource_matches = True
                if blockchain_filter == blockchain:
                    exact_matches.add(blockchain)
            
            # Check aliases
            aliases = resource.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    if isinstance(alias, str):
                        alias_lower = alias.lower()
                        if blockchain_filter in alias_lower:
                            resource_matches = True
                            if blockchain_filter == alias_lower:
                                exact_matches.add(alias_lower)
            
            if resource_matches:
                matches.append(resource)
        
        # Determine if this is a partial match (multiple matches but no exact matches)
        is_partial_match = len(matches) > 1 and len(exact_matches) == 0
        
        # Get resource IDs from matched resources for suggestions
        suggested_terms = []
        if is_partial_match:
            for resource in matches:
                resource_id = resource.get("id", "")
                if resource_id and resource_id not in suggested_terms:
                    suggested_terms.append(resource_id)
        
        return matches, is_partial_match, suggested_terms
    
    def _format_resource_summary(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Format a resource for summary display."""
        return {
            "id": resource.get("id"),
            "name": resource.get("name"),
            "blockchain": resource.get("blockchain"),
            "category": resource.get("category"),
            "description": resource.get("description")
        }
    
    def _format_resource_detailed(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Format a resource for detailed display."""
        detailed = self._format_resource_summary(resource)
        detailed.update({
            "location": resource.get("location"),
            "aliases": resource.get("aliases", []),
            "schemas": resource.get("schemas", []),
            "artifact_location": resource.get("artifact_location"),
            "target_branch": resource.get("target_branch")
        })
        return detailed
    
    # ========== MODELS ==========
    
    async def get_models(
        self,
        schema: Optional[str] = None,
        level: Optional[str] = None,
        resource_id: Optional[Union[str, List[str]]] = None,
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Search and retrieve dbt models with filtering.
        
        Args:
            schema: Filter by schema name (partial match)
            level: Filter by medallion level (bronze, silver, gold)
            resource_id: Specific resource(s) to search
            limit: Maximum number of results
            
        Returns:
            Dict containing:
            - models: List of model data
            - total_found: Total models found
            - returned_count: Number of models returned (after limit)
            - truncated: Whether results were truncated
            - filters_applied: Dict of applied filters
            - successful_projects: List of successfully loaded projects
            - failed_projects: List of projects that failed to load
        """
        try:
            # Determine which resources to search
            requested_resources = []
            if resource_id:
                if isinstance(resource_id, str):
                    requested_resources = [resource_id]
                elif isinstance(resource_id, list):
                    requested_resources = resource_id
            else:
                # Get all available resources, respecting MAX_PROJECTS limit
                all_resources = self.resource_registry.list_project_ids()
                max_projects = self.project_manager.config.MAX_PROJECTS
                
                if len(all_resources) > max_projects:
                    return {
                        "models": [],
                        "total_found": 0,
                        "returned_count": 0,
                        "truncated": False,
                        "filters_applied": {"schema": schema, "level": level, "resource_id": resource_id, "limit": limit},
                        "successful_projects": [],
                        "failed_projects": [],
                        "error": f"Too many resources available ({len(all_resources)}). Please specify resource_id to search specific projects, or use schema/level filters. Available resources: {all_resources[:10]}{'...' if len(all_resources) > 10 else ''}"
                    }
                
                requested_resources = all_resources
            
            # Load artifacts for each resource
            successful_artifacts = {}
            failed_resources = []
            
            for res_id in requested_resources:
                try:
                    artifacts = await self.project_manager.get_project_artifacts([res_id])
                    if artifacts and res_id in artifacts:
                        successful_artifacts[res_id] = artifacts[res_id]
                    else:
                        failed_resources.append(res_id)
                except Exception as e:
                    logger.warning(f"Failed to load artifacts for resource {res_id}: {e}")
                    failed_resources.append(res_id)
            
            if not successful_artifacts:
                return {
                    "models": [],
                    "total_found": 0,
                    "returned_count": 0,
                    "truncated": False,
                    "filters_applied": {"schema": schema, "level": level, "resource_id": resource_id, "limit": limit},
                    "successful_projects": [],
                    "failed_projects": failed_resources,
                    "error": f"No valid resources found. Failed resources: {failed_resources}" if failed_resources else "No artifacts loaded"
                }
            
            # Filter models across all projects
            all_filtered_models = []
            for proj_id, (manifest, _) in successful_artifacts.items():
                nodes = manifest.get("nodes", {})
                if not isinstance(nodes, dict):
                    logger.warning(f"Invalid manifest structure in project {proj_id}: 'nodes' is not a dictionary")
                    continue
                
                project_models = self._filter_models_by_criteria(nodes, schema, level, proj_id)
                all_filtered_models.extend(project_models)
            
            # Sort all models by project, schema, then name
            all_filtered_models = sorted(
                all_filtered_models, 
                key=lambda x: (x.get("resource_id", ""), x.get("schema", ""), x.get("name", ""))
            )
            
            # Apply limit
            total_found = len(all_filtered_models)
            truncated = total_found > limit
            returned_models = all_filtered_models[:limit] if truncated else all_filtered_models
            
            return {
                "models": returned_models,
                "total_found": total_found,
                "returned_count": len(returned_models),
                "truncated": truncated,
                "filters_applied": {"schema": schema, "level": level, "resource_id": resource_id, "limit": limit},
                "successful_projects": list(successful_artifacts.keys()),
                "failed_projects": failed_resources
            }
            
        except Exception as e:
            logger.error(f"Error in get_models: {e}")
            return {
                "models": [],
                "total_found": 0,
                "returned_count": 0,
                "truncated": False,
                "filters_applied": {"schema": schema, "level": level, "resource_id": resource_id, "limit": limit},
                "successful_projects": [],
                "failed_projects": [],
                "error": f"Internal error retrieving models: {str(e)}"
            }
    
    def _filter_models_by_criteria(
        self, 
        models: Dict[str, Any], 
        schema: Optional[str], 
        level: Optional[str], 
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """Filter models based on schema or medallion level criteria."""
        filtered_models = []
        
        for model_id, model_info in models.items():
            if not isinstance(model_info, dict) or model_info.get("resource_type") != "model":
                continue
                
            # Check if model matches criteria
            matches = False
            
            if schema:
                # Partial schema match to handle cases like silver_api
                matches = schema in model_info.get("schema", "").lower()
            elif level:
                # Check both schema and fqn for level matching
                model_fqn = model_info.get("fqn", [])
                
                if level == "bronze":
                    matches = any("bronze" in part.lower() for part in model_fqn) or "bronze" in model_info.get("schema", "").lower()
                elif level == "silver":
                    matches = any("silver" in part.lower() for part in model_fqn) or "silver" in model_info.get("schema", "").lower()
                elif level == "gold":
                    matches = any("gold" in part.lower() for part in model_fqn) or "gold" in model_info.get("schema", "").lower()
            
            if matches:
                # Extract key model information
                model_data = {
                    "unique_id": model_id,
                    "name": model_info.get("name"),
                    "schema": model_info.get("schema"),
                    "database": model_info.get("database"),
                    "materialized": model_info.get("config", {}).get("materialized"),
                    "description": model_info.get("description", ""),
                    "tags": model_info.get("tags", []),
                    "path": model_info.get("original_file_path"),
                    "fqn": model_info.get("fqn", []),
                    "relation_name": model_info.get("relation_name"),
                    "resource_id": resource_id
                }
                filtered_models.append(model_data)
        
        # Sort by schema then name for consistent ordering
        return sorted(filtered_models, key=lambda x: (x.get("schema", ""), x.get("name", "")))
    
    # ========== MODEL DETAILS ==========
    
    async def get_model_by_id(
        self,
        unique_id: Optional[str] = None,
        model_name: Optional[str] = None,
        table_name: Optional[str] = None,
        fqn: Optional[str] = None,
        resource_id: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific dbt model.
        
        Args:
            unique_id: Model's unique ID (e.g., "model.ethereum_models.core__fact_transactions")
            model_name: Model name for search
            table_name: Table name for search
            fqn: Fully qualified name (e.g., "ethereum.core.fact_transactions")
            resource_id: Specific resource(s) to search
            
        Returns:
            Dict containing model details or error information
        """
        try:
            # Validate input
            if not unique_id and not model_name and not table_name and not fqn:
                return {
                    "error": "Either unique_id, model_name, table_name, or fqn must be provided"
                }
            
            # Input sanitization for unique_id format
            if unique_id is not None and not unique_id.startswith("model."):
                return {
                    "error": "unique_id must start with 'model.'"
                }
            
            # Handle FQN search (e.g., "ethereum.core.fact_transactions")
            if fqn:
                return await self._search_by_fqn(fqn, resource_id)
            
            # Handle unique_id lookup
            if unique_id:
                try:
                    extracted_project = self.project_manager._validate_unique_id_project(unique_id)
                    artifacts = await self.project_manager.get_project_artifacts(extracted_project)
                    
                    if extracted_project in artifacts:
                        manifest, catalog = artifacts[extracted_project]
                        model_node, found_unique_id = self._find_model_node(manifest, unique_id, model_name, table_name)
                        
                        if model_node and found_unique_id:
                            return await self._format_model_details(model_node, found_unique_id, catalog, extracted_project)
                        else:
                            return {
                                "error": f"Model '{unique_id}' not found in project '{extracted_project}'"
                            }
                except ValueError as e:
                    return {
                        "error": f"Invalid unique_id: {str(e)}"
                    }
            
            # Multi-project search for model_name
            if model_name:
                found_models = await self.project_manager.find_model_in_projects(model_name, resource_id)
                
                if not found_models:
                    identifier = unique_id if unique_id else model_name
                    project_info = f" in projects {resource_id}" if resource_id else ""
                    return {
                        "error": f"Model '{identifier}' not found{project_info}"
                    }
                
                if len(found_models) == 1:
                    # Single model found
                    found_model = found_models[0]
                    return await self._format_model_details(
                        found_model["manifest_data"], 
                        found_model["unique_id"], 
                        {"nodes": {found_model["unique_id"]: found_model["catalog_data"]}},
                        found_model["resource_id"]
                    )
                else:
                    # Multiple models found
                    return {
                        "multiple_matches": True,
                        "matches": [
                            {
                                "unique_id": found_model["unique_id"],
                                "resource_id": found_model["resource_id"],
                                "schema": found_model["manifest_data"].get("schema"),
                                "database": found_model["manifest_data"].get("database")
                            }
                            for found_model in found_models
                        ],
                        "message": f"Multiple models named '{model_name}' found. Please use the specific unique_id."
                    }
            
            # Fallback search
            artifacts = await self.project_manager.get_project_artifacts(resource_id or [])
            if not artifacts:
                return {
                    "error": "No artifacts available for search"
                }
            
            # Search in available projects
            for proj_id, (manifest, catalog) in artifacts.items():
                model_node, found_unique_id = self._find_model_node(manifest, unique_id, model_name, table_name)
                if model_node and found_unique_id:
                    return await self._format_model_details(model_node, found_unique_id, catalog, proj_id)
            
            # Model not found
            identifier = unique_id if unique_id else (model_name if model_name else table_name)
            return {
                "error": f"Model '{identifier}' not found"
            }
            
        except Exception as e:
            logger.error(f"Error in get_model_by_id: {e}")
            return {
                "error": f"Internal error retrieving model details: {str(e)}"
            }
    
    def _find_model_node(
        self, 
        manifest: Dict[str, Any], 
        unique_id: Optional[str], 
        model_name: Optional[str], 
        table_name: Optional[str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Find model node in manifest."""
        nodes = manifest.get("nodes", {})
        
        if not isinstance(nodes, dict):
            raise ValueError("Invalid manifest structure: 'nodes' is not a dictionary")
        
        if unique_id:
            # Direct lookup by unique_id
            model_node = nodes.get(unique_id)
            if model_node and model_node.get("resource_type") == "model":
                return model_node, unique_id
            return None, None
        
        elif model_name:
            # Search by model name
            for node_id, node in nodes.items():
                if (isinstance(node, dict) and 
                    node.get("resource_type") == "model" and 
                    node.get("name") == model_name):
                    return node, node_id
        
        elif table_name:
            # Search by table name
            matching_models = []
            
            for node_id, node in nodes.items():
                if not isinstance(node, dict) or node.get("resource_type") != "model":
                    continue
                
                # Check relation_name (e.g., "flipside_dev_models.core.fact_transactions")
                relation_name = node.get("relation_name", "")
                if relation_name and relation_name.endswith(f".{table_name}"):
                    matching_models.append((node, node_id))
                    continue
                
                # Check if model name ends with the table name
                model_node_name = node.get("name", "")
                if model_node_name.endswith(f"__{table_name}") or model_node_name.endswith(f"_{table_name}"):
                    matching_models.append((node, node_id))
                    continue
                
                # Check if the model name exactly matches the table name
                if model_node_name == table_name:
                    matching_models.append((node, node_id))
            
            # Return first match if any found
            if matching_models:
                return matching_models[0]
        
        return None, None
    
    async def _format_model_details(
        self, 
        model_node: Dict[str, Any], 
        unique_id: str, 
        catalog: Dict[str, Any], 
        resource_id: str
    ) -> Dict[str, Any]:
        """Format model details into a structured response."""
        try:
            # Get catalog information if available
            catalog_node = catalog.get("nodes", {}).get(unique_id, {})
            
            # Extract model details
            model_details = {
                "unique_id": unique_id,
                "name": model_node.get("name"),
                "description": model_node.get("description", ""),
                "schema": model_node.get("schema"),
                "database": model_node.get("database"),
                "relation_name": model_node.get("relation_name"),
                "materialized": model_node.get("config", {}).get("materialized"),
                "tags": model_node.get("tags", []),
                "meta": model_node.get("meta", {}),
                "path": model_node.get("original_file_path"),
                "raw_code": model_node.get("raw_code", ""),
                "compiled_code": model_node.get("compiled_code"),
                "depends_on": model_node.get("depends_on", {}),
                "refs": model_node.get("refs", []),
                "sources": model_node.get("sources", []),
                "fqn": model_node.get("fqn", []),
                "access": model_node.get("access"),
                "constraints": model_node.get("constraints", []),
                "version": model_node.get("version"),
                "latest_version": model_node.get("latest_version"),
                "resource_id": resource_id,
            }
            
            # Process columns
            columns = self._extract_model_columns(model_node, catalog_node)
            model_details["columns"] = columns
            
            # Add catalog metadata if available
            if catalog_node:
                model_details["catalog_metadata"] = catalog_node.get("metadata", {})
                model_details["stats"] = catalog_node.get("stats", {})
            
            return model_details
            
        except Exception as e:
            logger.error(f"Error formatting model details: {e}")
            return {
                "error": f"Error formatting model details: {str(e)}"
            }
    
    def _extract_model_columns(
        self, 
        model_node: Dict[str, Any], 
        catalog_node: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract and merge column information from manifest and catalog."""
        # Add column information from manifest
        manifest_columns = model_node.get("columns", {})
        if not isinstance(manifest_columns, dict):
            manifest_columns = {}
            
        columns = {}
        for col_name, col_info in manifest_columns.items():
            columns[col_name] = {
                "name": col_name,
                "description": col_info.get("description", ""),
                "data_type": col_info.get("data_type"),
                "meta": col_info.get("meta", {}),
                "tags": col_info.get("tags", []),
                "constraints": col_info.get("constraints", [])
            }
        
        # Enhance with catalog column information if available
        catalog_columns = catalog_node.get("columns", {})
        if not isinstance(catalog_columns, dict):
            catalog_columns = {}
            
        for col_name, col_info in catalog_columns.items():
            if col_name in columns:
                columns[col_name].update({
                    "type": col_info.get("type"),
                    "index": col_info.get("index"),
                    "comment": col_info.get("comment")
                })
            else:
                # Column exists in catalog but not manifest
                columns[col_name] = {
                    "name": col_name,
                    "type": col_info.get("type"),
                    "index": col_info.get("index"),
                    "comment": col_info.get("comment", ""),
                    "description": "",
                    "data_type": col_info.get("type"),
                    "meta": {},
                    "tags": [],
                    "constraints": []
                }
        
        return columns
    
    async def _search_by_fqn(self, fqn: str, resource_id: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
        """
        Search for a model using a fully qualified name (e.g., "ethereum.core.fact_transactions").
        
        Supports formats:
        - database.schema.table (e.g., "ethereum.core.fact_transactions")
        - schema.table (e.g., "core.fact_transactions")
        """
        try:
            # Parse FQN
            fqn_parts = fqn.split('.')
            if len(fqn_parts) == 3:
                # database.schema.table format
                target_database, target_schema, target_table = fqn_parts
            elif len(fqn_parts) == 2:
                # schema.table format
                target_database = None
                target_schema, target_table = fqn_parts
            else:
                return {
                    "error": f"Invalid FQN format: '{fqn}'. Expected format: 'database.schema.table' or 'schema.table'"
                }
            
            # Load project artifacts
            artifacts = await self.project_manager.get_project_artifacts(resource_id or [])
            if not artifacts:
                return {
                    "error": "No artifacts available for FQN search"
                }
            
            # Search across projects for matching FQN
            matching_models = []
            for proj_id, (manifest, catalog) in artifacts.items():
                nodes = manifest.get("nodes", {})
                if not isinstance(nodes, dict):
                    continue
                
                for node_id, node_data in nodes.items():
                    if not isinstance(node_data, dict) or node_data.get("resource_type") != "model":
                        continue
                    
                    # Check if this model matches the FQN
                    model_database = node_data.get("database", "").lower()
                    model_schema = node_data.get("schema", "").lower()
                    model_name = node_data.get("name", "").lower()
                    
                    # Try to match table name patterns
                    # dbt models often use naming conventions like "core__fact_transactions" for table "fact_transactions"
                    possible_table_names = [
                        model_name,  # Exact match
                        model_name.split('__')[-1] if '__' in model_name else model_name,  # Remove prefix
                        model_name.replace('_', ''),  # No underscores
                    ]
                    
                    target_table_lower = target_table.lower()
                    schema_matches = model_schema == target_schema.lower()
                    table_matches = target_table_lower in [name.lower() for name in possible_table_names]
                    
                    # Database check (optional for 2-part FQN)
                    database_matches = (
                        target_database is None or  # 2-part FQN, skip database check
                        model_database == target_database.lower() or
                        target_database.lower() in model_database  # Partial match for variations
                    )
                    
                    if schema_matches and table_matches and database_matches:
                        matching_models.append({
                            "node_id": node_id,
                            "node_data": node_data,
                            "catalog_data": catalog.get("nodes", {}).get(node_id, {}),
                            "project_id": proj_id,
                            "match_score": self._calculate_fqn_match_score(
                                fqn, model_database, model_schema, model_name
                            )
                        })
            
            if not matching_models:
                return {
                    "error": f"No models found matching FQN: '{fqn}'"
                }
            
            # Sort by match score (highest first) and return best match
            matching_models.sort(key=lambda x: x["match_score"], reverse=True)
            best_match = matching_models[0]
            
            # Format the response
            return await self._format_model_details(
                best_match["node_data"],
                best_match["node_id"],
                {"nodes": {best_match["node_id"]: best_match["catalog_data"]}},
                best_match["project_id"]
            )
            
        except Exception as e:
            logger.error(f"Error in FQN search: {e}")
            return {
                "error": f"Internal error during FQN search: {str(e)}"
            }
    
    def _calculate_fqn_match_score(self, target_fqn: str, database: str, schema: str, model_name: str) -> float:
        """Calculate a match score for FQN matching (higher = better match)."""
        score = 0.0
        
        # Exact schema match gets high score
        target_parts = target_fqn.lower().split('.')
        if len(target_parts) >= 2 and schema.lower() == target_parts[-2]:
            score += 10.0
        
        # Table name similarity
        target_table = target_parts[-1].lower()
        if model_name.lower() == target_table:
            score += 10.0  # Exact match
        elif target_table in model_name.lower():
            score += 5.0   # Partial match
        elif model_name.lower().endswith(f"__{target_table}"):
            score += 8.0   # dbt naming convention match
        
        # Database match (if specified)
        if len(target_parts) == 3:
            target_db = target_parts[0].lower()
            if database.lower() == target_db:
                score += 5.0
            elif target_db in database.lower():
                score += 2.0
        
        return score
    
    # ========== DESCRIPTIONS ==========
    
    async def get_description(
        self,
        doc_name: str,
        resource_id: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Get documentation blocks from dbt manifest.
        
        Args:
            doc_name: Name of the documentation block
            resource_id: Specific resource(s) to search
            
        Returns:
            Dict containing documentation information or error details
        """
        try:
            if not resource_id:
                return {
                    "error": "resource_id is required for get_description to avoid cross-contamination of blockchain-specific documentation"
                }
            
            # Load project artifacts
            artifacts = await self.project_manager.get_project_artifacts(resource_id)
            if not artifacts:
                return {
                    "error": "No artifacts found for the specified resource_id"
                }
            
            # Search for documentation blocks across all specified projects
            all_matching_docs = []
            
            for proj_id, (manifest, _) in artifacts.items():
                docs = manifest.get("docs", {})
                if not isinstance(docs, dict):
                    logger.warning(f"Invalid manifest structure in project {proj_id}: 'docs' is not a dictionary")
                    continue
                
                # Find matching documentation blocks
                for doc_id, doc_info in docs.items():
                    if (isinstance(doc_info, dict) and 
                        doc_info.get("resource_type") == "doc" and
                        doc_info.get("name") == doc_name):
                        all_matching_docs.append({
                            "project_id": proj_id,
                            "doc_id": doc_id,
                            "package_name": doc_info.get("package_name", "Unknown Package"),
                            "path": doc_info.get("original_file_path", "Unknown path"),
                            "content": doc_info.get("block_contents", "")
                        })
            
            if not all_matching_docs:
                resource_info = f" in resources {resource_id}" if resource_id else ""
                return {
                    "error": f"Documentation block '{doc_name}' not found{resource_info}"
                }
            
            return {
                "doc_name": doc_name,
                "matches": all_matching_docs,
                "total_matches": len(all_matching_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in get_description: {e}")
            return {
                "error": f"Internal error retrieving description: {str(e)}"
            }