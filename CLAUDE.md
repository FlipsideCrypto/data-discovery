# Custom dbt MCP Server Build Instructions

## Project Overview
Build a lightweight, custom Model Context Protocol (MCP) server that integrates with local dbt projects using the `dbt-mcp` package from dbt-labs. This server will expose ONLY the dbt Core tools and will be configured for use with Claude Desktop.

## Requirements

### Dependencies
- Python 3.8+
- `dbt-mcp` package from dbt-labs/dbt-mcp
- MCP SDK for Python
- Local dbt project(s) on the machine

### Core Functionality
- Import and use `dbt-mcp` as the base
- Enable ONLY dbt Core tools (disable all other tool categories)
- Configure for local dbt project integration
- Provide Claude Desktop-compatible MCP server

## Technical Specifications

### Project Structure
```
custom-dbt-mcp/
├── server.py              # Main MCP server implementation
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── README.md            # Setup and usage instructions
└── claude_config.json   # Claude Desktop configuration
```

### Key Components

#### 1. Server Implementation (`server.py`)
- Import the dbt-mcp package
- Initialize MCP server with only Core tools enabled
- Handle dbt project discovery and configuration
- Implement proper error handling and logging
- Ensure compatibility with Claude Desktop's MCP client

#### 2. Configuration Management (`config.py`)
- Auto-discover local dbt projects
- Allow manual dbt project path specification
- Validate dbt project structure and profiles
- Handle dbt profiles.yml integration
- Configure tool filtering (Core only)

#### 3. Tool Categories to Handle
From dbt-mcp package, identify and ENABLE only:
- **Core Tools**: Basic dbt operations (run, test, compile, parse, etc.)

DISABLE these categories:
- Documentation tools
- Lineage/visualization tools  
- Advanced analytics tools
- Any non-essential tooling

### Implementation Requirements

#### Core dbt Tools to Expose
The server should expose these essential dbt Core operations:
- `dbt run` - Execute models
- `dbt test` - Run tests
- `dbt compile` - Compile models
- `dbt parse` - Parse project
- `dbt clean` - Clean artifacts
- `dbt deps` - Install dependencies
- Model/test file reading and analysis
- Basic project structure exploration

#### Configuration Features
- Automatic dbt project detection in common locations
- Support for multiple dbt projects
- dbt profiles.yml integration
- Environment variable handling for dbt configurations
- Validation of dbt installation and project health

#### Error Handling
- Graceful handling of missing dbt installations
- Clear error messages for invalid dbt projects
- Proper logging for debugging
- Fallback behaviors when dbt operations fail

## Integration Requirements

### Claude Desktop Configuration
Generate a `claude_config.json` that:
- Defines the MCP server endpoint
- Specifies the server startup command
- Includes any required environment variables
- Provides clear server identification

### Example Configuration Structure
```json
{
  "mcpServers": {
    "dbt-core": {
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
- Handles local dbt project integration
- Provides clean API for Claude Desktop
- Includes comprehensive error handling

### 2. Configuration System (`config.py`)
- Auto-discovery of dbt projects
- Configuration validation
- Environment setup helpers
- Tool filtering implementation

### 3. Dependencies (`requirements.txt`)
Complete list of required packages with versions

### 4. Documentation (`README.md`)
- Installation instructions
- Configuration guide
- Claude Desktop setup steps
- Troubleshooting guide
- Usage examples

### 5. Claude Configuration (`claude_config.json`)
Ready-to-use configuration file for Claude Desktop integration

## Implementation Notes

### dbt-mcp Package Integration
- Study the dbt-mcp package structure to understand tool categories
- Identify the specific Core tools and their implementations
- Understand the package's configuration system
- Determine how to selectively enable/disable tool categories

### Local dbt Project Handling
- Implement robust dbt project detection
- Handle various dbt project structures (single project, multi-project setups)
- Integrate with existing dbt profiles and configurations
- Respect dbt's standard directory structures and conventions

### MCP Protocol Compliance
- Ensure full compliance with MCP specification
- Implement proper resource discovery
- Handle tool invocation correctly
- Provide appropriate metadata and descriptions

## Success Criteria

The completed MCP server should:
1. Successfully integrate with the dbt-mcp package
2. Expose only dbt Core functionality to Claude
3. Auto-discover and work with local dbt projects
4. Integrate seamlessly with Claude Desktop
5. Provide robust error handling and logging
6. Be easily configurable for different environments

## Getting Started

1. Research the dbt-mcp package structure and API
2. Set up the basic MCP server framework
3. Implement dbt project discovery
4. Configure tool filtering for Core-only functionality
5. Test with a local dbt project
6. Create Claude Desktop configuration
7. Document setup and usage procedures

This implementation will provide a clean, focused interface for working with dbt Core functionality through Claude Desktop while maintaining the flexibility to expand functionality in the future.