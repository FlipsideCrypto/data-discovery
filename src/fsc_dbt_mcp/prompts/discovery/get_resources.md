Lists all available dbt project resources (blockchain datasets) that can be used with other discovery tools. **Essential for discovery** - use this first to understand what blockchain data projects are available for analysis.

**Parameters:**
`show_details`: Include detailed information like schemas, aliases, and artifact locations (default: false)  
`blockchain_filter`: Filter resources by blockchain name or alias (e.g., 'ethereum', 'eth', 'bitcoin', 'btc', 'multi-chain')  
`category_filter`: Filter resources by category (e.g., 'evm', 'l1', 'svm', 'multi-chain', 'internal')

**Resource Discovery:**
- Shows all blockchain projects available for dbt model exploration
- Organized by blockchain ecosystem (Bitcoin, Ethereum, multi-chain, etc.)
- Displays resource IDs and aliases that can be used in other tools
- Indicates project type (local development vs GitHub repositories)
- Shows available schemas (core, bronze, silver, gold, defi, nft, etc.)

**Key Information Provided:**
- **Resource ID**: Primary identifier for use in other tools (e.g., "ethereum-models", "bitcoin-models")
- **Aliases**: Alternative names that can be used to reference the resource (e.g., ["ethereum", "eth", "ethereum_models"])
- **Blockchain**: Which blockchain ecosystem the data covers (e.g., "ethereum", "bitcoin", "polygon")
- **Category**: Technical classification (e.g., "evm", "l1", "svm", "multi-chain", "internal")
- **Schemas**: Available data layers following medallion architecture (e.g., ["core", "bronze", "silver", "gold", "defi"])
- **URLs**: GitHub artifact locations for manifest.json and catalog.json (when show_details=true)

**Field Definitions (when show_details=true):**

**Aliases** - Alternative names you can use to reference this resource in other tools:
- Includes the main blockchain name (e.g., "ethereum") 
- Common abbreviations (e.g., "eth" for Ethereum, "btc" for Bitcoin)
- Underscore variations (e.g., "ethereum_models")
- Used for flexible resource identification across tools

**Category** - Technical classification of the blockchain ecosystem:
- **"evm"** - Ethereum Virtual Machine compatible chains (Ethereum, Polygon, Arbitrum, Avalanche, etc.)
- **"l1"** - Layer 1 blockchains (Bitcoin, Near, Flow)
- **"svm"** - Solana Virtual Machine projects (Solana)
- **"multi-chain"** - Cross-chain and bridge protocols
- **"internal"** - FlipsideCrypto internal tools and metrics

**Schemas** - Data layers following the medallion architecture:
- **"bronze"** - Raw, unprocessed blockchain data
- **"silver"** - Cleaned and standardized data
- **"gold"** - Business-ready aggregated data
- **"core"** - Essential standardized tables (fact_transactions, dim_contracts, etc.)
- **"defi"** - DeFi protocol specific data (DEXs, lending, etc.)
- **"nft"** - NFT marketplace and collection data

**Blockchain Filter with Alias Support:**
The `blockchain_filter` parameter matches against both the main blockchain name AND all aliases. Examples:
- `blockchain_filter="eth"` matches Ethereum (via alias)
- `blockchain_filter="btc"` matches Bitcoin (via alias) 
- `blockchain_filter="polygon"` matches Polygon (via main name)
- `blockchain_filter="matic"` matches Polygon (via alias)

**Smart Partial Match Detection:**
When a partial filter matches multiple resources, the tool provides helpful suggestions with resource IDs:
- `blockchain_filter="bit"` matches Bitcoin and Arbitrum → Shows "Did you mean 'bitcoin-models', 'arbitrum-models'?"
- `blockchain_filter="a"` matches 7 resources → Shows "Did you mean 'arbitrum-models', 'avalanche-models', 'crosschain-models' or others?"
- `blockchain_filter="pol"` matches only Polygon → No suggestions (single match)
- Exact matches (like "eth" or "bitcoin") don't trigger suggestions

**Usage Examples:**
1. **Quick overview**: `get_resources()` - See all available blockchain projects
2. **Detailed view**: `get_resources(show_details=true)` - Full information including schemas and URLs
3. **Ethereum focus**: `get_resources(blockchain_filter="ethereum")` - Only Ethereum-related projects
4. **Using aliases**: `get_resources(blockchain_filter="eth")` - Same as above, using alias
5. **Bitcoin by alias**: `get_resources(blockchain_filter="btc")` - Bitcoin projects using alias
6. **Polygon variations**: `get_resources(blockchain_filter="matic")` - Polygon via alias
7. **EVM ecosystems**: `get_resources(category_filter="evm")` - All EVM-compatible chains (Ethereum, Polygon, Arbitrum, etc.)
8. **Layer 1 chains**: `get_resources(category_filter="l1")` - Bitcoin, Near, and other L1 blockchains
9. **Solana ecosystem**: `get_resources(category_filter="svm")` - Solana Virtual Machine projects
10. **DeFi analysis**: `get_resources(category_filter="evm", show_details=true)` - Detailed EVM info

**Perfect for:**
- **Starting analysis**: Understand what blockchain data is available
- **Resource planning**: See which projects cover your target blockchain
- **Alias discovery**: Find alternative ways to reference projects
- **Schema exploration**: Understand medallion architecture across projects
- **Cross-chain analysis**: Identify multi-chain and cross-ecosystem projects

**Integration with other tools:**
Use the resource IDs from this tool in:
- `get_models(resource_id="ethereum-models")` - Get models from specific project
- `get_model_details(resource_id=["bitcoin-models", "ethereum-models"])` - Search across projects
- `get_description(resource_id="ethereum-models")` - Get project-specific documentation