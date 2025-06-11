Get comprehensive model metadata including columns, dependencies, SQL, and statistics for a specific dbt model.

**Parameters (use uniqueId when available):**
- `uniqueId`: **PREFERRED** - Full model ID (e.g., "model.bitcoin-models.core__fact_transactions")
- `model_name`: Model name (e.g., "core__fact_transactions") - fallback when uniqueId unavailable  
- `table_name`: Table name to search for (e.g., "fact_transactions")
- `resource_id`: Project ID(s) to search in (from get_resources())

**Returns:** Columns, types, descriptions, dependencies, compiled SQL, statistics, and metadata.

**Examples:**
- `get_model_details(uniqueId="model.ethereum-models.core__fact_transactions")` - **PREFERRED**
- `get_model_details(model_name="core__fact_blocks", resource_id="bitcoin-models")`
- `get_model_details(table_name="fact_transactions", resource_id=["bitcoin-models", "ethereum-models"])`
