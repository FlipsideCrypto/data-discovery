# FSC Data Discovery Service

Dual-interface data discovery system for dbt projects. Provides both **MCP server** access for AI assistants and **REST API** for programmatic integration with blockchain data models from Bitcoin, Ethereum, and Kairos projects.

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐
│   MCP Interface     │    │   REST API          │
│ (Claude, AI tools)  │    │ (AI Platform Team)  │
└─────────┬───────────┘    └───────────┬─────────┘
          │                            │
          └─────────┬──────────────────┘
                    │
          ┌─────────▼───────────┐
          │  Shared Service     │
          │  (JSON responses)   │
          └─────────┬───────────┘
                    │
          ┌─────────▼───────────┐
          │ dbt Artifact Cache  │
          │ (GitHub + Local)    │
          └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- [UV](https://docs.astral.sh/uv/getting-started/installation/) with Python 3.10+
- Git

### Installation
```bash
# Clone and setup
git clone <repo-url>
cd data-discovery
uv venv --python 3.10
source .venv/bin/activate
uv sync

# Test the shared service
uv run python -c "from data_discovery.api.service import DataDiscoveryService; print('✅ Service ready')"
```

## 🔌 MCP Server Setup

For AI assistants like Claude Desktop:

1. **Add to Claude Desktop** (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "command": "/absolute/path/to/data-discovery/.venv/bin/python",
         "args": ["/absolute/path/to/src/data_discovery/server.py"],
         "env": {
           "DEPLOYMENT_MODE": "desktop"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop** and start exploring:
   - "Show me all Bitcoin core models"
   - "Get details on ethereum.core.fact_transactions using FQN"
   - "List available blockchain projects"

3. **Debug logs**: `tail -f ~/.cache/data-discovery/claude-server.log`

## 🛠️ Available Tools & Endpoints

### Discovery Tools ✅

| **MCP Tool** | **Future REST Endpoint** | **Description** |
|--------------|---------------------------|-----------------|
| `get_resources` | `GET /resources` | List available dbt projects (Bitcoin, Ethereum, Kairos) |
| `get_models` | `GET /models?filters` | Search models across projects with filtering |
| `get_model_details` | `GET /models/:id` | Comprehensive model metadata and schema |
| `get_description` | `GET /descriptions/:id` | Documentation blocks with expert context |

### Search Capabilities

#### **MCP Parameters** (for AI assistants)
```typescript
// Resource discovery
get_resources(show_details?: boolean, blockchain_filter?: string, category_filter?: string)

// Model search  
get_models(schema?: string, level?: string, resource_id?: string[], limit?: number)

// Model details with multiple search options
get_model_details({
  uniqueId?: string,           // "model.ethereum-models.core__fact_transactions"
  fqn?: string,               // "ethereum.core.fact_transactions" 
  model_name?: string,        // "core__fact_transactions"
  table_name?: string,        // "fact_transactions"
  resource_id?: string[]
})

// Documentation
get_description(doc_name: string, resource_id: string[])
```

#### **REST API Format** (coming soon)
```bash
# Resource discovery
GET /resources?show_details=true&blockchain_filter=ethereum

# Model search
GET /models?schema=core&resource_id=ethereum-models&limit=50

# Model details (multiple search options)
GET /models/model.ethereum-models.core__fact_transactions    # by unique_id
GET /models?fqn=ethereum.core.fact_transactions              # by FQN  
GET /models?model_name=core__fact_transactions               # by model name

# Documentation  
GET /descriptions/__overview__?resource_id=ethereum-models
```

### FQN (Fully Qualified Name) Support 🎯

Perfect for AI platform team integration:

```bash
# Supported FQN formats
ethereum.core.fact_transactions     # database.schema.table
core.fact_transactions              # schema.table

# Smart matching handles dbt conventions
core__fact_transactions → fact_transactions
defi_ethereum_uniswap_v3 → matches "uniswap_v3" table searches
```

## 🔧 Technical Details

### Shared Service Architecture

```python
# Core service class used by both interfaces
from data_discovery.api.service import DataDiscoveryService

service = DataDiscoveryService()

# Returns structured JSON (perfect for REST APIs)
result = await service.get_models(schema="core", limit=10)
# Result: {"models": [...], "total_found": 45, "truncated": false, ...}

# MCP tools convert JSON to TextContent for AI assistants
# REST endpoints return JSON directly
```

### Dependencies
- `mcp` - Model Context Protocol SDK
- `aiohttp` - Async HTTP for GitHub integration  
- `loguru` - Modern logging
- `dataclasses` - Property validation

### File Structure
```
src/data_discovery/
├── api/
│   ├── service.py              # Shared service layer (JSON responses)
│   └── rest.py                 # REST API endpoints (coming soon)
├── server.py                   # MCP server implementation
├── project_manager.py          # Multi-project artifact management  
├── resources/                  # Project definitions and MCP resources
├── tools/discovery/            # MCP tools (use shared service)
└── prompts/                    # Tool descriptions and help text
```

## 🚫 Deprecated Features

### dbt CLI Tools (Disabled)
Previously available, now disabled pending multi-project migration:
- `dbt_list`, `dbt_compile`, `dbt_show`

These may be re-enabled in future versions with multi-project support.

## ⚙️ Configuration

### Environment Variables
- `DEPLOYMENT_MODE` - Set to `"desktop"` for Claude Desktop (required)
- `DEBUG` - Enable debug logging (`"true"`/`"false"`)

### Deployment Modes
- **`desktop`** (recommended): Uses `~/.cache/data-discovery/` for cache
- **`local`**: Uses `target/` directory (development only)

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Test core imports
   python -c "from data_discovery.api.service import DataDiscoveryService; print('✅ OK')"
   ```

2. **MCP Server Issues**
   ```bash
   # Test MCP server directly
   python src/data_discovery/server.py
   ```

3. **Cache Issues**
   ```bash
   # Clear cache and restart
   rm -rf ~/.cache/data-discovery/
   ```

### Debug Logs
```bash
# MCP server logs (Claude Desktop)
tail -f ~/.cache/data-discovery/claude-server.log

# Service-level debugging  
export DEBUG=true
python -c "from loguru import logger; logger.info('Debug enabled')"
```

## 🚀 Deployment

### Current: MCP Server
- ✅ Ready for Claude Desktop and MCP clients
- ✅ Multi-project discovery with caching
- ✅ GitHub integration for remote artifacts

### Coming Soon: REST API  
- 🚧 FastAPI endpoints using shared service
- 🚧 ECS/Fargate deployment for AI platform team
- 🚧 Direct JSON responses for vector search integration

---

**Ready for both AI assistant integration (MCP) and programmatic access (REST API)**