# FSC dbt MCP Server Development Guide

## Project Overview
Build a lightweight, custom Model Context Protocol (MCP) server that integrates with dbt projects to define custom tools for data discovery. This MCP server reads dbt JSON artifacts `catalog.json` and `manifest.json` to return model details, lineage, metadata, and more to a LLM client. 

**Current State**: Core functionality completed for local dbt projects. Next priority is multi-project support followed by remote GitHub-hosted dbt projects.

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

## 🚀 PHASE 2A: Multi-Project Support (PRIORITY)

### Current Challenge
The existing server supports only a single dbt project via `DBT_PROJECT_DIR`. We need to scale to support multiple dbt projects (starting with 3, ultimately unlimited) while maintaining MCP best practices and backward compatibility.

### Requirements
- **Resource-first discovery**: MCP resource to list available projects
- **Project-aware tools**: Existing tools enhanced with optional `project_id` parameter
- **Backward compatibility**: Single-project configurations continue to work
- **Flexible configuration**: Support both local and remote project definitions
- **Scalable architecture**: Easy extension from 3 to N projects

### Implementation Plan

#### Step 1: Core MCP Resource - Available Projects
Add discoverable resource listing all configured dbt projects:

```python
@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="dbt://projects",
            name="Available dbt Projects",
            description="List of all configured dbt projects with metadata",
            mimeType="application/json"
        )
    ]
```

```python
@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    if str(uri) == "dbt://projects":
        projects = get_available_projects()
        return json.dumps({
            "projects": [
                {
                    "id": "bitcoin-models",
                    "name": "Bitcoin Models",
                    "description": "dbt models for Bitcoin blockchain data",
                    "location": "/Users/jackforgash/gh/fs/bitcoin-models",
                    "aliases": ["bitcoin", "btc"]
                },
                {
                    "id": "ethereum-models", 
                    "name": "Ethereum Models",
                    "description": "dbt models for Ethereum blockchain data",
                    "location": "flipside-crypto/ethereum-models",
                    "aliases": ["ethereum", "eth", "mainnet", "eth mainnet"]
                },
                {
                    "id": "kairos-models",
                    "name": "Kairos Models", 
                    "description": "Flipside developed stats and metrics models across all blockchains",
                    "location": "/Users/jackforgash/gh/fs/kairos-models",
                    "aliases": ["kairos", "metrics"]
                }
            ]
        }, indent=2)
```

Resource returns project metadata including:
- Project ID, name, description, aliases
- Local path or GitHub repository (as just "location" right now but may need better disambiguation)
- Other metadata possible

#### Step 2: Enhanced Configuration Management
Expand `ServerConfig` to handle multiple projects:

```python
class ServerConfig:
    def __init__(self):
        self.projects = self._load_project_configs()  # Dict[str, ProjectConfig]
        # ... existing config ...
    
    def _load_project_configs(self) -> Dict[str, ProjectConfig]:
        # Support primary project (backward compatibility)
        # Load additional projects from DBT_PROJECTS_CONFIG JSON
```

#### Step 3: Project-Aware Tool Enhancement
Modify existing tools to accept optional `project_id` parameter:

```python
inputSchema={
    "properties": {
        "model_name": {"type": "string", "description": "Name of the dbt model"},
        "project_id": {
            "type": "string", 
            "description": "ID of dbt project (see 'dbt://projects' resource). If not specified, searches all projects.",
            "enum": ["bitcoin-models", "ethereum-models", "core-models", "all"]
        }
    },
    "required": ["model_name"]
}
```

#### Step 4: Project Resolution Logic
Add `ProjectManager` class for artifact resolution:

```python
class ProjectManager:
    async def get_project_artifacts(self, project_id: str) -> Tuple[dict, dict]:
        """Get manifest and catalog for specific project."""
    
    async def find_model_in_projects(self, model_name: str, project_id: Optional[str] = None):
        """Find model across configured projects."""
```
Remote projects (where a github repository is hosted) should resolve the project path to the location of the 2 json artifacts. All projects host a branch `/docs` with the latest dbt documentation and thus an up to date catalog and manifest.  
 - Example URL: `https://raw.githubusercontent.com/FlipsideCrypto/bitcoin-models/refs/heads/docs/docs/catalog.json`  
If a project is defined in resources to be a github repository, it can be assumed the json files are on `/docs` IN the directory `/docs` (note - NOT TARGET)

May need to add a project routing or selection step / tool to assess the project(s) involved in the query. NOTE - projectS as a user may be asking for comparative analytics.  


#### Step 5: Migration Path
- **Phase 1**: Add resource support, updating existing tools
- **Phase 2**: Add optional `project_id` parameter
- **Phase 3**: Enhanced project discovery and search capabilities with resource utilization
- **Phase 4**: Optimization and caching for multi-project scenarios (TBD on caching)

### Success Criteria for 2A
1. MCP resource successfully lists 3 configured projects
2. All existing tools work without modification (backward compatibility)
3. Tools accept optional `project_id` and search across projects when unspecified
4. LLM can discover available projects via resource before tool usage
5. Configuration supports both local paths and GitHub repository definitions

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