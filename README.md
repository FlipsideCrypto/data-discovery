# FSC dbt MCP Server dba `data-discovery`

Model Context Protocol (MCP) server for dbt project discovery. Query Flipside dbt models through any MCP-enabled client.

## 🚀 Quickstart

1. **Install**:
   ```bash
   git clone <repo-url>
   cd fsc-dbt-mcp
   pip install -e .
   ```

2. **Add to Claude Desktop** (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "command": "python",
         "args": ["/absolute/path/to/fsc-dbt-mcp/src/fsc_dbt_mcp/server.py"],
         "env": {
           "DEPLOYMENT_MODE": "desktop"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** and start exploring:
   - "Show me all Bitcoin core models"
   - "Get details on ethereum transaction models"
   - "List available blockchain projects"

## Available Tools

### Discovery Tools ✅
- **`get_resources`** - List available dbt projects (Bitcoin, Ethereum, Kairos)
- **`get_models`** - Search models across projects with filtering
- **`get_model_details`** - Comprehensive model metadata and schema
- **`get_description`** - Documentation blocks with expert context

### dbt CLI Tools ⚠️ 
Currently disabled pending multi-project migration:
- `dbt_list`, `dbt_compile`, `dbt_show`

## Configuration

### Environment Variables
- `DEPLOYMENT_MODE` - Set to `"desktop"` for Claude Desktop (required)
- `DEBUG` - Enable debug logging (`"true"`/`"false"`)
- `DBT_PATH` - Full path to dbt executable (for pyenv users)

### Deployment Modes
- **`desktop`** (recommended): Uses `~/.cache/fsc-dbt-mcp/` for cache
- **`local`**: Uses `target/` directory (development only)

## Troubleshooting

### Common Issues
1. **`Error executing code: Cannot convert undefined or null to object`**
   - Client passed `null` as `resource_id` 
   - JSON artifacts not cached yet

2. **"dbt command not found"**
   - Set `DBT_PATH` environment variable
   - Example: `DBT_PATH=/Users/username/.pyenv/versions/3.12.11/bin/dbt`

### Test Server
```bash
python src/fsc_dbt_mcp/server.py
```

## Technical Details

### Dependencies
- `mcp` - Model Context Protocol SDK
- `aiohttp` - Async HTTP for GitHub integration

### Architecture
- Multi-project artifact management with local caching
- GitHub integration for remote dbt artifacts  
- MCP Resources for project discovery
- Property-based input validation
