# FSC dbt-MCP Server dba `data-discovery`

A lightweight Model Context Protocol (MCP) server that provides both dbt Core CLI functionality and custom discovery tools for dbt projects. **Now supports multi-project operations** - seamlessly work with multiple blockchain dbt projects including Bitcoin, Ethereum, and cross-chain analytics.

## Features

- **🚀 Multi-Project Support**: Work across Bitcoin, Ethereum, and multi-chain dbt projects simultaneously
- **📊 MCP Resources**: Discoverable project catalog via MCP Resources (`dbt://projects`)
- **🔧 dbt CLI Tools**: Essential dbt commands (list, compile, show) with project awareness
- **🔍 Discovery Tools**: Advanced model exploration with cross-project search capabilities
- **🏠 Claude Desktop Integration**: Production-ready configuration with deployment mode support
- **📖 Rich Documentation**: Markdown-based tool descriptions with blockchain-specific context

## Installation

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Verify dbt installation**:
   ```bash
   dbt --version
   ```

## Configuration

### Environment Variables

Set these environment variables for proper operation:

**Optional:**
- `DBT_PATH` - Full path to dbt executable (recommended for pyenv users)
- `DEBUG` - Enable debug logging (`true`/`false`)
- `MAX_FILE_SIZE` - Maximum file size for JSON artifacts (default: 10MB)
- `DEPLOYMENT_MODE` - Deployment mode (`local`, `desktop`, `remote`) - affects cache directory location
- `CACHE_DIR` - Custom cache directory path (overrides deployment mode defaults)

> **Note**: Setting `DBT_PATH` is especially important for pyenv users, as older dbt versions may not support all CLI flags (like `--log-format`) used by this server.

#### Deployment Modes

The `DEPLOYMENT_MODE` environment variable controls how the server handles file paths and cache directories:

- **`local`** (default): Uses relative `target/` directory for cache. Best for local development and MCP Inspector testing.
- **`desktop`**: Uses `~/.cache/fsc-dbt-mcp/` for cache. **Required for Claude Desktop** to avoid read-only file system errors.
- **`remote`**: Uses `~/.cache/fsc-dbt-mcp/` for cache. For containerized or remote deployments.

### dbt Profiles

The server looks for dbt profiles in:
1. `$DBT_PROFILES_DIR` (if set)
2. `$HOME/.dbt` (default location)

This is only required if using `dbt_cli` tools to execute dbt commands.

## Claude Desktop Setup

1. **Update Claude Desktop configuration** by adding the server configuration to your Claude Desktop MCP settings:

   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "command": "python",
         "args": ["/path/to/your/fsc-dbt-mcp/src/fsc_dbt_mcp/server.py"],
         "env": {
           "DBT_PATH": "/path/to/dbt/executable",
           "DEPLOYMENT_MODE": "desktop"
         }
       }
     }
   }
   ```

2. **Adjust the paths** to match your installation and set environment variables as needed.

3. **Restart Claude Desktop** to load the new MCP server.

## Usage

Once configured with Claude Desktop, you can use dbt commands and discovery tools through Claude:

**dbt CLI Commands:** (currently disabled)
- "List all dbt models in the project"
- "Compile the dbt project" 
- "Show me the top 5 rows from the users table"
- "Execute this SQL query: SELECT * FROM fact_orders"

**Discovery Tools:**
- "Get details about the customer_orders model" 
- "Show me Bitcoin transaction models in the core schema"
- "Find all DeFi models across Ethereum projects"
- "Get expert context for Bitcoin blockchain analysis"
- "List all models in ethereum-models project"

**Multi-Project Operations:**
- "Compare transaction models between Bitcoin and Ethereum"
- "Show me all gold-level models across blockchain projects"
- "Find models named 'dim_blocks' in any project"

## Available Tools

### dbt CLI Tools (3 tools)
- **`dbt_list`** - List dbt resources (models, tests, sources, etc.) with optional selectors
- **`dbt_compile`** - Compile dbt models to generate SQL without executing
- **`dbt_show`** - Execute inline SQL queries against the data warehouse with sample results

### Discovery Tools (4 tools)
- **`get_resources`** - Retrieve available dbt projects from the resource list.
- **`get_model_details`** - Retrieve comprehensive model metadata with multi-project support:
  - Model description, schema, database, materialization
  - Column details with types, descriptions, and comments  
  - Dependencies (refs and sources)
  - Statistics from catalog
  - Raw and compiled SQL
  - Tags, meta properties, and constraints
  - **Project-aware**: Auto-detects project from `uniqueId` or searches specified projects

- **`get_description`** - Retrieve documentation blocks (e.g., `__MCP__` expert context):
  - Project-specific documentation to prevent context mixing
  - Expert blockchain knowledge from documentation blocks
  - **Requires project_id** to maintain context isolation

- **`get_models`** - List and filter models across projects:
  - Filter by schema (core, defi, nft) or medallion level (bronze, silver, gold)
  - Multi-project search with hierarchical results (Project → Schema → Models)
  - Cross-blockchain model discovery

### MCP Resources (2 resources)
- **`dbt://projects`** - Discoverable catalog of all available dbt projects
- **`dbt://project/{id}`** - Detailed metadata for specific projects (Bitcoin, Ethereum, Kairos)

## Available Projects

The server comes pre-configured with access to multiple blockchain dbt projects.  

Use the MCP Resource `dbt://projects` to discover all available projects and their metadata.

## Troubleshooting

### Common Issues / Known Errors

1. **`Error executing code: Cannot convert undefined or null to object`**
   - The client passed `true` or `null` as `resource_id`
   - The client passed `null` as `resource_id` and the JSON artifact was unable to be retrieved or has not yet been cached.

2. **dbt: error: unrecognized arguments: --log-format json**
   - This occurs with older dbt versions that don't support `--log-format` flag
   - Solution: Set `DBT_PATH` to a compatible dbt version (≥1.9)
   - This likely occurs if multiple python versions are maintained via `pyenv`


3. **"dbt command not found"**
   - Verify dbt is installed: `dbt --version`
   - For pyenv users: Set `DBT_PATH` to full dbt executable path
   - Example: `export DBT_PATH=/Users/username/.pyenv/versions/3.12.11/bin/dbt`

### Validation

Test the server manually:
```bash
python src/fsc_dbt_mcp/server.py
```

## Requirements

- Python 3.12+

## Dependencies

- `dbt-mcp>=0.2.5` - Used for reference (not directly imported)
- `mcp` - Model Context Protocol SDK

## License

This project is inspired by the `dbt-mcp` package from dbt-labs but implements custom tooling.
