# Custom dbt MCP Server - Core Tools Only

A lightweight Model Context Protocol (MCP) server that exposes only dbt Core functionality using the `dbt-mcp` package as a base. This server integrates with local dbt projects and provides Claude Desktop-compatible MCP interface.

## Features

- **Core dbt Operations Only**: Exposes only essential dbt commands (run, test, compile, parse, clean, deps)
- **Auto-Discovery**: Automatically finds and configures local dbt projects
- **Claude Desktop Integration**: Ready-to-use configuration for Claude Desktop
- **Lightweight**: Minimal dependencies and focused functionality

## Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone or download this repository**

3. **Verify dbt installation**:
   ```bash
   dbt --version
   ```

## Configuration

### Required Setup

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Set your dbt project path** in the `.env` file:
   ```
   DBT_PROJECT_DIR=/path/to/your/dbt/project
   ```

### dbt Profiles

The server looks for dbt profiles in:
1. `$DBT_PROFILES_DIR` (if set)
2. `$HOME/.dbt` (default location)

## Claude Desktop Setup

1. **Update Claude Desktop configuration** by adding the contents of `claude_config.json` to your Claude Desktop MCP settings.

2. **Adjust the paths** in `claude_config.json` to match your installation:
   ```json
   {
     "mcpServers": {
       "dbt-core": {
         "command": "uvx",
         "args": [
           "--env-file",
            "/path/to/your/fsc-dbt-mcp/.env",
            "dbt-mcp"
         ]
       }
     }
   }
   ```

3. **Restart Claude Desktop** to load the new MCP server.

## Usage

Once configured with Claude Desktop, you can use dbt commands through Claude:

- "Run my dbt models"
- "Test the dbt project"
- "Compile the dbt project"
- "Show me the dbt project structure"
- "Clean dbt artifacts"

## Available dbt Core Tools

The server exposes only these essential dbt operations:
- `dbt run` - Execute models
- `dbt test` - Run tests  
- `dbt compile` - Compile models
- `dbt parse` - Parse project
- `dbt clean` - Clean artifacts
- `dbt deps` - Install dependencies
- Model and test file reading
- Project structure exploration

## Tool Filtering

The server disables non-core functionality through environment variables:
- `DISABLE_SEMANTIC_LAYER=true` - Disables semantic layer tools
- `DISABLE_DISCOVERY=true` - Disables discovery API tools
- `DISABLE_REMOTE=true` - Disables remote tools

## Troubleshooting

### Common Issues

1. **"dbt-mcp package not found"**
   - Install with: `pip install dbt-mcp`

2. **"DBT_PROJECT_DIR environment variable not set"**
   - Create a `.env` file from `.env.example`
   - Set `DBT_PROJECT_DIR` to your dbt project path
   - Ensure you have a valid `dbt_project.yml` file

3. **"dbt installation check failed"**
   - Verify dbt is installed: `dbt --version`
   - Ensure dbt is in your PATH

4. **Claude Desktop connection issues**
   - Check the server path in `claude_config.json`
   - Verify Python can be found at the specified path
   - Check Claude Desktop logs for error messages

### Validation

Test the server manually:
```bash
uvx --env-file .env fsc-dbt-mcp
```

## Requirements

- Python 3.12+
- uv package manager
- dbt Core installation  
- Valid dbt project with `dbt_project.yml`
- dbt profiles configured in `~/.dbt/profiles.yml`

## License

This project builds upon the `dbt-mcp` package from dbt-labs.