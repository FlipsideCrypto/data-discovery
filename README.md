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
   
   # Create and activate a virtual environment with uv
   uv venv
   source .venv/bin/activate
   
   # Install dependencies
   uv sync
   
   # Configure environment (optional)
   cp .env.example .env
   # Edit .env as needed
   ```

2. **Start the API server**:
   ```bash
   # Using the console script (recommended)
   data-discovery
   
   # Development server with hot reload
   uv run uvicorn src.data_discovery.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using the main module directly
   uv run python src/data_discovery/main.py
   ```

3. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # List resources
   curl http://localhost:8000/api/v1/resources
   
   # API documentation
   open http://localhost:8000/docs
   ```

### 🤖 MCP Integration

**Note**: The integrated fastapi_mcp currently only supports SSE (Server-Sent Events) transport, while Claude **Desktop** requires stdio transport.

1. **Cursor Integration**:
   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "url": "http://localhost:8000/mcp"
       }
     }
   }
   ```
*Start the API server per the quickstart guide.*  
*If hosted remotely, replace `localhost:8000` with the host.*  

2. **Claude Desktop Deployment Configuration** (`claude_desktop_config.json`):
*NOT YET SUPPORTED*  
   ```json
   {
     "mcpServers": {
       "data-discovery": {
         "command": "/absolute/path/to/.local/bin/uv",
         "args": [
           "--directory",
           "/absolute/path/to/data-discovery",
           "run",
           "data-discovery"
         ],
         "env": {
           "DEPLOYMENT_MODE": "desktop"
         }
       }
     }
   }
   ```

3. **MCP Transport Limitations**:
   - **fastapi_mcp**: SSE transport only (web browsers, API clients)
   - **Claude Desktop**: Requires stdio transport
   - **Solution**: Use the main app with MCP integration for Claude Desktop
   - **Future**: stdio support may be added to fastapi_mcp

4. **Restart MCP Client** and explore:
   - "Show me all Bitcoin core models"
   - "Get details on ethereum transaction models"
   - "List available blockchain projects"

## 📊 API Endpoints

### Core Discovery Endpoints
- **`GET /api/v1/resources`** - List available dbt projects with filtering
- **`GET /api/v1/models`** - Search models by schema, level, or resource (defaults to level=gold)
- **`GET /api/v1/models/{unique_id}`** - Get detailed model information
- **`GET /api/v1/descriptions/{doc_name}`** - Retrieve documentation blocks

### Additional Endpoints
- **`GET /health`** - Health check and status
- **`GET /docs`** - Interactive API documentation
- **`GET /openapi.json`** - OpenAPI specification
- **`/mcp`** - MCP protocol endpoint via SSE (when fastapi_mcp available)

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
- **`api`** (default): REST API server mode with optional MCP via SSE
- **`desktop`**: Claude Desktop MCP integration mode (stdio transport)
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
   # Check if fastapi_mcp is installed (for SSE transport)
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

# Test the console script
data-discovery

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
- `src/data_discovery/main.py` - FastAPI application entry point with MCP integration
- `src/data_discovery/core/service.py` - Core business logic
- `src/data_discovery/api/discovery/` - REST endpoint implementations
- `src/data_discovery/mcp/` - MCP integration module

### Dependencies
- `fastapi` + `uvicorn` - REST API server
- `fastapi-mcp` - Automatic MCP tool generation
- `mcp` - Model Context Protocol SDK
- `aiohttp` - Async HTTP for GitHub integration
- `pydantic` - Data validation and settings
- `loguru` - Advanced logging

---

## 📋 Recent Changes

### API Filtering Updates
- **Default Level**: `/models` endpoint now defaults to `level=gold` for higher quality results
- **Utility Model Filtering**: Models from `fsc_utils` package are excluded from gold-level results
- **Quality Focus**: Gold level now returns curated, production-ready models only

### MCP Transport Limitations
- **fastapi_mcp**: Currently supports SSE transport only
- **Claude Desktop**: Requires stdio transport (incompatible with fastapi_mcp)
- **Workaround**: Use standalone MCP server (`src/data_discovery/server.py`) for Claude Desktop
- **Future**: stdio transport support may be added to fastapi_mcp
