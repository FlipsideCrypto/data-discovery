# FSC dbt MCP Server Development Guide

## Project Overview
Build a lightweight, custom Model Context Protocol (MCP) server that integrates with dbt projects to define custom tools for data discovery. This MCP server reads dbt JSON artifacts `catalog.json` and `manifest.json` to return model details, lineage, metadata, and more to a LLM client. 

**Current State**: Core functionality completed for local dbt projects. Next priority is supporting remote GitHub-hosted dbt projects.

## ✅ COMPLETED PHASE 1: Local dbt Project Support

### Implemented Components

#### 1. Unified MCP Server (`src/fsc_dbt_mcp/server.py`)
- ✅ Single MCP server combining dbt CLI and discovery tools
- ✅ Comprehensive error handling and logging
- ✅ Environment variable configuration (`DBT_PROJECT_DIR`, `DBT_PATH`)
- ✅ Claude Desktop compatibility

#### 2. dbt CLI Tools (3 tools - `src/fsc_dbt_mcp/tools/dbt_cli.py`)
- ✅ **`dbt_list`** - List dbt resources with optional selectors
- ✅ **`dbt_compile`** - Compile dbt models to SQL
- ✅ **`dbt_show`** - Execute inline SQL queries with sample results
- ✅ Direct subprocess calls to dbt CLI with proper logging
- ✅ Support for `DBT_PATH` environment variable (pyenv compatibility)

#### 3. Discovery Tools (1 tool - `src/fsc_dbt_mcp/tools/discovery.py`)
- ✅ **`get_model_details`** - Comprehensive model metadata including:
  - Model description, schema, database, materialization
  - Column details with types, descriptions, and comments
  - Dependencies (refs and sources)  
  - Statistics from catalog
  - Raw and compiled SQL
  - Tags, meta properties, and constraints

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

## 🚀 PHASE 2: Remote GitHub dbt Projects (PRIORITY)

### Current Challenge
All testing has been done on local dbt projects. Our dbt projects live on GitHub, so the required JSON artifacts (`manifest.json`, `catalog.json`) that contain the data for the discovery tools live across different GitHub repositories.

### Requirements
- **QUICK and EFFICIENT** access to JSON artifacts from GitHub repositories
- Support for multiple GitHub repositories containing different dbt projects
- Caching strategy to avoid repeated API calls
- Authentication handling for private repositories
- Fallback mechanisms when artifacts are unavailable

### Implementation Considerations

#### Potential Approaches
1. **GitHub API Integration**
   - Direct API calls to fetch `target/manifest.json` and `target/catalog.json`
   - OAuth token authentication
   - Rate limiting and caching

2. **GitHub Actions Artifacts**
   - Access artifacts uploaded by GitHub Actions workflows
   - May require different API endpoints and authentication

3. **Configuration-Based Repository Mapping**
   - Environment variables or config file specifying repository URLs
   - Support for multiple projects/repositories

#### Environment Variables for Remote Support
```bash
# Required for remote GitHub support
GITHUB_TOKEN=ghp_xxx                    # GitHub API token
GITHUB_REPOS=org/repo1,org/repo2        # Comma-separated repository list
GITHUB_ARTIFACTS_BRANCH=main            # Branch containing artifacts (default: main)

# Optional caching
ARTIFACTS_CACHE_TTL=3600                # Cache TTL in seconds
ARTIFACTS_CACHE_DIR=/tmp/fsc-dbt-cache  # Local cache directory
```

## 🔮 FUTURE ROADMAP

### Phase 3: Enhanced Discovery Tools

#### New Tool: `generate_expert_context`
- **Purpose**: Return prompt context for "blockchain experts"
- **Status**: Concept phase - definition needed
- **Implementation**: TBD

#### Additional Discovery Tools (from original roadmap)
| Tool Name             | Status | Description                                                     |
| --------------------- | ------ | --------------------------------------------------------------- |
| get_gold_models       | 📋 TODO | Gets all gold models                                            |
| get_all_models        | 📋 TODO | Gets all models                                                 |
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

**IMMEDIATE (Phase 2)**:
1. 🔥 **GitHub API integration** for artifact fetching
2. 🔥 **Caching mechanism** for performance
3. 🔥 **Multi-repository configuration** support
4. 🔥 **Authentication and security** implementation

**SHORT TERM**:
1. Additional discovery tools (get_all_models, search functions)
2. generate_expert_context tool definition and implementation
3. Supported blockchains resource

**MEDIUM TERM**:
1. Flipside model structure resources
2. Advanced lineage and dependency tools
3. Performance optimizations and caching improvements

This roadmap provides a clear path from the current local-only implementation to a comprehensive, GitHub-integrated dbt discovery platform optimized for blockchain data analysis workflows.