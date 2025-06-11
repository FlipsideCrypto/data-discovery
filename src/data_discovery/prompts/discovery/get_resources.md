List available blockchain dbt projects. **Use this first** to discover what data is available for analysis.

**Parameters:**
- `show_details`: Include schemas, aliases, and URLs (default: false)
- `blockchain_filter`: Filter by blockchain name or alias (e.g., "ethereum", "eth", "bitcoin", "btc") 
- `category_filter`: Filter by category ("evm", "l1", "svm", "multi-chain", "internal")

**Returns:**
- **Resource ID**: Primary identifier for other tools (e.g., "ethereum-models", "bitcoin-models")
- **Aliases**: Alternative names (e.g., "eth", "btc") 
- **Blockchain**: Ecosystem covered (e.g., "ethereum", "bitcoin")
- **Category**: Technical type ("evm", "l1", "svm", etc.)
- **Schemas**: Available data layers ("core", "defi", "nft", "bronze", "silver", "gold")

**Key Categories:**
- **"evm"**: Ethereum, Polygon, Arbitrum, Avalanche, etc.
- **"l1"**: Bitcoin, Near, Flow
- **"svm"**: Solana ecosystem

**Examples:**
- `get_resources()` - All available projects
- `get_resources(blockchain_filter="eth")` - Ethereum projects (using alias)
- `get_resources(category_filter="evm")` - All EVM-compatible chains
- `get_resources(show_details=true)` - Full details including schemas and URLs