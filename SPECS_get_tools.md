# updating the get_ tools
## current tools
tool signatures for discovery get_ tools

**get_description**  
 - retrieve a dbt documentation block by name from json artifacts
input
 - doc_name (required)
 - resource_id (required, array accepted)

returns json object of the doc block, if exists
returns non-critical error if doc block does not exist

**get_model_details**  
 - retrieve a dbt model by name from json artifacts
input
 - uniqueId
 - model_name
 - table_name
 - resource_id (required, array accepted)

returns json object of the model, if exists
returns non-critical error if model does not exist

**get_models**  
 - get multiple models by some search criteria from json artifacts

input
 - schema
 - level
 - resource_id
 - limit

returns json object of the models, if exists
returns non-critical error if models do not exist

**get_resources**  
 - retrieve a list of resources from the mcp resource list

input
 - show_details
 - blockchain_filter
 - category_filter

returns json object of the resources, if exists
returns non-critical error if resources do not exist

## proposed change thoughts
these all take some sort of filter to search json file(s) for an object to return.
they all need to know where to look (resource_id)

i want to generalize the definition of these properties so the tool inputSchema can simply reference them which means i want to align what the properties are as much as possible.
 - resource_id is easy, that's pretty standard across the get_ tools
 - we have several _name properties
  - i could maybe define TYPES (docs, model, table) so the search param is name and type ?
   - eg
   {
        "name": "bitcoin",
        "type": "blockchain
   }
   or
   {
    "name": "__overview__",
    "type": "docs"
   }
 - these are kind of like the args
 - resource id tells us where to search
 - args tells us what to search for 

so, each property is defined as a class to be reused by tools  
input validation is a class method  
any error handling at the property level is handled within the property definition  
the code for the tool then just focuses on the required execution
resource id can always be a string or an array  
resource id is pretty much always required, the tools always need to know where to look  
 - this starts to bring in project_manager which is a little out of scope for this refactor
 - this refactor aims to simplify the tools to improve debugging, streamline type and property management, and make it super simple to deploy new get_ tools
 - i think project_manager will continue to be the layer that adds support for searching and utilizing multiple resources
 - while the tools simplify into doing one thing and doing that one thing really well with concise code
 - and utilizes mcp best practices



## Docs on Tools
https://modelcontextprotocol.io/docs/concepts/tools#python
### Tool Implementation Best Practices
    Provide clear, descriptive names and descriptions
    Use detailed JSON Schema definitions for parameters
    Include examples in tool descriptions to demonstrate how the model should use them
    Implement proper error handling and validation
    Use progress reporting for long operations
    Keep tool operations focused and atomic
    Document expected return value structures
    Implement proper timeouts
    Consider rate limiting for resource-intensive operations
    Log tool usage for debugging and monitoring

### Error handling
Tool errors should be reported within the result object, not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error. When a tool encounters an error:

    Set isError to true in the result
    Include error details in the content array

Here’s an example of proper error handling for tools:
```python
try:
    # Tool operation
    result = perform_operation()
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=f"Operation successful: {result}"
            )
        ]
    )
except Exception as error:
    return types.CallToolResult(
        isError=True,
        content=[
            types.TextContent(
                type="text",
                text=f"Error: {str(error)}"
            )
        ]
    )
```
This approach allows the LLM to see that an error occurred and potentially take corrective action or request human intervention.



## next
 - add proper error handling with isError
 - add logs when sending requests to get json files from remote
 - review caching system
 - claude is trying to call 'ListPromptsRequest' to which the server is responding {"code":-32601,"message":"Method not found"}
    - should this be implemented?