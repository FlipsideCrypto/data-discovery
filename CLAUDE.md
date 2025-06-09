# Custom dbt MCP Server Build Instructions

## Project Overview
Build a lightweight, custom Model Context Protocol (MCP) server that integrates with dbt projects to define custom tools for data discovery. The package `dbt-labs/dbt-mcp` will be used for Core CLI tools, but everything else will be custom built. This MCP server will read dbt JSON artifacts `catalog.json` and `manifest.json` to return model details, lineage, metadata, and more to a LLM client. In development, these files will be provided in the project directory. In practice, these files are accessible from the dbt project repositories where they are executed using Github Actions.  

## Requirements

### Dependencies
- Python 3.12+
- `dbt-mcp` package from dbt-labs/dbt-mcp
- MCP SDK for Python. Documentaion on developing MCP servers available in @MCP.md
- Local dbt project(s) on the machine for development

### Core Functionality
- Import and use `dbt-mcp` as the base for core tooling
- Enable ONLY dbt Core tools (disable all other tool categories) from `dbt-mcp`
- Build custom data discovery tools that parse and traverse the JSON artifacts
- Provide Claude Desktop-compatible MCP server configuration

## Technical Specifications

### Project Structure
Organize primitives in proper directories. Follow standard `src/` namespace convention.  
```
fsc-dbt-mcp/
├── src/
│   └── fsc_dbt_mcp/
│       ├── __init__.py
│       ├── server.py
│       ├── prompts/
│       ├── resources/
│       └── tools/
│           ├── __init__.py
│           └── discovery.py
```

### Key Components

#### Base Server Implementation (`server.py`)
- Import the dbt-mcp package
- Initialize MCP server with only Core CLI tools enabled
- Implement proper error handling and logging
- Ensure compatibility with Claude Desktop's MCP client
From dbt-mcp package, identify and ENABLE only:
- **Core Tools**: Basic dbt operations (run, test, compile, parse, etc.)

DISABLE these categories:
- Documentation tools
- Lineage/visualization tools  
- Advanced analytics tools
- Any non-essential tooling that requires dbt Cloud

#### Custom Tools (`src/fsc_dbt_mcp/tools`)
- Build custom tools for data discovery and integrate into the custom MCP server
- Integrate into a singular `server.py` runtime file, allowing for usage of core `dbt-mcp` CLI tools alongside custom tools in a single MCP Server

A non-final list of proposed tools is provided, inspired by current discovery tools built into `dbt-labs/dbt-mcp` and an open source project `mattijsdp/dbt-docs-mcp`.  

| Tool Name             | Description                                                     | **dbt-docs-mcp equivalent** |
| --------------------- | --------------------------------------------------------------- | --------------------------- |
| get_gold_models       | Gets all gold models                                            |                             |
| get_all_models        | Gets all models                                                 |                             |
| get_model_details     | Gets details for a specific model                               | `get_dbt_node_attributes`   |
| get_model_parents     | Gets parent nodes of a specific model                           | `get_dbt_predecessors`      |
| get_model_children    | Gets children modes of a specific model                         | `get_dbt_successors`        |
| search_by_object_name | Find nodes (models, sources, tests, etc.) by name               | `search_dbt_node_names`     |
| search_by_column_name | Locate nodes based on column names                              | `search_dbt_column_names`   |
| search_by_sql_code    | Search within the compiled SQL code of nodes                    | `search_dbt_sql_code`       |
| TBD if implementing   | Trace all upstream sources for a specific column in a model     | `get_column_ancestors`      |
| TBD if implementing   | Trace all downstream dependents of a specific column in a model | `get_column_descendants`    |


### Implementation Requirements

#### Core dbt Tools to Expose
The server should expose these essential dbt Core operations:
- `dbt ls` -  Lists resources in the dbt project, such as models and tests
- `dbt compile` - Compile models
- `dbt parse` - Parse project
- `dbt show` - Runs a query against the data warehouse returning a data sample

The server should **overwrite** and restrict tools that alter data
- `dbt run` - Execute models
- `dbt test` - Run tests

#### Configuration Features
- Support for multiple dbt projects
- Environment variable handling for dbt configurations
- Validation of dbt installation and project health

#### Error Handling
- Graceful handling of missing dbt installations
- Clear error messages for invalid dbt projects
- Proper logging for debugging
- Fallback behaviors when dbt operations fail

## Integration Requirements

### Claude Desktop Configuration
Maintain a `claude_config.example.json` that:
- Defines the MCP server endpoint
- Specifies the server startup command
- Includes any required environment variables
- Provides clear server identification
- Use best practices for starting the server, whether a `python` or `uvx` command

### Example Configuration Structure
```json
{
  "mcpServers": {
    "fsc-dbt-mcp": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "DBT_PROJECT_PATH": "/path/to/dbt/project"
      }
    }
  }
}
```

## Development Guidelines

**IMPORTANT**: For detailed MCP development guidance, security best practices, and implementation patterns, refer to [MCP.md](./MCP.md) which contains comprehensive documentation on the Model Context Protocol.

### Code Quality
- Use type hints throughout
- Implement comprehensive error handling
- Add logging for debugging and monitoring
- Follow Python best practices and PEP 8
- Include docstrings for all functions and classes

### Testing Considerations
- Validate against real dbt projects
- Test with different dbt project structures
- Ensure compatibility with various dbt versions
- Test Claude Desktop integration

### Security
- Validate all file paths to prevent directory traversal
- Sanitize inputs for dbt commands
- Implement proper permission checking
- Avoid exposing sensitive configuration data

## Deliverables

### 1. Complete MCP Server (`server.py`)
A fully functional MCP server that:
- Imports and configures dbt-mcp with Core tools only
- Handles local or remote dbt project integration
- Provides clean API for Claude Desktop
- Includes comprehensive error handling
- Returns a suite of tools for data discovery

### 2. Dependencies (`requirements.txt`)
Complete list of required packages with versions

### 3. Documentation (`README.md`)
- Installation instructions
- Configuration guide
- Claude Desktop setup steps
- Troubleshooting guide
- Usage examples

### 4. Claude Configuration (`claude_config.json`)
Ready-to-use configuration file for Claude Desktop integration

## Implementation Notes

### dbt-mcp Package Integration
- Study the `dbt-labs/dbt-mcp` package structure to understand tool categories
- Study `mattijsdp/dbt-docs-mcp` for one example of an open source data discovery server that utilizes JSON artifacts
- Identify the specific Core tools and their implementations
- Understand the package's configuration system
- Determine how to selectively enable/disable tool categories

### MCP Protocol Compliance
- Ensure full compliance with MCP specification (see [MCP.md](./MCP.md) for complete protocol documentation)
- Implement proper resource discovery
- Handle tool invocation correctly
- Provide appropriate metadata and descriptions

## Success Criteria

The completed MCP server should:
1. Successfully integrate with the dbt-mcp package
2. Expose only dbt Core functionality to Claude
3. Provide custom data discovery tools, resources and prompts
4. Integrate seamlessly with Claude Desktop
5. Provide robust error handling and logging
6. Be easily configurable for different environments

This implementation will provide a clean, focused interface for working with dbt Core functionality through Claude Desktop while maintaining the flexibility to expand functionality in the future.