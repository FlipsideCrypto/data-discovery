Retrieves a list of dbt models with optional filtering by schema or medallion level (bronze/silver/gold). **Supports multi-project operations** - can search across multiple blockchain data projects simultaneously. Combines functionality of get_all_models and get_gold_models in one tool.

**Parameters:**
`schema`: Filter models by schema name (e.g., 'core', 'defi', 'nft'). Takes precedence over level if both are provided.
`level`: Filter models by medallion level (bronze, silver, gold). Ignored if schema is provided.
`project_id`: Project ID(s) to search in. Can be a single project ID string or array of project IDs (max 5). If not provided, searches all available projects.
`limit`: Maximum number of models to return (default: 10, max: 200)

**Multi-Project Model Discovery:**
- Search across multiple blockchain data projects (Bitcoin, Ethereum, multi-chain, etc.)
- Results organized hierarchically: Project → Schema → Models
- Each model includes project context for clear identification
- Perfect for exploring model structure across different blockchain ecosystems
- Supports filtering by medallion architecture levels across all projects

**Default Behavior:**
- Defaults to 'core' schema when no filters are provided
- Searches all available projects when no project_id specified

**Usage Examples:**
1. **Core models across all projects**: `get_models()` (defaults to schema='core')
2. **DeFi models in specific projects**: `get_models(schema="defi", project_id=["ethereum-models", "polygon-models"])`
3. **Gold-level models across blockchain projects**: `get_models(level="gold", project_id=["bitcoin-models", "ethereum-models"])`
4. **All core models in single project**: `get_models(schema="core", project_id="ethereum-models", limit=50)`
5. **Cross-project NFT exploration**: `get_models(schema="nft")`

**Perfect for:**
- Exploring model structure across blockchain ecosystems
- Finding models within specific data layers or business domains
- Cross-project analysis and comparison
- Understanding medallion architecture implementation across projects
