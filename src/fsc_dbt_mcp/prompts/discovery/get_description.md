Retrieves documentation blocks from the dbt manifest by name (e.g., __MCP__ blocks) to provide domain expertise and guidelines.
The DEFAULT and primary documentation block is `__MCP__` (if exists) as this is where the LLM expert context is defined. This is the information to use when constructing an expert.  
  
Column-level documentation that exists on models should be documented in a dbt jinja doc-block. If it is, that column can be retrieved with this tool.
`get_description` provides just the raw documentation content and might be useful for:
- Getting specific column docs without loading the entire model metadata
- Accessing documentation blocks that aren't tied to specific models
- Lighter-weight queries when you only need documentation content
