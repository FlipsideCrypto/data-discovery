Retrieves documentation blocks from dbt projects. Use for getting project descriptions, expert context (`__MCP__` blocks), and domain-specific documentation.

**Parameters:**
- `doc_name`: Documentation block name (default: "__overview__")
- `resource_id`: **REQUIRED** - Single string or array of project IDs from get_resources()

**Key blocks:**
- `__overview__`: Project description
- `__MCP__`: Expert blockchain knowledge and context

**Examples:**
- `get_description(resource_id="bitcoin-models")` - Get Bitcoin project overview
- `get_description(doc_name="__MCP__", resource_id="ethereum-models")` - Get Ethereum expert context
- `get_description(resource_id=["bitcoin-models", "ethereum-models"])` - Multi-project search
