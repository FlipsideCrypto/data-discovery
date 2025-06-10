Retrieves a list of dbt models with optional filtering by schema or medallion level (bronze/silver/gold). **Supports multi-resource operations** - can search across multiple blockchain data resources simultaneously. Combines functionality of get_all_models and get_gold_models in one tool.

**Parameters:**
`schema`: Filter models by schema name (e.g., 'core', 'defi', 'nft'). Takes precedence over level if both are provided.
`level`: Filter models by medallion level (bronze, silver, gold). Ignored if schema is provided.
`resource_id`: Resource ID(s) to search in. Can be a single resource ID string or array of resource IDs (max 5). If not provided, searches all available resources. DO NOT PASS `true` OR `null` AS `resource_id`!
`limit`: Maximum number of models to return (default: 10, max: 200)

**Multi-Resource Model Discovery:**
- Search across multiple blockchain data resources (Bitcoin, Ethereum, multi-chain, etc.)
- Results organized hierarchically: Resource → Schema → Models
- Each model includes resource context for clear identification
- Perfect for exploring model structure across different blockchain ecosystems
- Supports filtering by medallion architecture levels across all resources

**Default Behavior:**
- Defaults to 'core' schema when no filters are provided
- Searches all available resources when no resource_id specified

**Usage Examples:**
1. **Core models across all resources**: `get_models()` (defaults to schema='core')
2. **DeFi models in specific resources**: `get_models(schema="defi", resource_id=["ethereum-models", "polygon-models"])`
3. **Gold-level models across blockchain resources**: `get_models(level="gold", resource_id=["bitcoin-models", "ethereum-models"])`
4. **All core models in single resource**: `get_models(schema="core", resource_id="ethereum-models", limit=50)`
5. **Cross-resource NFT exploration**: `get_models(schema="nft")`

**Perfect for:**
- Exploring model structure across blockchain ecosystems
- Finding models within specific data layers or business domains
- Cross-resource analysis and comparison
- Understanding medallion architecture implementation across resources
