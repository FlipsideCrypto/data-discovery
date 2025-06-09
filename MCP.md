# Model Context Protocol (MCP) Developer Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Protocol Fundamentals](#protocol-fundamentals)
4. [MCP Primitives](#mcp-primitives)
5. [Developing MCP Servers in Python](#developing-mcp-servers-in-python)
6. [Best Practices](#best-practices)
7. [Security Considerations](#security-considerations)
8. [Transport Mechanisms](#transport-mechanisms)

## Overview

The Model Context Protocol (MCP) is an open standard that enables seamless integration between Large Language Model (LLM) applications and external data sources and tools. MCP allows AI assistants to securely access and interact with local and remote resources while maintaining user control and consent. This developer guide is a summarization of the repository `modelcontextprotocol/modelcontextprotocol`. The repository should be referred to, as needed, for the most up to date documentation.  

### Key Benefits
- **Universal Connectivity**: Connect AI applications to any data source or tool through a standardized interface
- **Security-First Design**: Built-in consent and authorization mechanisms
- **Composable Architecture**: Mix and match different MCP servers for custom functionality
- **Developer-Friendly**: Simple JSON-RPC protocol with comprehensive SDKs

### Use Cases
- Access live data from databases, APIs, and files
- Execute tools and functions with user approval
- Provide domain-specific prompts and workflows
- Enable collaborative AI-human workflows

## Core Architecture

MCP follows a **Client-Host-Server** architecture pattern:

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   MCP Client    │    │   AI Host    │    │   MCP Server    │
│  (Claude, etc.) │◄──►│ (Claude App) │◄──►│ (Your Server)   │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

### Components

#### MCP Client
The LLM or AI assistant that needs access to external resources and tools. Examples include Claude, GPT-4, or custom AI applications.

#### Host Application  
The application that embeds and manages the AI client. This could be Claude Desktop, a custom chat interface, or an AI-powered workflow tool. The host handles user interactions and consent flows.

#### MCP Server
Your custom server that provides access to specific resources, tools, or data sources. This is what you'll build to extend AI capabilities.

### Design Principles

1. **Servers are Stateless**: Each server can handle multiple clients independently
2. **Explicit Consent**: All tool executions require user approval through the host
3. **Capability-Based**: Servers declare what they can do; clients choose what to use
4. **Extensible**: New capabilities can be added without breaking existing implementations

## Protocol Fundamentals

MCP uses **JSON-RPC 2.0** as its underlying communication protocol, providing a standardized way for clients and servers to exchange messages.

### Message Types

#### Requests
Messages that expect a response:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "methodName",
  "params": { ... }
}
```

#### Responses
Replies to requests:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "result": { ... }
}
```

#### Notifications  
One-way messages that don't expect responses:
```json
{
  "jsonrpc": "2.0",
  "method": "notificationMethod",
  "params": { ... }
}
```

### Connection Lifecycle

#### 1. Initialization
```python
# Server announces capabilities
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "resources": {},
      "tools": {},
      "prompts": {}
    },
    "serverInfo": {
      "name": "my-server",
      "version": "1.0.0"
    }
  }
}
```

#### 2. Operation
Normal request/response cycles for accessing resources, calling tools, etc.

#### 3. Shutdown
Graceful termination using standard JSON-RPC lifecycle methods.

## MCP Primitives

MCP defines five core primitives that servers can implement:

### 1. Resources

Resources represent **file-like data** that can be read by clients to provide context to LLMs.

#### Key Characteristics
- **Read-only**: Resources are primarily for providing context, not modification
- **Discoverable**: Clients can list available resources
- **Typed**: Resources have MIME types (text/plain, application/json, etc.)
- **URI-based**: Each resource has a unique URI

#### Implementation Example
```python
@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="file://config.json",
            name="Configuration",
            description="Server configuration file",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    if str(uri) == "file://config.json":
        return json.dumps({"setting": "value"})
    raise ValueError(f"Unknown resource: {uri}")
```

#### Use Cases
- Configuration files
- Documentation and help text
- Data exports and reports
- Reference materials

### 2. Tools

Tools are **functions** that LLMs can invoke to perform actions or retrieve information.

#### Key Characteristics
- **Executable**: Tools perform actions when called
- **Parameterized**: Tools accept structured input parameters
- **User-Approved**: All tool executions require explicit user consent
- **Described**: Tools have detailed descriptions for LLM understanding

#### Implementation Example
```python
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_weather":
        location = arguments["location"]
        # Fetch weather data
        weather_data = get_weather_api(location)
        return [types.TextContent(type="text", text=f"Weather in {location}: {weather_data}")]
```

#### Use Cases
- API integrations
- Database queries
- File operations
- External service interactions

### 3. Prompts

Prompts are **templates** for messages or workflows that clients can use.

#### Key Characteristics
- **Templated**: Support dynamic arguments
- **Contextual**: Can include resources and dynamic content
- **Reusable**: Standardized workflows for common tasks
- **Discoverable**: Clients can list available prompts

#### Implementation Example
```python
@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="analyze_data",
            description="Analyze dataset with custom parameters",
            arguments=[
                types.PromptArgument(
                    name="dataset",
                    description="Dataset to analyze",
                    required=True
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    if name == "analyze_data":
        dataset = arguments["dataset"]
        return types.GetPromptResult(
            description=f"Analysis prompt for {dataset}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text", 
                        text=f"Please analyze the dataset: {dataset}"
                    )
                )
            ]
        )
```

#### Use Cases
- Standardized analysis workflows
- Domain-specific instructions
- Multi-step procedures
- Template-based content generation

### 4. Sampling

Sampling allows **servers to request LLM completions** from clients.

#### Key Characteristics
- **Server-Initiated**: Servers can request LLM interactions
- **Flexible**: Support various sampling parameters
- **Contextual**: Can include resources and conversation history

#### Implementation Example
```python
# Request LLM completion from client
async def analyze_with_llm(data: str) -> str:
    result = await server.request_sampling(
        messages=[
            types.SamplingMessage(
                role="user",
                content=types.TextContent(type="text", text=f"Analyze this data: {data}")
            )
        ],
        max_tokens=1000
    )
    return result.content
```

### 5. Roots

Roots define **filesystem boundaries** that clients can access.

#### Key Characteristics
- **Security Boundaries**: Limit filesystem access scope
- **Client-Managed**: Clients control which roots are available
- **Discoverable**: Servers can query available roots

## Developing MCP Servers in Python

### Setup and Dependencies

Install the MCP Python SDK:
```bash
pip install mcp
```

### Basic Server Structure

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Initialize server
server = Server("my-server")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="memory://example",
            name="Example Resource",
            description="An example resource",
            mimeType="text/plain"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    if uri == "memory://example":
        return "This is example content"
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="echo",
            description="Echo back the input",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo"
                    }
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a tool"""
    if name == "echo":
        message = arguments.get("message", "")
        return [types.TextContent(type="text", text=f"Echo: {message}")]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling Patterns

```python
from mcp.types import McpError, ErrorCode

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "risky_operation":
            # Perform operation that might fail
            result = perform_risky_operation(arguments)
            return [types.TextContent(type="text", text=result)]
        else:
            raise McpError(
                ErrorCode.METHOD_NOT_FOUND,
                f"Unknown tool: {name}"
            )
    except ValueError as e:
        raise McpError(
            ErrorCode.INVALID_PARAMS,
            f"Invalid parameters: {str(e)}"
        )
    except Exception as e:
        raise McpError(
            ErrorCode.INTERNAL_ERROR,
            f"Internal error: {str(e)}"
        )
```

### Configuration Management

```python
import os
from pathlib import Path
from typing import Optional

class ServerConfig:
    def __init__(self):
        self.base_path = Path(os.getenv("SERVER_BASE_PATH", "."))
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    def validate(self):
        """Validate configuration"""
        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {self.base_path}")
        
        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {self.base_path}")

# Use configuration
config = ServerConfig()
config.validate()
```

## Best Practices

### 1. Server Design

#### Stateless Design
```python
# Good: Stateless operations
@server.call_tool()
async def get_file_info(name: str, arguments: dict) -> list[types.TextContent]:
    file_path = arguments["path"]
    # Get info directly from filesystem
    stat = os.stat(file_path)
    return [types.TextContent(type="text", text=f"Size: {stat.st_size}")]

# Avoid: Storing state between calls
class StatefulServer:
    def __init__(self):
        self.cache = {}  # Avoid this pattern
```

#### Clear Resource Naming
```python
# Good: Descriptive URIs
types.Resource(
    uri="file:///home/user/documents/config.json",
    name="Application Configuration",
    description="Main configuration file containing server settings"
)

# Avoid: Ambiguous URIs
types.Resource(
    uri="item1",
    name="File",
    description="A file"
)
```

### 2. Error Handling

#### Comprehensive Error Responses
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        # Tool implementation
        return perform_tool_operation(name, arguments)
    except FileNotFoundError:
        raise McpError(ErrorCode.INVALID_PARAMS, "File not found")
    except PermissionError:
        raise McpError(ErrorCode.INVALID_PARAMS, "Permission denied")
    except Exception as e:
        # Log the full error internally
        logger.error(f"Unexpected error in {name}: {e}")
        # Return user-friendly error
        raise McpError(ErrorCode.INTERNAL_ERROR, "Operation failed")
```

### 3. Input Validation

#### Schema Validation
```python
def validate_file_path(path: str) -> str:
    """Validate and normalize file path"""
    if not path:
        raise ValueError("Path cannot be empty")
    
    # Normalize path
    normalized = os.path.normpath(path)
    
    # Prevent directory traversal
    if ".." in normalized:
        raise ValueError("Path traversal not allowed")
    
    return normalized

@server.call_tool()
async def read_file(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        file_path = validate_file_path(arguments["path"])
        # Proceed with safe path
        content = read_file_safely(file_path)
        return [types.TextContent(type="text", text=content)]
    except ValueError as e:
        raise McpError(ErrorCode.INVALID_PARAMS, str(e))
```

### 4. Resource Management

#### Efficient Resource Handling
```python
@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    # Parse URI to determine resource type
    if uri.startswith("file://"):
        file_path = uri[7:]  # Remove file:// prefix
        
        # Check file size before reading
        stat = os.stat(file_path)
        if stat.st_size > MAX_FILE_SIZE:
            raise McpError(
                ErrorCode.INVALID_PARAMS, 
                f"File too large: {stat.st_size} bytes"
            )
        
        # Read file efficiently
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    raise McpError(ErrorCode.INVALID_PARAMS, f"Unknown resource: {uri}")
```

### 5. Documentation

#### Comprehensive Tool Descriptions
```python
types.Tool(
    name="search_database",
    description="Search the customer database using flexible criteria. "
               "Returns customer records matching the search parameters. "
               "Supports searching by name, email, company, or ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string (searches name, email, company)"
            },
            "customer_id": {
                "type": "string", 
                "description": "Exact customer ID to find"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 10, max: 100)",
                "minimum": 1,
                "maximum": 100
            }
        },
        "anyOf": [
            {"required": ["query"]},
            {"required": ["customer_id"]}
        ]
    }
)
```

## Security Considerations

### 1. User Consent and Control

MCP implements a **human-in-the-loop** security model:

- **Tool Execution**: All tool calls require explicit user approval
- **Transparent Operations**: Users see what tools are being called and with what parameters
- **Granular Control**: Users can approve or deny individual operations

### 2. Input Sanitization

```python
import os
from pathlib import Path

def sanitize_file_path(user_path: str, base_dir: str) -> str:
    """Safely resolve file path within base directory"""
    # Resolve to absolute path
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()
    
    # Ensure target is within base directory
    if not str(target).startswith(str(base)):
        raise ValueError("Path outside allowed directory")
    
    return str(target)
```

### 3. Data Privacy

```python
# Avoid logging sensitive information
@server.call_tool()
async def authenticate_user(name: str, arguments: dict) -> list[types.TextContent]:
    username = arguments.get("username")
    password = arguments.get("password")
    
    # Good: Log operation without sensitive data
    logger.info(f"Authentication attempt for user: {username}")
    
    # Avoid: Logging sensitive information
    # logger.info(f"Auth attempt: {username}:{password}")  # DON'T DO THIS
    
    if authenticate(username, password):
        return [types.TextContent(type="text", text="Authentication successful")]
    else:
        return [types.TextContent(type="text", text="Authentication failed")]
```

### 4. Resource Access Control

```python
ALLOWED_DIRECTORIES = [
    "/home/user/documents",
    "/home/user/projects"
]

def check_file_access(file_path: str) -> bool:
    """Check if file access is allowed"""
    abs_path = os.path.abspath(file_path)
    
    for allowed_dir in ALLOWED_DIRECTORIES:
        if abs_path.startswith(allowed_dir):
            return True
    
    return False
```

## Transport Mechanisms

### 1. Standard I/O (stdio)

The primary transport for MCP servers, using stdin/stdout for communication.

#### Characteristics
- **Simple**: Easy to implement and debug
- **Universal**: Works across all platforms
- **Secure**: No network exposure
- **Process-based**: Each server runs as a separate process

#### Implementation
```python
import mcp.server.stdio

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )
```

### 2. Streamable HTTP

For servers that need network accessibility or integration with web services.

#### Characteristics
- **Network-accessible**: Can be reached over HTTP
- **Scalable**: Can handle multiple concurrent clients
- **Stateless**: Each request is independent
- **Standard**: Uses SSE (Server-Sent Events) for streaming

#### Configuration Example
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["server.py"],
      "transport": {
        "type": "http",
        "url": "http://localhost:8000/mcp"
      }
    }
  }
}
```

This comprehensive guide provides everything needed to understand and develop MCP servers effectively, following the latest 2025-03-26 specification and incorporating security best practices throughout.