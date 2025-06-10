Retrieves documentation blocks from dbt manifests by name (e.g., __MCP__ blocks) to provide domain expertise and guidelines. **Supports multi-project operations** - can search across multiple blockchain data projects to find comprehensive documentation.

The DEFAULT and primary documentation block is `__MCP__` (if exists) as this is where the LLM expert context is defined. This is the information to use when constructing an expert.  

**Parameters:**
`doc_name`: Name of the documentation block to retrieve (default: "__MCP__")
`project_id`: **REQUIRED** - Project ID(s) to search in. Can be a single project ID string or array of project IDs (max 5). Required to avoid cross-contamination of blockchain-specific documentation.

**Multi-Project Documentation Discovery:**
- Searches across multiple blockchain data projects simultaneously
- Aggregates documentation from different projects (e.g., Bitcoin, Ethereum, multi-chain)
- Results grouped by project for clarity
- Perfect for gathering comprehensive domain expertise across blockchain ecosystems

**Use Cases:**
- **Expert context building**: Find `__MCP__` blocks across projects to understand blockchain data modeling patterns
- **Column documentation**: Get specific column docs without loading entire model metadata
- **Cross-project guidelines**: Access documentation blocks that provide guidelines across multiple blockchain datasets
- **Lightweight queries**: Get just documentation content when you don't need full model metadata

**Usage Examples:**
1. **Get expert context for specific project**: `get_description(doc_name="__MCP__", project_id="bitcoin-models")`
2. **Find documentation in multiple blockchain projects**: `get_description(doc_name="trading_metrics", project_id=["ethereum-models", "bitcoin-models"])`
3. **Project-specific documentation**: `get_description(doc_name="defi_concepts", project_id="ethereum-models")`

**Important:** `project_id` is required to prevent mixing blockchain-specific context that could confuse analysis.
