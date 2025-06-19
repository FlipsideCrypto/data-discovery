"""
Core service layer for data discovery functionality.
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from data_discovery.project_manager import project_manager
from data_discovery.resources import resource_registry


class DataDiscoveryService:
    """Core service for data discovery operations."""
    
    async def get_resources(
        self, 
        show_details: bool = False,
        blockchain_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all available dbt project resources."""
        try:
            # Get all available resources from project manager
            project_ids = resource_registry.list_project_ids()
            
            if not project_ids:
                return {
                    "success": False,
                    "error": "No project resources found",
                    "data": []
                }
            
            # Get detailed data for each project
            all_resources = []
            for project_id in project_ids:
                try:
                    project_data = resource_registry.get_project_by_id(project_id)
                    all_resources.append(project_data)
                except Exception as e:
                    logger.warning(f"Failed to load project {project_id}: {e}")
                    continue
            
            if not all_resources:
                return {
                    "success": False,
                    "error": "No resources loaded successfully",
                    "data": []
                }
            
            # Apply filters
            filtered_resources, is_partial_blockchain_match, blockchain_suggestions = self._filter_resources(
                all_resources, blockchain_filter, category_filter
            )
            
            # Apply show_details filtering
            if not show_details:
                # Return only basic fields: id, blockchain, description
                filtered_resources = [
                    {
                        "id": resource.get("id"),
                        "blockchain": resource.get("blockchain"),
                        "description": resource.get("description", ""),
                        "aliases": resource.get("aliases", [])
                    }
                    for resource in filtered_resources
                ]
            
            return {
                "success": True,
                "data": filtered_resources,
                "total_count": len(all_resources),
                "filtered_count": len(filtered_resources),
                "filters": {
                    "blockchain": blockchain_filter,
                    "category": category_filter,
                    "show_details": show_details
                },
                "suggestions": blockchain_suggestions if is_partial_blockchain_match else None
            }
            
        except Exception as e:
            logger.error(f"Error in get_resources: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "data": []
            }
    
    async def get_models(
        self,
        schema: Optional[str] = None,
        level: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
        show_details: bool = False
    ) -> Dict[str, Any]:
        """Get models with filtering by schema or medallion level."""
        try:
            # Validate input
            if not schema and not level and not resource_id:
                return {
                    "success": False,
                    "error": "At least one parameter (schema, level, or resource_id) is required",
                    "data": []
                }
            
            # Validate level parameter
            if level and level not in ["bronze", "silver", "gold"]:
                return {
                    "success": False,
                    "error": f"Invalid level '{level}'. Must be one of: bronze, silver, gold",
                    "data": []
                }
            
            # Determine which resources to search
            requested_resources = []
            if resource_id:
                requested_resources = [resource_id] if isinstance(resource_id, str) else resource_id
            else:
                all_resources = resource_registry.list_project_ids()
                requested_resources = all_resources
                logger.info(f"Cross-project search across {len(requested_resources)} projects")
            
            # Load artifacts with fast-fail for known problematic projects
            successful_artifacts = {}
            failed_resources = []
            
            for res_id in requested_resources:
                try:
                    # Quick timeout/retry logic could be added here
                    artifacts = await project_manager.get_project_artifacts([res_id])
                    if artifacts and res_id in artifacts:
                        successful_artifacts[res_id] = artifacts[res_id]
                        logger.debug(f"Successfully loaded artifacts for {res_id}")
                    else:
                        failed_resources.append(res_id)
                        logger.debug(f"No artifacts available for {res_id}")
                except Exception as e:
                    # Don't log warnings for cross-project searches to reduce noise
                    if resource_id:  # Only log warnings for specific resource requests
                        logger.warning(f"Failed to load artifacts for resource {res_id}: {e}")
                    else:
                        logger.debug(f"Skipping {res_id}: {e}")
                    failed_resources.append(res_id)
            
            if not successful_artifacts:
                return {
                    "success": False,
                    "error": f"No valid resources found. Failed resources: {failed_resources}",
                    "data": []
                }
            
            # Filter models
            all_filtered_models = []
            for proj_id, (manifest, _) in successful_artifacts.items():
                nodes = manifest.get("nodes", {})
                if isinstance(nodes, dict):
                    project_models = self._filter_models_by_criteria(nodes, schema, level, proj_id, show_details)
                    all_filtered_models.extend(project_models)
            
            # Sort and limit
            all_filtered_models = sorted(
                all_filtered_models, 
                key=lambda x: (x.get("resource_id", ""), x.get("schema", ""), x.get("name", ""))
            )
            
            truncated = len(all_filtered_models) > limit
            if truncated:
                all_filtered_models = all_filtered_models[:limit]
            
            return {
                "success": True,
                "data": all_filtered_models,
                "count": len(all_filtered_models),
                "truncated": truncated,
                "failed_resources": failed_resources,
                "filters": {
                    "schema": schema,
                    "level": level,
                    "resource_id": resource_id,
                    "limit": limit,
                    "show_details": show_details
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_models: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "data": []
            }
    
    async def get_model_details(
        self,
        unique_id: Optional[str] = None,
        model_name: Optional[str] = None,
        table_name: Optional[str] = None,
        fqn: Optional[str] = None,
        resource_id: Optional[str] = None,
        show_details: bool = False
    ) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        try:
            # Validate input
            if not unique_id and not model_name and not table_name and not fqn:
                return {
                    "success": False,
                    "error": "Either unique_id, model_name, table_name, or fqn must be provided",
                    "data": None
                }
            
            # Handle FQN lookup (database.schema.table format)
            if fqn:
                parts = fqn.split('.')
                if len(parts) != 3:
                    return {
                        "success": False,
                        "error": "FQN must be in format 'database.schema.table'",
                        "data": None
                    }
                
                database, schema, table = parts
                return await self._find_model_by_fqn(database, schema, table, resource_id, show_details)
            
            # Handle unique_id lookup
            if unique_id:
                if not unique_id.startswith("model."):
                    return {
                        "success": False,
                        "error": "unique_id must start with 'model.'",
                        "data": None
                    }
                
                try:
                    extracted_project = project_manager._validate_unique_id_project(unique_id)
                    artifacts = await project_manager.get_project_artifacts(extracted_project)
                    
                    if extracted_project in artifacts:
                        manifest, catalog = artifacts[extracted_project]
                        model_node, found_unique_id = self._find_model_node(
                            manifest, unique_id, model_name, table_name
                        )
                        
                        if model_node and found_unique_id:
                            model_details = self._format_model_details(
                                model_node, found_unique_id, catalog, extracted_project, show_details
                            )
                            return {
                                "success": True,
                                "data": model_details
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Model not found in project '{extracted_project}'",
                                "data": None
                            }
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Invalid unique_id: {str(e)}",
                        "data": None
                    }
            
            # Handle model_name lookup
            if model_name:
                found_models = await project_manager.find_model_in_projects(model_name, resource_id)
                
                if not found_models:
                    return {
                        "success": False,
                        "error": f"Model '{model_name}' not found",
                        "data": None
                    }
                
                if len(found_models) == 1:
                    found_model = found_models[0]
                    model_details = self._format_model_details(
                        found_model["manifest_data"],
                        found_model["unique_id"],
                        {"nodes": {found_model["unique_id"]: found_model["catalog_data"]}},
                        found_model["resource_id"],
                        show_details
                    )
                    return {
                        "success": True,
                        "data": model_details
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Multiple models named '{model_name}' found",
                        "data": None,
                        "multiple_matches": [
                            {
                                "unique_id": m["unique_id"],
                                "resource_id": m["resource_id"],
                                "schema": m["manifest_data"].get("schema"),
                                "database": m["manifest_data"].get("database")
                            }
                            for m in found_models
                        ]
                    }
            
            # Fallback search
            artifacts = await project_manager.get_project_artifacts(resource_id or [])
            if not artifacts:
                return {
                    "success": False,
                    "error": "No artifacts available",
                    "data": None
                }
            
            for proj_id, (manifest, catalog) in artifacts.items():
                model_node, found_unique_id = self._find_model_node(
                    manifest, unique_id, model_name, table_name
                )
                if model_node and found_unique_id:
                    model_details = self._format_model_details(
                        model_node, found_unique_id, catalog, proj_id, show_details
                    )
                    return {
                        "success": True,
                        "data": model_details
                    }
            
            identifier = unique_id or model_name or table_name
            return {
                "success": False,
                "error": f"Model '{identifier}' not found",
                "data": None
            }
            
        except Exception as e:
            logger.error(f"Error in get_model_details: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "data": None
            }
    
    async def get_description(
        self,
        doc_name: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """Get documentation block by name and resource."""
        try:
            if not resource_id:
                return {
                    "success": False,
                    "error": "resource_id is required",
                    "data": []
                }
            
            # Load project artifacts
            artifacts = await project_manager.get_project_artifacts(resource_id)
            if not artifacts:
                return {
                    "success": False,
                    "error": "No artifacts available",
                    "data": []
                }
            
            # Search for documentation blocks
            all_matching_docs = []
            for proj_id, (manifest, _) in artifacts.items():
                docs = manifest.get("docs", {})
                if isinstance(docs, dict):
                    for doc_id, doc_info in docs.items():
                        if (isinstance(doc_info, dict) and 
                            doc_info.get("resource_type") == "doc" and
                            doc_info.get("name") == doc_name):
                            all_matching_docs.append({
                                "project_id": proj_id,
                                "doc_id": doc_id,
                                "name": doc_info.get("name"),
                                "package_name": doc_info.get("package_name"),
                                "path": doc_info.get("original_file_path"),
                                "content": doc_info.get("block_contents", "")
                            })
            
            if not all_matching_docs:
                return {
                    "success": False,
                    "error": f"Documentation block '{doc_name}' not found",
                    "data": []
                }
            
            return {
                "success": True,
                "data": all_matching_docs,
                "count": len(all_matching_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in get_description: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "data": []
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
        
        # Determine if this is a partial match
        is_partial_match = len(matches) > 1 and len(exact_matches) == 0
        
        # Get suggestions
        suggested_terms = []
        if is_partial_match:
            for resource in matches:
                resource_id = resource.get("id", "")
                if resource_id and resource_id not in suggested_terms:
                    suggested_terms.append(resource_id)
        
        return matches, is_partial_match, suggested_terms
    
    def _filter_models_by_criteria(
        self, 
        models: Dict[str, Any], 
        schema: Optional[str], 
        level: Optional[str], 
        resource_id: str,
        show_details: bool = False
    ) -> List[Dict[str, Any]]:
        """Filter models based on schema or medallion level criteria."""
        filtered_models = []
        
        for model_id, model_info in models.items():
            if not isinstance(model_info, dict) or model_info.get("resource_type") != "model":
                continue
            
            matches = False
            
            if schema:
                # Exact schema match to avoid partial matches (e.g., "core" matching "scores")
                matches = schema.lower() == model_info.get("schema", "").lower()
            elif level:
                model_fqn = model_info.get("fqn", [])
                if level == "bronze":
                    matches = any("bronze" in part.lower() for part in model_fqn) or "bronze" in model_info.get("schema", "").lower()
                elif level == "silver":
                    matches = any("silver" in part.lower() for part in model_fqn) or "silver" in model_info.get("schema", "").lower()
                elif level == "gold":
                    # Exclude fsc_utils models from gold results  
                    if "fsc_utils" in model_id:
                        matches = False
                    else:
                        matches = any("gold" in part.lower() for part in model_fqn) or "gold" in model_info.get("schema", "").lower()
            else:
                # If no schema or level filter provided, include all models from the resource
                matches = True
            
            if matches:
                # Base fields (always included)
                model_data = {
                    "name": model_info.get("name"),
                    "database": model_info.get("database"),
                    "schema": model_info.get("schema"),
                    "description": model_info.get("description", ""),
                    "relation_name": model_info.get("relation_name")
                }
                
                # Additional fields when show_details=True
                if show_details:
                    model_data.update({
                        "unique_id": model_id,
                        "materialized": model_info.get("config", {}).get("materialized"),
                        "tags": model_info.get("tags", []),
                        "path": model_info.get("original_file_path"),
                        "fqn": model_info.get("fqn", []),
                        "resource_id": resource_id
                    })
                
                filtered_models.append(model_data)
        
        return sorted(filtered_models, key=lambda x: (x.get("schema", ""), x.get("name", "")))
    
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
            model_node = nodes.get(unique_id)
            if model_node and model_node.get("resource_type") == "model":
                return model_node, unique_id
            return None, None
        
        elif model_name:
            for node_id, node in nodes.items():
                if (isinstance(node, dict) and 
                    node.get("resource_type") == "model" and 
                    node.get("name") == model_name):
                    return node, node_id
        
        elif table_name:
            matching_models = []
            for node_id, node in nodes.items():
                if not isinstance(node, dict) or node.get("resource_type") != "model":
                    continue
                
                relation_name = node.get("relation_name", "")
                if relation_name and relation_name.endswith(f".{table_name}"):
                    matching_models.append((node, node_id))
                    continue
                
                model_node_name = node.get("name", "")
                if (model_node_name.endswith(f"__{table_name}") or 
                    model_node_name.endswith(f"_{table_name}") or
                    model_node_name == table_name):
                    matching_models.append((node, node_id))
            
            if matching_models:
                return matching_models[0]
        
        return None, None
    
    def _format_model_details(
        self, 
        model_node: Dict[str, Any], 
        unique_id: str, 
        catalog: Dict[str, Any], 
        resource_id: str,
        show_details: bool = False
    ) -> Dict[str, Any]:
        """Format model details into a structured response."""
        catalog_node = catalog.get("nodes", {}).get(unique_id, {})
        
        # Extract column information
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
        
        # Enhance with catalog column information
        catalog_columns = catalog_node.get("columns", {})
        if isinstance(catalog_columns, dict):
            for col_name, col_info in catalog_columns.items():
                if col_name in columns:
                    columns[col_name].update({
                        "type": col_info.get("type"),
                        "index": col_info.get("index"),
                        "comment": col_info.get("comment")
                    })
                else:
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
        
        # Base fields (always included for /models/{id})
        result = {
            "name": model_node.get("name"),
            "database": model_node.get("database"),
            "schema": model_node.get("schema"),
            "description": model_node.get("description", ""),
            "relation_name": model_node.get("relation_name"),
            "columns": columns
        }
        
        # Additional fields when show_details=True
        if show_details:
            result.update({
                "unique_id": unique_id,
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
                "catalog_metadata": catalog_node.get("metadata", {}),
                "stats": catalog_node.get("stats", {})
            })
        
        return result
    
    async def _find_model_by_fqn(
        self, 
        database: str, 
        schema: str, 
        table: str, 
        resource_id: Optional[str] = None,
        show_details: bool = False
    ) -> Dict[str, Any]:
        """Find model by fully qualified name (database.schema.table)."""
        try:
            # Determine which resources to search
            if resource_id:
                search_resources = [resource_id] if isinstance(resource_id, str) else resource_id
            else:
                search_resources = resource_registry.list_project_ids()
            
            # Load artifacts and search
            for res_id in search_resources:
                try:
                    artifacts = await project_manager.get_project_artifacts([res_id])
                    if not artifacts or res_id not in artifacts:
                        continue
                    
                    manifest, catalog = artifacts[res_id]
                    nodes = manifest.get("nodes", {})
                    
                    if not isinstance(nodes, dict):
                        continue
                    
                    # Search for model matching the FQN
                    for node_id, node in nodes.items():
                        if not isinstance(node, dict) or node.get("resource_type") != "model":
                            continue
                        
                        # Check if model matches database.schema.table
                        model_database = node.get("database", "").lower()
                        model_schema = node.get("schema", "").lower()
                        
                        # Also check relation_name for full match
                        relation_name = node.get("relation_name", "")
                        expected_fqn = f"{database.lower()}.{schema.lower()}.{table.lower()}"
                        
                        if (model_database == database.lower() and 
                            model_schema == schema.lower() and
                            (node.get("name", "").lower() == table.lower() or
                             relation_name.lower().endswith(f".{table.lower()}"))):
                            
                            model_details = self._format_model_details(node, node_id, catalog, res_id, show_details)
                            return {
                                "success": True,
                                "data": model_details
                            }
                
                except Exception as e:
                    logger.warning(f"Error searching resource {res_id} for FQN: {e}")
                    continue
            
            return {
                "success": False,
                "error": f"Model with FQN '{database}.{schema}.{table}' not found",
                "data": None
            }
            
        except Exception as e:
            logger.error(f"Error in _find_model_by_fqn: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "data": None
            }


# Global service instance
service = DataDiscoveryService()