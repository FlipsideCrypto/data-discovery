get_model_details provides structured metadata (Type, Description, Comment) about a specific dbt model, returning the column documentation PLUS type information, model structure, dependencies, and compiled SQL. **Supports multi-project operations** - can search across multiple blockchain data projects simultaneously.

IMPORTANT: Use uniqueId when available.  
 - Using uniqueId guarantees the correct model is retrieved  
 - Using only model_name may return incorrect results or fail entirely  
 - If you obtained models via get_models(), you should always use the uniqueId from those results  

**Parameters:**
`uniqueId`: The unique identifier of the model (format: "model.project_name.model_name"). STRONGLY RECOMMENDED when available. Example `model.ethereum_models.core__fact_blocks`.   
`model_name`: The name of the dbt model. Only use this when uniqueId is unavailable. Example `core__fact_blocks`  
`table_name`: The table name to search for (e.g., `fact_transactions`). Searches across all schemas for models that produce this table name. Useful when you know the table name but not the full model name.   
`resource_id`: Resource ID(s) to search in. Can be a single resource ID string or array of resource IDs (max 5). If not provided, searches all available resources. Use this to focus searches on specific blockchain data projects. Example `ethereum-models`.  

**Multi-Project Intelligence:**
- When using `uniqueId`, automatically extracts and targets the specific project from the ID format
- When using `model_name` or `table_name`, searches across specified projects (or all projects if none specified)
- If multiple models with the same name exist across projects, shows disambiguation with project context
- Response includes project information to clarify which blockchain dataset the model belongs to

**Usage Examples:**
1. **PREFERRED METHOD** - Using uniqueId (always use this when available): `get_model_details(uniqueId="model.bitcoin-models.core__fact_transactions")`
2. **Multi-project search** - Find model across specific projects: `get_model_details(model_name="core__fact_blocks", resource_id=["bitcoin-models", "ethereum-models"])`
3. **Table name search** - Find model by table name: `get_model_details(table_name="fact_transactions", resource_id="bitcoin-models")`
4. **FALLBACK METHOD** - Using only model_name (searches all projects): `get_model_details(model_name="fact_transactions")`
