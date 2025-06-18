# Data Discovery API

**REST API-first** data discovery system for dbt projects across blockchain datasets. Provides FastAPI endpoints with optional MCP tool integration for AI agents.

## 🚀 Quickstart

### Prerequisites
- [UV](https://docs.astral.sh/uv/getting-started/installation/) with `Python 3.10` or higher
- Git

### 🔌 REST API (Primary)

1. **Installation**:
   ```bash
   # Clone and setup
   git clone <repo-url>
   cd data-discovery
   uv sync
   
   # Configure environment (optional)
   cp .env.example .env
   # Edit .env as needed
   ```

2. **Start the API server**:
   ```bash
   # Development server with hot reload
   uv run uvicorn src.data_discovery.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using the main module
   uv run python src/data_discovery/main.py
   ```

3. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # List resources
   curl http://localhost:8000/api/v1/discovery/resources
   
   # API documentation
   open http://localhost:8000/docs
   ```

### 🤖 MCP Integration (Claude Desktop)

For Claude Desktop, use the uv directory approach (similar to other MCP servers):

1. **Add to Claude Desktop** (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "command": "/absolute/path/to/.local/bin/uv",
         "args": [
           "--directory",
           "/absolute/path/to/data-discovery",
           "run",
           "src/data_discovery/server.py"
         ],
         "env": {
           "DEPLOYMENT_MODE": "desktop"
         }
       }
     }
   }
   ```

2. **Alternative - Direct Python path**:
   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "command": "/absolute/path/to/data-discovery/.venv/bin/python",
         "args": ["/absolute/path/to/data-discovery/src/data_discovery/server.py"],
         "env": {
           "DEPLOYMENT_MODE": "desktop"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop** and explore:
   - "Show me all Bitcoin core models"
   - "Get details on ethereum transaction models"
   - "List available blockchain projects"

## 📊 API Endpoints

### Core Discovery Endpoints
- **`GET /api/v1/discovery/resources`** - List available dbt projects with filtering
- **`GET /api/v1/discovery/models`** - Search models by schema, level, or resource
- **`GET /api/v1/discovery/models/{unique_id}`** - Get detailed model information
- **`GET /api/v1/discovery/descriptions/{doc_name}`** - Retrieve documentation blocks

### Additional Endpoints
- **`GET /health`** - Health check and status
- **`GET /docs`** - Interactive API documentation
- **`GET /openapi.json`** - OpenAPI specification
- **`/mcp`** - MCP protocol endpoint (when fastapi_mcp available)

### MCP Tools (Auto-Generated)
When accessed via MCP clients, the REST endpoints are automatically exposed as tools:
- **`get_resources`** - List available dbt projects
- **`get_models`** - Search models across projects
- **`get_model_by_id`** - Get model details by unique ID
- **`get_description`** - Documentation blocks with context

## ⚙️ Configuration

### Environment Variables
All configuration can be set via environment variables or `.env` file:

```bash
# API Server Settings
API_HOST=0.0.0.0           # Server host
API_PORT=8000              # Server port

# Application Settings  
DEBUG_MODE=false           # Enable debug logging
DEPLOYMENT_MODE=api        # Deployment mode (api/desktop)
LOG_LEVEL=INFO            # Logging level

# Resource Limits
MAX_FILE_SIZE=10485760    # Max file size (10MB)
MAX_PROJECTS=50           # Max projects to load simultaneously
```

### Deployment Modes
- **`api`** (default): REST API server mode
- **`desktop`**: Claude Desktop MCP integration mode
- **`local`**: Development mode with local caching

## 🔧 Troubleshooting

### Common Issues

1. **API Server Won't Start**
   ```bash
   # Check if port is in use
   lsof -i :8000
   
   # Use different port
   API_PORT=8001 uv run uvicorn src.data_discovery.main:app --port 8001
   ```

2. **MCP Integration Issues**
   ```bash
   # Check if fastapi_mcp is installed
   uv pip show fastapi-mcp
   
   # Install if missing
   uv add fastapi-mcp
   ```

3. **Empty Results from API**
   - No project artifacts cached yet
   - Check resource configuration in `src/data_discovery/resources/`

### Development
```bash
# Run with hot reload
uv run uvicorn src.data_discovery.main:app --reload

# Test legacy MCP server
uv run python src/data_discovery/server.py

# Check logs
tail -f ~/.cache/data-discovery/claude-server.log
```

## 🏗️ Architecture

### REST API-First Design
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation and serialization  
- **Single Service Layer** - Shared business logic between REST and MCP
- **Automatic MCP Integration** - REST endpoints wrapped as MCP tools

### Key Components
- `src/data_discovery/main.py` - FastAPI application entry point
- `src/data_discovery/core/service.py` - Core business logic
- `src/data_discovery/api/discovery/` - REST endpoint implementations
- `src/data_discovery/server.py` - Legacy MCP server (still supported)

### Dependencies
- `fastapi` + `uvicorn` - REST API server
- `fastapi-mcp` - Automatic MCP tool generation
- `mcp` - Model Context Protocol SDK
- `aiohttp` - Async HTTP for GitHub integration
- `pydantic` - Data validation and settings
- `loguru` - Advanced logging

---

## 🔄 Migration from MCP-First

This project has been refactored from MCP-first to **REST API-first** architecture:

### What Changed
- **Primary Interface**: REST API endpoints (was: MCP tools)
- **MCP Integration**: Auto-generated from REST endpoints (was: manually coded)
- **Single Codebase**: No duplication between REST and MCP (was: separate implementations)
- **Entry Point**: `src/data_discovery/main.py` (was: `src/data_discovery/server.py`)

### Backward Compatibility
- ✅ **Legacy MCP server** still works (`src/data_discovery/server.py`)
- ✅ **All MCP tools** available through REST API + fastapi_mcp
- ✅ **Same functionality** with improved architecture
- ✅ **Claude Desktop** integration maintained

### Benefits
- 🚀 **Better Performance** - Direct REST API access
- 🔧 **Easier Integration** - Standard HTTP endpoints
- 📖 **Auto Documentation** - OpenAPI/Swagger docs
- 🧪 **Better Testing** - Standard REST API testing tools
- 🔄 **Single Source of Truth** - No code duplication
