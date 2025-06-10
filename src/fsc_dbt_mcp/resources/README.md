# dbt Project Resources - CSV-Driven Configuration

This directory implements a scalable, CSV-driven approach to managing dbt project resources for the FlipsideCrypto ecosystem.

## Overview

Instead of maintaining individual Python files for each blockchain project, we now use:

1. **Generic dbt project resource type** (`dbt_project_resource.py`)
2. **CSV configuration file** (`dbt_projects.csv`)  
3. **Auto-generated GitHub URLs** for FlipsideCrypto/* repositories
4. **Intelligent alias generation** based on blockchain names

## CSV Schema

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `id` | ✅ | Unique project identifier | `bitcoin-models` |
| `name` | ✅ | Human-readable project name | `Bitcoin Models` |
| `blockchain` | ✅ | Blockchain name | `bitcoin`, `ethereum`, `polygon` |
| `category` | ✅ | Technical classification | `evm`, `l1`, `svm`, `multi-chain`, `internal` |
| `type` | ✅ | Project type | `local`, `github` |
| `location` | ✅ | Local path OR GitHub repo | `/path/to/local` or `FlipsideCrypto/repo-name` |
| `target_branch` | Optional | Branch name (default: `main`) | `main`, `docs` |
| `aliases` | Optional | Pipe-separated aliases | `bitcoin\|btc\|bitcoin_models` |
| `schemas` | Optional | Pipe-separated schemas | `core\|bronze\|silver\|gold\|defi` |

## Adding New Projects

To add a new FlipsideCrypto blockchain project:

1. **Add a row to `dbt_projects.csv`**:
   ```csv
   cardano-models,Cardano Models,cardano,github,FlipsideCrypto/cardano-models,docs,cardano|ada|cardano_models,core|bronze|silver|gold|defi
   ```

2. **The system automatically**:
   - Generates description: `"dbt models for cardano blockchain data analysis and exploration"`
   - Generates GitHub artifact URLs: `https://raw.githubusercontent.com/FlipsideCrypto/cardano-models/docs/target/manifest.json`
   - Creates MCP resource URIs: `dbt://project/cardano-models`
   - Generates common aliases: `["cardano", "ada", "cardano_models"]`
   - Uses specified schemas or defaults to: `["core", "bronze", "silver", "gold"]`

3. **No Python code required!** 🎉

## Features

### 🚀 **Scalable**
- Add hundreds of projects with CSV rows, not Python files
- No code changes needed for new FlipsideCrypto projects

### 🔧 **Flexible**
- Supports both local and GitHub projects
- Custom GitHub repositories and branches
- Override aliases and schemas per project

### 🛡️ **Validated**
- CSV validation with helpful error messages
- Required field checking
- Project ID format validation

### ⚡ **Hot Reloadable**
- `resource_registry.refresh_projects()` reloads CSV without restart
- Perfect for development and testing

## GitHub URL Generation

For GitHub projects, artifact URLs are automatically generated:

```python
# Input CSV:
# type: github
# location: FlipsideCrypto/ethereum-models  
# target_branch: docs

# Generated URLs:
{
    "manifest": "https://raw.githubusercontent.com/FlipsideCrypto/ethereum-models/docs/target/manifest.json",
    "catalog": "https://raw.githubusercontent.com/FlipsideCrypto/ethereum-models/docs/target/catalog.json"
}
```

## Alias Generation

Smart alias generation based on project patterns:

```python
# For project_id: "bitcoin-models", blockchain: "bitcoin"
# Generated aliases: ["bitcoin-models", "bitcoin", "btc", "bitcoin_models"]

# For project_id: "ethereum-models", blockchain: "ethereum"  
# Generated aliases: ["ethereum-models", "ethereum", "eth", "ethereum_models"]
```

## Migration from Individual Files ✅

Migration complete! The old individual resource files (`bitcoin_models.py`, `ethereum_models.py`, `kairos_models.py`) have been removed. The CSV system now provides 100% compatible data structures with better scalability.

## Usage Examples

```python
from fsc_dbt_mcp.resources import resource_registry

# List all projects
project_ids = resource_registry.list_project_ids()

# Get specific project
bitcoin_project = resource_registry.get_project_by_id("bitcoin-models")

# Hot reload (development only)
resource_registry.refresh_projects()
```

## Benefits

- **📈 Scales to 100+ blockchain projects**
- **⚡ No deployment needed for new projects**  
- **🎯 Single source of truth in CSV**
- **🔄 Hot reloadable for development**
- **✅ Maintains full compatibility**
- **🛡️ Built-in validation and error handling**