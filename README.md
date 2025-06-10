# FSC dbt-MCP Server dba `data-discovery`

A lightweight Model Context Protocol (MCP) server that provides both dbt Core CLI functionality and custom discovery tools for dbt projects. This server integrates with local dbt projects and provides a Claude Desktop-compatible MCP interface.

## Features

- **dbt CLI Tools**: Essential dbt commands (list, compile, show) 
- **Discovery Tools**: Custom tools for exploring dbt models and project metadata
- **Claude Desktop Integration**: Ready-to-use configuration for Claude Desktop
- **Prompt-Based Descriptions**: Rich tool descriptions loaded from markdown files

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

**Required:**
- `DBT_PROJECT_DIR` - Path to your dbt project directory (containing `dbt_project.yml`)

**Optional:**
- `DBT_PATH` - Full path to dbt executable (recommended for pyenv users)
- `DEBUG` - Enable debug logging (`true`/`false`)
- `MAX_FILE_SIZE` - Maximum file size for JSON artifacts (default: 10MB)
- `DEPLOYMENT_MODE` - Deployment mode (`local`, `desktop`, `remote`) - affects cache directory location
- `CACHE_DIR` - Custom cache directory path (overrides deployment mode defaults)

### Common Setup Examples

**Standard installation:**
```bash
export DBT_PROJECT_DIR=/path/to/your/dbt/project
export DEPLOYMENT_MODE=local
```

**pyenv users (recommended):**
```bash
export DBT_PROJECT_DIR=/path/to/your/dbt/project
export DBT_PATH=/Users/username/.pyenv/versions/3.12.11/bin/dbt
export DEPLOYMENT_MODE=local
```

> **Note**: Setting `DBT_PATH` is especially important for pyenv users, as older dbt versions may not support all CLI flags (like `--log-format`) used by this server.

### Deployment Modes

The `DEPLOYMENT_MODE` environment variable controls how the server handles file paths and cache directories:

- **`local`** (default): Uses relative `target/` directory for cache. Best for local development and MCP Inspector testing.
- **`desktop`**: Uses `~/.cache/fsc-dbt-mcp/` for cache. **Required for Claude Desktop** to avoid read-only file system errors.
- **`remote`**: Uses `~/.cache/fsc-dbt-mcp/` for cache. For containerized or remote deployments.

### dbt Profiles

The server looks for dbt profiles in:
1. `$DBT_PROFILES_DIR` (if set)
2. `$HOME/.dbt` (default location)

## Claude Desktop Setup

1. **Update Claude Desktop configuration** by adding the server configuration to your Claude Desktop MCP settings:

   ```json
   {
     "mcpServers": {
       "fsc-dbt-mcp": {
         "command": "python",
         "args": ["/path/to/your/fsc-dbt-mcp/src/fsc_dbt_mcp/server.py"],
         "env": {
           "DBT_PROJECT_DIR": "/path/to/your/dbt/project",
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

**dbt CLI Commands:**
- "List all dbt models in the project"
- "Compile the dbt project" 
- "Show me the top 5 rows from the users table"
- "Execute this SQL query: SELECT * FROM fact_orders"

**Discovery Tools:**
- "Get details about the customer_orders model"
- "Show me information about model.my_project.sales_summary"
- "What columns does the users table have?"

## Available Tools

### dbt CLI Tools (3 tools)
- **`dbt_list`** - List dbt resources (models, tests, sources, etc.) with optional selectors
- **`dbt_compile`** - Compile dbt models to generate SQL without executing
- **`dbt_show`** - Execute inline SQL queries against the data warehouse with sample results

### Discovery Tools (1 tool)
- **`get_model_details`** - Retrieve comprehensive model metadata including:
  - Model description, schema, database, materialization
  - Column details with types, descriptions, and comments  
  - Dependencies (refs and sources)
  - Statistics from catalog
  - Raw and compiled SQL
  - Tags, meta properties, and constraints

## Architecture

This server provides a unified MCP interface that combines:
- **dbt CLI Tools**: Direct subprocess calls to dbt commands with proper logging
- **Discovery Tools**: Custom implementations that parse dbt manifest.json and catalog.json artifacts
- **Prompt System**: Tool descriptions loaded from markdown files for rich, detailed help text

All tools run in a single MCP server process for simplified deployment.

## Troubleshooting

### Common Issues

1. **"DBT_PROJECT_DIR environment variable not set"**
   - Set `DBT_PROJECT_DIR` environment variable
   - Ensure you have a valid `dbt_project.yml` file in that directory

2. **"dbt command not found"**
   - Verify dbt is installed: `dbt --version`
   - For pyenv users: Set `DBT_PATH` to full dbt executable path
   - Example: `export DBT_PATH=/Users/username/.pyenv/versions/3.12.11/bin/dbt`

3. **"syntax error line 3 at position 2 unexpected 'limit'"**
   - LIMIT should be passed as a parameter, not in the query text.

4. **dbt: error: unrecognized arguments: --log-format json**
   - This occurs with older dbt versions that don't support `--log-format` flag
   - Solution: Set `DBT_PATH` to a compatible dbt version (≥1.9)
   - This likely occurs if multiple python versions are maintained via `pyenv`

5. **"No valid dbt artifacts found"**
   - Run `dbt compile` in your dbt project to generate manifest.json
   - Run `dbt docs generate` to create catalog.json
   - Ensure target/ directory exists in your dbt project

### Validation

Test the server manually:
```bash
python src/fsc_dbt_mcp/server.py
```

## Requirements

- Python 3.12+
- dbt Core installation (≥1.0 recommended)
- Valid dbt project with `dbt_project.yml`
- dbt profiles configured in `~/.dbt/profiles.yml`
- Generated dbt artifacts (`target/manifest.json` and `target/catalog.json`)

## Dependencies

- `dbt-mcp>=0.2.5` - Used for reference (not directly imported)
- `mcp` - Model Context Protocol SDK

## License

This project is inspired by the `dbt-mcp` package from dbt-labs but implements custom tooling.