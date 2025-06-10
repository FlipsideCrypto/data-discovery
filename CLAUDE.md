# FSC dbt MCP Server Development Guide

## Project Overview
Build a lightweight, custom Model Context Protocol (MCP) server that integrates with dbt projects to define custom tools for data discovery. This MCP server reads dbt JSON artifacts `catalog.json` and `manifest.json` to return model details, lineage, metadata, and more to a LLM client. 

**Current State**: ✅ **PRODUCTION READY** - Complete multi-project blockchain ecosystem with 26 FlipsideCrypto dbt projects, robust error handling, intelligent caching, and comprehensive discovery tools.

## ✅ COMPLETED PHASE 1: Local dbt Project Support

### Implemented Components

#### 1. Unified MCP Server (`src/fsc_dbt_mcp/server.py`)
- ✅ Single MCP server combining dbt CLI and discovery tools
- ✅ Comprehensive error handling and logging
- ✅ Environment variable configuration (`DBT_PROJECT_DIR`, `DBT_PATH`)
- ✅ Claude Desktop compatibility

#### 2. dbt CLI Tools (3 tools - `src/fsc_dbt_mcp/tools/dbt_cli.py`)
- ✅ **`dbt_list`** - List dbt resources with optional selectors ⚠️ *Single project only*
- ✅ **`dbt_compile`** - Compile dbt models to SQL ⚠️ *Single project only*
- ✅ **`dbt_show`** - Execute inline SQL queries with sample results ⚠️ *Single project only*
- ✅ Direct subprocess calls to dbt CLI with proper logging
- ✅ Support for `DBT_PATH` environment variable (pyenv compatibility)
- ⚠️ **Limitation**: Not yet updated for multi-project support (Phase 3 priority)

#### 3. Discovery Tools (3 tools - `src/fsc_dbt_mcp/tools/discovery/`)
- ✅ **`get_model_details`** - Comprehensive model metadata including:
  - Model description, schema, database, materialization
  - Column details with types, descriptions, and comments
  - Dependencies (refs and sources)  
  - Statistics from catalog
  - Raw and compiled SQL
  - Tags, meta properties, and constraints
  - **Multi-project support** with intelligent project detection
- ✅ **`get_description`** - Documentation block retrieval with:
  - Expert context from `__MCP__` blocks
  - Project-specific documentation
  - **Requires project_id** to prevent cross-contamination
- ✅ **`get_models`** - Model listing and filtering with:
  - Schema and medallion level filtering
  - Multi-project hierarchical results
  - Project-aware model discovery

#### 4. Prompt System (`src/fsc_dbt_mcp/prompts/`)
- ✅ **`get_prompt()`** function following dbt-labs pattern
- ✅ Markdown-based tool descriptions
- ✅ Rich, detailed help text for tools
- ✅ Selector guidance and dbt_show usage instructions

#### 5. Project Structure
```
fsc-dbt-mcp/
├── src/
│   └── fsc_dbt_mcp/
│       ├── __init__.py
│       ├── server.py                    ✅ Unified MCP server
│       ├── prompts/
│       │   ├── prompts.py              ✅ Prompt loader
│       │   ├── dbt_cli/
│       │   │   └── dbt_show.md         ✅ dbt_show tool description
│       │   └── shared/
│       │       └── selector.md         ✅ Selector parameter guidance
│       ├── resources/                   ✅ Documentation resources
│       └── tools/
│           ├── __init__.py
│           ├── discovery.py            ✅ Model discovery tools
│           └── dbt_cli.py              ✅ dbt CLI integration
```

#### 6. Configuration & Documentation
- ✅ **README.md** - Complete setup and usage guide
- ✅ **pyproject.toml** - Project configuration with minimal dependencies
- ✅ **claude_config.json** - Ready-to-use Claude Desktop configuration
- ✅ Environment variable documentation and troubleshooting

### Architecture Decision: Custom Implementation vs dbt-mcp
**Decision Made**: Instead of importing `dbt-mcp` package, we implemented custom dbt CLI tools using subprocess calls. This provides:
- Better control over command execution and logging
- Simplified dependencies (only `mcp` SDK required)
- More transparent error handling
- Easier customization for specific use cases

## ✅ PHASE 2A: Multi-Project Support (COMPLETED)

### Current State: **SHIPPED** ✅
Multi-project support has been successfully implemented and tested. All discovery tools now support project-aware operations with intelligent context handling.

### ✅ Implemented Components

#### 1. MCP Resources System (`src/fsc_dbt_mcp/resources/`)
- ✅ **ResourceRegistry** - Centralized resource management with DRY principles
- ✅ **Project Resource Definitions** - Bitcoin, Ethereum, and Kairos models
- ✅ **MCP Resource Integration** - Proper resource listing and reading
- ✅ **URI Patterns** - `dbt://project/{id}` and `dbt://projects` schema

#### 2. ProjectManager (`src/fsc_dbt_mcp/project_manager.py`)
- ✅ **Multi-project artifact loading** - Local and GitHub repository support
- ✅ **Array-based project_id parameter** - Support up to 5 projects (configurable)
- ✅ **Local caching system** - UTC timestamps in `target/{project_id}/` structure
- ✅ **GitHub artifact fetching** - Raw URLs with aiohttp integration
- ✅ **Smart project extraction** - Auto-detect project from `uniqueId` format
- ✅ **Deployment mode support** - Local, desktop, remote configurations

#### 3. Project-Aware Discovery Tools (All 3 tools updated)
- ✅ **get_model_details** - Multi-project search with intelligent project detection
- ✅ **get_description** - **Requires project_id** to prevent blockchain context mixing
- ✅ **get_models** - Cross-project model listing with hierarchical organization
- ✅ **Enhanced error handling** - All errors include available projects list
- ✅ **DRY refactoring** - Shared utilities in `discovery/utils.py`

#### 4. Configuration & Environment Support
- ✅ **DEPLOYMENT_MODE** - Local vs desktop vs remote cache directory handling
- ✅ **Required dependencies** - aiohttp now required for GitHub operations
- ✅ **Updated documentation** - README and prompt descriptions reflect multi-project capabilities

### ✅ Key Features Delivered

#### **Multi-Project Intelligence**
- **Smart project detection**: Automatically extracts project from `uniqueId` format
- **Cross-project search**: Search models across Bitcoin, Ethereum, and multi-chain projects
- **Context isolation**: `get_description` requires project specification to prevent blockchain context mixing
- **Hierarchical results**: Project → Schema → Models organization

#### **Enhanced Error Handling**
- **Available projects list**: All error messages include available projects for guidance
- **Null/undefined handling**: Graceful handling of missing `project_id` parameters
- **Validation with context**: Rich error messages with troubleshooting guidance

#### **Performance & Caching**
- **Local artifact caching**: UTC timestamps with configurable TTL
- **GitHub integration**: Async artifact fetching with error resilience
- **Deployment awareness**: Automatic cache directory selection based on environment

#### **Developer Experience**
- **DRY utilities**: Shared error handling and validation functions
- **Type safety**: Consistent `List[TextContent]` return types
- **Comprehensive logging**: Debug information for troubleshooting

### ✅ Architecture Achievements
- **Backward compatibility**: All existing functionality preserved
- **Resource-driven discovery**: MCP Resources provide project catalog
- **Modular design**: Clean separation between resources, project management, and tools
- **Scalable foundation**: Ready for additional blockchain projects and tool expansion
- **Flexible configuration**: Support both local and remote project definitions
- **DRY implementation**: Shared utilities eliminate code duplication

### ✅ Ready for Production

The multi-project system is **complete and battle-tested**. Key capabilities:

#### **Project Discovery**
- MCP Resources provide discoverable project catalog at `dbt://projects`
- Individual project details available at `dbt://project/{id}`
- Support for local projects (bitcoin-models, kairos-models) and GitHub projects (ethereum-models)

#### **Tool Integration**
- All discovery tools (`get_model_details`, `get_description`, `get_models`) support multi-project operations
- Intelligent parameter handling: `project_id` can be string, array, or omitted
- Context isolation prevents blockchain-specific documentation mixing

#### **Deployment Ready**
- `DEPLOYMENT_MODE` environment variable handles Claude Desktop vs local development
- Comprehensive error handling with guidance for users
- Performance optimized with local caching and async GitHub operations

Resource returns comprehensive project metadata including:
- Project ID, name, description, blockchain type
- Artifact locations (local paths or GitHub URLs)
- Schema structure and feature documentation
- Last updated timestamps and metadata

### Current State: **PLANNING** 📋
Phase 2A multi-project foundation enables advanced discovery capabilities across blockchain ecosystems.

#### New Tool: `generate_expert_context`
- **Purpose**: Generate specialized blockchain expert context from project documentation
- **Status**: Ready for implementation
- **Foundation**: Leverages multi-project `get_description` with `__MCP__` blocks
- **Use case**: Create domain-specific expert personas for Bitcoin, Ethereum, DeFi analysis

#### **PRIORITY: Multi-Project dbt CLI Tools** 🚨
**Current Issue**: dbt CLI tools (`dbt_list`, `dbt_compile`, `dbt_show`) only work with single project via `DBT_PROJECT_DIR`

**Required Updates:**
- Add `project_id` parameter to all dbt CLI tools
- Update dbt CLI handlers to switch working directory based on project
- Modify subprocess calls to operate in correct project context
- Ensure compatibility with both local and GitHub projects (GitHub projects need local clone/checkout)
- Update tool schemas and documentation

**Impact**: Currently dbt CLI tools are not project-aware and will fail or return incorrect results when used in multi-project context.

#### Additional Discovery Tools (from original roadmap)
| Tool Name             | Status | Description                                                     |
| --------------------- | ------ | --------------------------------------------------------------- |
| get_gold_models       | ✅ DONE | Gets all gold models                                            |
| get_all_models        | ✅ DONE | Gets all models                                                 |
| get_model_parents     | 📋 TODO | Gets parent nodes of a specific model                           |
| get_model_children    | 📋 TODO | Gets children modes of a specific model                         |
| search_by_object_name | 📋 TODO | Find nodes (models, sources, tests, etc.) by name               |
| search_by_column_name | 📋 TODO | Locate nodes based on column names                              |
| search_by_sql_code    | 📋 TODO | Search within the compiled SQL code of nodes                    |

### Phase 4: Resources and Contextual Information

#### Resource: Supported Blockchains
- **Purpose**: Reference of supported blockchain networks
- **Implementation**: TBD - could be JSON file, markdown resource, or dynamic tool
- **Integration**: Likely consumed by discovery tools and expert context generation

#### Resource/Prompt: Flipside Model Structure
- **Purpose**: Context for Flipside's medallion standard architecture
- **Content**:
  - Definition of schema layers (bronze, silver, gold)
  - Gold schema breakdown (defi, nft, core, etc.)
  - Model naming conventions
  - Data governance patterns
- **Implementation**: Markdown resources + prompts

## Technical Implementation Notes

### Current Dependencies
```toml
dependencies = [
    "mcp",              # MCP SDK
]
```

### Future Dependencies (for GitHub support)
```toml
dependencies = [
    "mcp",              # MCP SDK  
    "requests",         # HTTP client for GitHub API
    "aiohttp",          # Async HTTP for better performance
    "python-dotenv",    # Environment configuration
]
```

### Security Considerations for Remote Access
- GitHub token secure storage and rotation
- Repository access validation
- Strict input validation against JSON Schemas for all tool and API inputs
- Artifact content validation (prevent malicious JSON)
- Rate limiting and respectful API usage
- Audit logging for artifact access

### Performance Requirements
- **Target**: <2 second response time for cached artifacts
- **Target**: <5 second response time for fresh GitHub API calls  
- **Caching**: Implement TTL-based caching with configurable refresh
- **Concurrency**: Support parallel artifact fetching for multiple repositories

## Success Criteria

### Phase 2 (Remote GitHub Support)
1. Successfully fetch and parse dbt artifacts from GitHub repositories
2. Maintain sub-5-second response times for discovery tools
3. Robust error handling for network issues and missing artifacts
4. Support for multiple dbt projects across different repositories
5. Secure and efficient GitHub API integration

### Future Phases
1. Complete set of discovery tools matching `dbt-docs-mcp` functionality
2. Rich contextual resources for blockchain and Flipside-specific information
3. Expert context generation for domain-specific assistance
4. Scalable architecture supporting multiple organizations and project structures

## Development Priorities

**IMMEDIATE (Phase 2A)**:
1. 🔥 **MCP resource for project discovery**
2. 🔥 **Multi-project configuration system**
3. 🔥 **Project-aware tool enhancement** 
4. 🔥 **ProjectManager implementation**
5. 🔥 **Backward compatibility validation**

**NEXT (Phase 2B)**:
1. 🔥 **GitHub API integration** for artifact fetching
2. 🔥 **Caching mechanism** for performance
3. 🔥 **Authentication and security** implementation

**SHORT TERM**:
1. Additional discovery tools (get_all_models, search functions)
2. generate_expert_context tool definition and implementation
3. Supported blockchains resource

**MEDIUM TERM**:
1. Flipside model structure resources
2. Advanced lineage and dependency tools
3. Performance optimizations and caching improvements

This roadmap provides a clear path from the current single-project implementation to a comprehensive, multi-project dbt discovery platform optimized for blockchain data analysis workflows.