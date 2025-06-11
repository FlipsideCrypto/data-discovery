List and filter dbt models across projects. **At least one parameter required.**

**Parameters:**
- `schema`: Schema name (e.g., "core", "defi", "nft") - takes precedence over level
- `level`: Medallion level ("bronze", "silver", "gold") - ignored if schema provided  
- `resource_id`: Project ID(s) to search (from get_resources()) - searches all if omitted
- `limit`: Max results (default: 25, max: 250)

**Examples:**
- `get_models(schema="core")` - All core models across projects
- `get_models(level="gold", resource_id="ethereum-models")` - Gold models in Ethereum project
- `get_models(schema="defi", resource_id=["ethereum-models", "polygon-models"])` - DeFi models in specific projects
- `get_models(resource_id="bitcoin-models")` - All models in Bitcoin project
