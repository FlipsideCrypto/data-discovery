Retrieves documentation blocks from dbt manifests by name (e.g., __MCP__ blocks) to provide domain expertise and guidelines. **Supports multi-resource operations** - can search across multiple blockchain data resources to find comprehensive documentation.

The DEFAULT and primary documentation block is `__overview____` as this often contains descriptive information about the dbt project. This is not comprehensive and should not be relied on as the sole source of information for a project.  

IF EXISTS, a documentation block `__MCP__` contains **expert information** about the project or blockchain.  

**Parameters:**
`doc_name`: Name of the documentation block to retrieve (default: "__overview__")
`resource_id`: **REQUIRED** - Resource ID(s) to search in. Can be a single resource ID string or array of resource IDs (max 5). Required to avoid cross-contamination of blockchain-specific documentation.

**Multi-Resource Documentation Discovery:**
- Searches across multiple blockchain data resources simultaneously
- Aggregates documentation from different resources (e.g., Bitcoin, Ethereum, multi-chain)
- Results grouped by resource for clarity
- Perfect for gathering comprehensive domain expertise across blockchain ecosystems

**Use Cases:**
- **General project information**: Search for the default `__overview__` documentation.
- **Expert context building**: Find `__MCP__` blocks across resources to understand blockchain data modeling patterns
- **Column documentation**: Get specific column docs without loading entire model metadata
- **Cross-resource guidelines**: Access documentation blocks that provide guidelines across multiple blockchain datasets
- **Lightweight queries**: Get just documentation content when you don't need full model metadata

**Usage Examples:**
1. **Get expert context for specific resource**: `get_description(doc_name="__MCP__", resource_id="bitcoin-models")`
2. **Find documentation in multiple blockchain resources**: `get_description(doc_name="trading_metrics", resource_id=["ethereum-models", "bitcoin-models"])`
3. **Resource-specific documentation**: `get_description(doc_name="defi_concepts", resource_id="ethereum-models")`

**Important:** `resource_id` is required to prevent mixing blockchain-specific context that could confuse analysis.
